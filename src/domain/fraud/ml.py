import os
import json
from typing import List


from src.domain.fraud import models


MODEL_DIR = os.getenv("FRAUD_MODEL_DIR", "/app/models")
IF_PATH = os.path.join(MODEL_DIR, "fraud_iforest.joblib")
XGB_PATH = os.path.join(MODEL_DIR, "fraud_xgb.joblib")


def _ensure_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def train_models(features: List[List[float]], labels: List[int]) -> dict:
    try:
        import numpy as np
        import joblib
        from sklearn.ensemble import IsolationForest
        from xgboost import XGBClassifier
    except Exception:
        return {"trained": False}
    _ensure_dir()
    X = np.array(features, dtype=float)
    y = np.array(labels, dtype=int)

    iforest = IsolationForest(n_estimators=200, random_state=42, contamination=0.05)
    iforest.fit(X)
    joblib.dump(iforest, IF_PATH)

    xgb = XGBClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.1,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    xgb.fit(X, y)
    joblib.dump(xgb, XGB_PATH)

    return {
        "iforest_path": IF_PATH,
        "xgb_path": XGB_PATH,
        "samples": len(X),
    }


def load_models():
    if not os.path.exists(IF_PATH) or not os.path.exists(XGB_PATH):
        return None, None
    try:
        import joblib
        return joblib.load(IF_PATH), joblib.load(XGB_PATH)
    except Exception:
        return None, None


def score_models(features: List[float]) -> dict:
    iforest, xgb = load_models()
    if not iforest or not xgb:
        return {"iforest": 0.0, "xgb": 0.0}
    try:
        import numpy as np
    except Exception:
        return {"iforest": 0.0, "xgb": 0.0}
    X = np.array([features], dtype=float)
    if_score = float(-iforest.score_samples(X)[0])  # higher = more anomalous
    xgb_score = float(xgb.predict_proba(X)[0][1])
    return {"iforest": if_score, "xgb": xgb_score}
