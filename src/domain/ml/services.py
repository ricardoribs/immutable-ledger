import os
import json
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime

from src.domain.ml import models
from src.domain.ledger import models as ledger_models


MODEL_PATH = os.getenv("CHURN_MODEL_PATH", "/app/models/churn_model.joblib")


class MlService:
    @staticmethod
    async def train_churn(db: AsyncSession):
        try:
            import joblib
            from sklearn.linear_model import LogisticRegression
        except Exception:
            return {"trained": False}
        stmt = select(ledger_models.User)
        res = await db.execute(stmt)
        users = res.scalars().all()
        if not users:
            return {"trained": False}

        X = []
        y = []
        for u in users:
            stmt_tx = select(func.count(ledger_models.Transaction.id)).where(
                ledger_models.Transaction.account_id.in_(
                    select(ledger_models.Account.id).where(ledger_models.Account.user_id == u.id)
                )
            )
            res_tx = await db.execute(stmt_tx)
            tx_count = int(res_tx.scalar() or 0)
            days = (datetime.utcnow() - u.created_at).days
            X.append([tx_count, days])
            y.append(1 if tx_count < 3 and days > 30 else 0)

        model = LogisticRegression()
        model.fit(np.array(X), np.array(y))
        joblib.dump(model, MODEL_PATH)
        meta = models.ChurnModel(version="v1", metrics=json.dumps({"samples": len(X)}))
        db.add(meta)
        await db.commit()
        return {"trained": True}

    @staticmethod
    async def predict_churn(db: AsyncSession, user_id: int) -> models.ChurnPrediction:
        try:
            import joblib
        except Exception:
            raise RuntimeError("ML dependencies not installed")
        if not os.path.exists(MODEL_PATH):
            await MlService.train_churn(db)
        model = joblib.load(MODEL_PATH)
        stmt_tx = select(func.count(ledger_models.Transaction.id)).where(
            ledger_models.Transaction.account_id.in_(
                select(ledger_models.Account.id).where(ledger_models.Account.user_id == user_id)
            )
        )
        res_tx = await db.execute(stmt_tx)
        tx_count = int(res_tx.scalar() or 0)
        user = await db.get(ledger_models.User, user_id)
        days = (datetime.utcnow() - user.created_at).days if user else 0
        score = float(model.predict_proba(np.array([[tx_count, days]]))[0][1])
        pred = models.ChurnPrediction(user_id=user_id, score=score)
        db.add(pred)
        await db.commit()
        return pred

    @staticmethod
    async def generate_recommendations(db: AsyncSession, user_id: int):
        recs = [
            "Considere investir em CDB de liquidez diaria.",
            "Habilite MFA para maior seguranca.",
            "Configure auto-investimento para aplicar saldo ocioso.",
        ]
        for r in recs:
            db.add(models.Recommendation(user_id=user_id, content=r))
        await db.commit()
