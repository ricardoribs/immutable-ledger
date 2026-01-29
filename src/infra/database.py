# src/infra/database.py

import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from src.core.config import settings

Base = declarative_base()

# ==============================================================================
# 1) ASYNC ENGINE (API)
# ==============================================================================

if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass

_async_connect_args = {}
_async_poolclass = None
if settings.DATABASE_URL.startswith("sqlite+aiosqlite://"):
    _async_connect_args = {"check_same_thread": False, "timeout": 30}
    _async_poolclass = NullPool

async_engine = create_async_engine(
    settings.DATABASE_URL,  # ex: postgresql+asyncpg://... or postgresql+psycopg://...
    echo=False,
    pool_pre_ping=True,
    connect_args=_async_connect_args,
    poolclass=_async_poolclass,
)

# Compat
engine = async_engine

async_session = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db():
    async with async_session() as session:
        yield session


# ==============================================================================
# 2) SYNC ENGINE (Middleware / scripts)
# ==============================================================================

def _sync_database_url(url: str) -> str:
    if url.startswith("sqlite+aiosqlite://"):
        return url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    if url.startswith("postgresql+asyncpg://"):
        return url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if url.startswith("postgresql+psycopg://"):
        return url.replace("postgresql+psycopg://", "postgresql://", 1)
    return url


SYNC_DATABASE_URL = _sync_database_url(settings.DATABASE_URL)

_sync_connect_args = {}
_sync_poolclass = None
if SYNC_DATABASE_URL.startswith("sqlite://"):
    _sync_connect_args = {"check_same_thread": False, "timeout": 30}
    _sync_poolclass = NullPool

sync_engine = create_engine(
    SYNC_DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_sync_connect_args,
    poolclass=_sync_poolclass,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine,
)

# ==============================================================================
# 3) INIT DB
# ==============================================================================


async def init_db():
    print("Iniciando setup do banco...")
    print("DATABASE_URL =", settings.DATABASE_URL)
    if os.getenv("SKIP_DB_INIT", "false").lower() == "true":
        print("SKIP_DB_INIT ativo, pulando init_db.")
        return

    try:
        from src.domain import registry as _registry  # noqa: F401
        print("Modelos carregados: src.domain.registry")
    except Exception as e:
        print(f"ERRO FATAL: Nao consegui importar os modelos. {e}")
        raise

    last_err = None
    for attempt in range(1, 11):
        try:
            async with async_engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                await conn.run_sync(Base.metadata.create_all)

            async with async_session() as session:
                from src.infra.seed import seed_dev
                await seed_dev(session)
                from src.domain.ledger import models as ledger_models
                seq = await session.get(ledger_models.LedgerSequence, 1)
                if not seq:
                    session.add(ledger_models.LedgerSequence(id=1, value=0))
                    await session.commit()

            print("Tabelas criadas/sincronizadas.")
            return
        except Exception as e:
            last_err = e
            print(f"DB nao pronto ({attempt}/10): {e}")
            await asyncio.sleep(1.5)

    raise RuntimeError(f"DB nao subiu/instavel apos retries: {last_err}")
