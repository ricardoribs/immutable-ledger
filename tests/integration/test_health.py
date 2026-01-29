import os
from fastapi.testclient import TestClient

os.environ["SKIP_DB_INIT"] = "true"
from src.main import app  # noqa: E402


def test_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"
