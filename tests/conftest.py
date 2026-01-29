import os
import pytest
from httpx import AsyncClient, ASGITransport

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from src.main import app
from src.core import security
from src.core.encryption import CryptoService
from src.infra import cache as cache_module
from src.infra.database import async_engine, Base


@pytest.fixture(scope="session", autouse=True)
async def setup_db_schema():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(autouse=True)
def fast_hashing(monkeypatch):
    def fake_hash(password: str) -> str:
        return f"hash:{password}"

    def fake_verify(password: str, hashed: str) -> bool:
        return hashed == f"hash:{password}"

    monkeypatch.setattr(security, "get_password_hash", fake_hash)
    monkeypatch.setattr(security, "verify_password", fake_verify)
    monkeypatch.setattr(CryptoService, "encrypt", staticmethod(lambda v: v))
    monkeypatch.setattr(CryptoService, "decrypt", staticmethod(lambda v: v))
    async def fake_get_value(key: str):
        return None

    async def fake_set_value(key: str, value: str, expire_in_seconds: int = 60):
        return None

    async def fake_delete_key(key: str):
        return None

    monkeypatch.setattr(cache_module.cache, "get_value", fake_get_value)
    monkeypatch.setattr(cache_module.cache, "set_value", fake_set_value)
    monkeypatch.setattr(cache_module.cache, "delete_key", fake_delete_key)

# Define que os testes usarao asyncio
@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

# O cliente agora vive durante toda a sessao (scope="session").
# Isso evita abrir e fechar conexoes a cada teste.
@pytest.fixture(scope="session")
async def client():
    await app.router.startup()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await app.router.shutdown()
