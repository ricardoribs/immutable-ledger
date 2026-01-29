from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from src.domain.ledger import models as ledger_models
from src.domain.reconciliation import models
from src.core.money import to_decimal


class ReconciliationService:
    @staticmethod
    async def run_reconciliation(db: AsyncSession) -> models.ReconciliationReport:
        report = models.ReconciliationReport()
        db.add(report)
        await db.flush()

        stmt_accounts = select(ledger_models.Account)
        res = await db.execute(stmt_accounts)
        accounts = res.scalars().all()
        report.total_accounts = len(accounts)

        for acc in accounts:
            stmt_sum = select(func.coalesce(func.sum(ledger_models.Posting.amount), 0.0)).where(
                ledger_models.Posting.account_id == acc.id
            )
            res_sum = await db.execute(stmt_sum)
            expected = to_decimal(res_sum.scalar() or 0)
            actual = to_decimal(acc.balance or 0)
            delta = to_decimal(actual - expected)
            if abs(delta) > to_decimal("0.01"):
                report.discrepancies += 1
                db.add(models.ReconciliationDiscrepancy(
                    report_id=report.id,
                    account_id=acc.id,
                    expected_balance=expected,
                    actual_balance=actual,
                    delta=delta,
                ))

        await db.commit()
        return report
