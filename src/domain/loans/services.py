from datetime import datetime, timedelta
from math import pow
import secrets

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.domain.loans import models, schemas
from src.domain.ledger import models as ledger_models
from src.domain.ledger import services as ledger_services
from src.domain.ledger import schemas as ledger_schemas
from src.core.config import settings
from decimal import Decimal
from src.core.money import to_decimal


class LoanService:
    @staticmethod
    async def _compute_credit_score(db: AsyncSession, user_id: int, account_id: int) -> int:
        stmt_bal = select(ledger_models.Account.balance).where(ledger_models.Account.id == account_id)
        res_bal = await db.execute(stmt_bal)
        balance = float(res_bal.scalar() or 0.0)

        stmt_tx = select(func.count(ledger_models.Transaction.id)).where(
            ledger_models.Transaction.account_id == account_id
        )
        res_tx = await db.execute(stmt_tx)
        tx_count = int(res_tx.scalar() or 0)

        base = 400
        score = base + min(300, int(balance / 100)) + min(200, tx_count * 2)
        return max(300, min(900, score))

    @staticmethod
    def _compute_iof(principal: float, term_months: int):
        days = term_months * 30
        principal_val = to_decimal(principal)
        fixed_rate = Decimal(str(settings.IOF_RATE_FIXED))
        daily_rate = Decimal(str(settings.IOF_RATE_DAILY))
        iof = principal_val * fixed_rate + principal_val * daily_rate * days
        return to_decimal(iof)
    @staticmethod
    def simulate(data: schemas.LoanSimulateRequest) -> schemas.LoanSimulateResponse:
        i = data.rate_monthly
        n = data.term_months
        amort = data.amortization_type.upper()
        if amort == "SAC":
            amort_val = data.principal / n
            total = 0.0
            first = 0.0
            for k in range(1, n + 1):
                interest = (data.principal - amort_val * (k - 1)) * i
                installment = amort_val + interest
                if k == 1:
                    first = installment
                total += installment
            installment = round(first, 2)
        else:
            if i <= 0:
                installment = data.principal / n
            else:
                installment = data.principal * (i * pow(1 + i, n)) / (pow(1 + i, n) - 1)
            total = installment * n
        total = round(total, 2)
        return schemas.LoanSimulateResponse(
            principal=data.principal,
            rate_monthly=i,
            term_months=n,
            installment_amount=round(installment, 2),
            total_payable=total,
            amortization_type=amort,
        )

    @staticmethod
    async def create_loan(db: AsyncSession, user_id: int, data: schemas.LoanCreate):
        score = await LoanService._compute_credit_score(db, user_id, data.account_id)
        principal_value = to_decimal(data.principal)
        iof_amount = LoanService._compute_iof(data.principal, data.term_months)
        loan = models.Loan(
            user_id=user_id,
            account_id=data.account_id,
            loan_type=data.loan_type,
            principal=principal_value,
            rate_monthly=data.rate_monthly,
            term_months=data.term_months,
            amortization_type=data.amortization_type.upper(),
            credit_score=score,
            iof_amount=iof_amount,
        )
        db.add(loan)
        await db.flush()

        if iof_amount > 0:
            db.add(models.LoanCharge(
                loan_id=loan.id,
                charge_type="IOF",
                amount=iof_amount,
            ))

        tx_credit = ledger_schemas.TransactionCreate(
            account_id=data.account_id,
            amount=principal_value,
            type="DEPOSIT",
            idempotency_key=secrets.token_urlsafe(16),
        )
        await ledger_services.LedgerService.create_transaction(db, tx_credit, otp=None)

        if iof_amount > 0:
            tx_iof = ledger_schemas.TransactionCreate(
                account_id=data.account_id,
                amount=iof_amount,
                type="WITHDRAW",
                idempotency_key=secrets.token_urlsafe(16),
            )
            await ledger_services.LedgerService.create_transaction(db, tx_iof, otp=None)

        sim = LoanService.simulate(
            schemas.LoanSimulateRequest(
                principal=data.principal,
                rate_monthly=data.rate_monthly,
                term_months=data.term_months,
                amortization_type=data.amortization_type,
            )
        )
        for i in range(1, data.term_months + 1):
            inst = models.LoanInstallment(
                loan_id=loan.id,
                due_date=datetime.utcnow() + timedelta(days=30 * i),
                amount=sim.installment_amount,
            )
            db.add(inst)

        await db.commit()
        return loan

    @staticmethod
    async def list_loans(db: AsyncSession, user_id: int):
        stmt = select(models.Loan).where(models.Loan.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalars().all()

    @staticmethod
    async def list_installments(db: AsyncSession, loan_id: int, user_id: int):
        stmt = select(models.LoanInstallment).where(models.LoanInstallment.loan_id == loan_id)
        res = await db.execute(stmt)
        return res.scalars().all()
