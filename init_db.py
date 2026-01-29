import asyncio
import sys

# 🔥 OBRIGATÓRIO NO WINDOWS
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from src.infra.database import engine, Base
from src.domain.ledger import models  # NÃO REMOVE

async def create_tables():
    print("🚀 Iniciando criação das tabelas no Banco de Dados...")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("✅ Tabelas criadas com sucesso!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_tables())
