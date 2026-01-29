import asyncio
from datetime import datetime, timedelta

from celery.schedules import crontab
from sqlalchemy import select

from src.infra.celery_app import celery_app
from src.infra.database import async_session
from src.domain.reconciliation.services import ReconciliationService
from src.domain.payments import models as payment_models
from src.domain.payments.services import PaymentService
from src.domain.pix import models as pix_models, schemas as pix_schemas
from src.domain.ledger import services as ledger_services
from src.domain.ledger import models as ledger_models
from src.domain.ledger import schemas as ledger_schemas
from src.domain.billing import models as billing_models
from src.domain.loans import models as loan_models
from src.domain.investments import models as inv_models
from src.domain.investments import services as inv_services
from src.domain.investments import schemas as inv_schemas
from src.domain.fraud.training import FraudTraining
from src.domain.regulatory.services import RegulatoryService
from src.domain.ml.services import MlService
from src.core.config import settings
from decimal import Decimal
from src.core.money import to_decimal


async def _run_reconciliation():
    async with async_session() as db:
        await ReconciliationService.run_reconciliation(db)


async def _run_scheduled_payments():
    async with async_session() as db:
        stmt_rec = select(payment_models.RecurringPayment).where(payment_models.RecurringPayment.active == True)  # noqa: E712
        res_rec = await db.execute(stmt_rec)
        for rec in res_rec.scalars().all():
            if rec.next_run_at and rec.next_run_at <= datetime.utcnow():
                payment = payment_models.Payment(
                    user_id=rec.user_id,
                    account_id=rec.account_id,
                    beneficiary_id=rec.beneficiary_id,
                    payment_type=rec.payment_type,
                    amount=rec.amount,
                    status="PENDING",
                )
                db.add(payment)
                rec.next_run_at = datetime.utcnow() + timedelta(days=rec.interval_days)
                await db.commit()

        stmt = select(payment_models.Payment).where(
            payment_models.Payment.status == "PENDING",
            payment_models.Payment.scheduled_for.is_not(None),
            payment_models.Payment.scheduled_for <= datetime.utcnow(),
        )
        res = await db.execute(stmt)
        for payment in res.scalars().all():
            try:
                await PaymentService._execute_payment(db, payment)
            except Exception:
                payment.status = "FAILED"
                await db.commit()


async def _run_pix_schedules():
    async with async_session() as db:
        stmt = select(pix_models.PixSchedule).where(
            pix_models.PixSchedule.status == "SCHEDULED",
            pix_models.PixSchedule.scheduled_for <= datetime.utcnow(),
        )
        res = await db.execute(stmt)
        for sched in res.scalars().all():
            try:
                data = pix_schemas.PixTransferCreate(
                    pix_key=sched.pix_key,
                    amount=sched.amount,
                    idempotency_key=f"pixsched:{sched.id}",
                )
                await ledger_services.LedgerService.process_pix_transfer(db, data, sched.from_account_id, otp=None)
                sched.status = "EXECUTED"
            except Exception:
                sched.status = "CANCELED"
            await db.commit()


async def _run_interest():
    async with async_session() as db:
        stmt = select(ledger_models.Account).where(
            ledger_models.Account.account_type == "SAVINGS"
        )
        res = await db.execute(stmt)
        for acc in res.scalars().all():
            if acc.balance <= 0:
                continue
            interest_rate = Decimal(str(settings.SAVINGS_INTEREST_MONTHLY))
            interest = to_decimal(acc.balance * interest_rate)
            if interest <= 0:
                continue
            tx = ledger_schemas.TransactionCreate(
                account_id=acc.id,
                amount=interest,
                type="DEPOSIT",
                idempotency_key=f"interest:{acc.id}:{datetime.utcnow().date()}",
            )
            try:
                await ledger_services.LedgerService.create_transaction(db, tx, otp=None)
            except Exception:
                continue


async def _run_loan_penalties():
    async with async_session() as db:
        stmt = select(loan_models.LoanInstallment).where(
            loan_models.LoanInstallment.paid == False,  # noqa: E712
            loan_models.LoanInstallment.due_date < datetime.utcnow(),
        )
        res = await db.execute(stmt)
        for inst in res.scalars().all():
            loan = await db.get(loan_models.Loan, inst.loan_id)
            if not loan:
                continue
            fee_rate = Decimal(str(settings.LOAN_LATE_FEE_RATE))
            daily_rate = Decimal(str(settings.LOAN_LATE_INTEREST_MONTHLY)) / Decimal("30")
            penalty = to_decimal(inst.amount * fee_rate)
            interest = to_decimal(inst.amount * daily_rate)
            if penalty <= 0 and interest <= 0:
                continue
            if penalty > 0:
                db.add(loan_models.LoanCharge(
                    loan_id=loan.id,
                    charge_type="PENALTY",
                    amount=penalty,
                ))
            if interest > 0:
                db.add(loan_models.LoanCharge(
                    loan_id=loan.id,
                    charge_type="INTEREST",
                    amount=interest,
                ))
            loan.fees_amount = to_decimal((loan.fees_amount or 0) + penalty + interest)
            await db.commit()


async def _run_auto_invest():
    async with async_session() as db:
        stmt = select(inv_models.AutoInvestConfig).where(inv_models.AutoInvestConfig.enabled == 1)
        res = await db.execute(stmt)
        for cfg in res.scalars().all():
            acc = await db.get(ledger_models.Account, cfg.account_id)
            if not acc or acc.balance <= cfg.min_balance:
                continue
            amount = to_decimal(acc.balance - cfg.min_balance)
            if amount <= 0:
                continue
            tx = ledger_schemas.TransactionCreate(
                account_id=cfg.account_id,
                amount=amount,
                type="WITHDRAW",
                idempotency_key=f"autoinv:{cfg.user_id}:{datetime.utcnow().date()}",
            )
            try:
                await ledger_services.LedgerService.create_transaction(db, tx, otp=None)
            except Exception:
                continue
            await inv_services.InvestmentService.create_order(
                db, cfg.user_id,
                inv_schemas.InvestmentOrderCreate(
                    account_id=cfg.account_id,
                    product_id=cfg.product_id,
                    order_type="BUY",
                    amount=amount,
                )
            )


async def _run_boleto_expiry():
    async with async_session() as db:
        stmt = select(billing_models.Boleto).where(
            billing_models.Boleto.status == "OPEN",
            billing_models.Boleto.due_date < datetime.utcnow(),
        )
        res = await db.execute(stmt)
        for boleto in res.scalars().all():
            boleto.status = "EXPIRED"
        await db.commit()


async def _run_fraud_training():
    async with async_session() as db:
        await FraudTraining.train(db)


async def _run_regulatory_reports():
    async with async_session() as db:
        period = datetime.utcnow().strftime("%Y-%m")
        await RegulatoryService.generate_scr_report(db, period)
        await RegulatoryService.generate_coaf_report(db, period)


async def _run_ml_training():
    async with async_session() as db:
        await MlService.train_churn(db)


@celery_app.task
def reconciliation_task():
    asyncio.run(_run_reconciliation())


@celery_app.task
def scheduled_payments_task():
    asyncio.run(_run_scheduled_payments())


@celery_app.task
def pix_schedules_task():
    asyncio.run(_run_pix_schedules())


@celery_app.task
def interest_task():
    asyncio.run(_run_interest())


@celery_app.task
def loan_penalties_task():
    asyncio.run(_run_loan_penalties())


@celery_app.task
def auto_invest_task():
    asyncio.run(_run_auto_invest())


@celery_app.task
def boleto_expiry_task():
    asyncio.run(_run_boleto_expiry())


@celery_app.task
def fraud_training_task():
    asyncio.run(_run_fraud_training())


@celery_app.task
def regulatory_reports_task():
    asyncio.run(_run_regulatory_reports())


@celery_app.task
def ml_training_task():
    asyncio.run(_run_ml_training())


celery_app.conf.beat_schedule.update({
    "reconciliation-daily": {
        "task": "src.domain.tasks.reconciliation_task",
        "schedule": crontab(hour=2, minute=0),
    },
    "scheduled-payments": {
        "task": "src.domain.tasks.scheduled_payments_task",
        "schedule": crontab(minute="*/5"),
    },
    "pix-schedules": {
        "task": "src.domain.tasks.pix_schedules_task",
        "schedule": crontab(minute="*/2"),
    },
    "interest-monthly": {
        "task": "src.domain.tasks.interest_task",
        "schedule": crontab(day_of_month="1", hour=3, minute=0),
    },
    "loan-penalties": {
        "task": "src.domain.tasks.loan_penalties_task",
        "schedule": crontab(hour="*/6"),
    },
    "auto-invest": {
        "task": "src.domain.tasks.auto_invest_task",
        "schedule": crontab(hour="*/4"),
    },
    "boleto-expiry": {
        "task": "src.domain.tasks.boleto_expiry_task",
        "schedule": crontab(hour=1, minute=0),
    },
    "fraud-training": {
        "task": "src.domain.tasks.fraud_training_task",
        "schedule": crontab(hour=4, minute=30),
    },
    "regulatory-reports": {
        "task": "src.domain.tasks.regulatory_reports_task",
        "schedule": crontab(day_of_month="1", hour=5, minute=0),
    },
    "ml-training": {
        "task": "src.domain.tasks.ml_training_task",
        "schedule": crontab(hour=6, minute=0),
    },
})
