from src.domain.fraud import models
from sqlalchemy.ext.asyncio import AsyncSession


class FraudAlertService:
    @staticmethod
    async def alert_team(db: AsyncSession, account_id: int, message: str, severity: str = "HIGH"):
        alert = models.FraudTeamAlert(
            account_id=account_id,
            severity=severity,
            message=message,
        )
        db.add(alert)
        await db.commit()
        return alert
