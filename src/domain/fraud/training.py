from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.domain.ledger import models as ledger_models
from src.domain.fraud import engine as fraud_engine
from src.domain.fraud import ml, models


class FraudTraining:
    @staticmethod
    async def build_dataset(db: AsyncSession, days: int = 30) -> tuple[list[list[float]], list[int]]:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = select(ledger_models.Transaction).where(ledger_models.Transaction.timestamp >= since)
        res = await db.execute(stmt)
        txs = res.scalars().all()

        features = []
        labels = []
        for tx in txs:
            feats, labels_names = await fraud_engine.FraudEngine.build_features(
                db,
                account_id=tx.account_id,
                amount_units=tx.amount,
                ip="127.0.0.1",
                user_agent="",
                device_fingerprint=None,
            )
            rule_score, _ = fraud_engine.FraudEngine._rule_score(feats, labels_names)
            label = 1 if rule_score >= 60 else 0
            features.append(feats)
            labels.append(label)
        return features, labels

    @staticmethod
    async def train(db: AsyncSession):
        feats, labels = await FraudTraining.build_dataset(db)
        if not feats:
            return {"trained": False, "reason": "no_data"}
        meta = ml.train_models(feats, labels)
        db.add(models.FraudModelMeta(model_type="IF", version="v1", metrics=str(meta)))
        db.add(models.FraudModelMeta(model_type="XGB", version="v1", metrics=str(meta)))
        await db.commit()
        return meta
