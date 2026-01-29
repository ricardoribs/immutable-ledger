import asyncio
import logging
from src.infra.database import engine
from src.domain.ledger.models import Base
# Importamos os modelos para o SQLAlchemy saber que eles existem
from src.domain.ledger import models 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def init_models():
    logger.info("🔄 Iniciando criação de tabelas...")
    
    async with engine.begin() as conn:
        # O run_sync permite rodar código síncrono (create_all) dentro do async
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("✅ Tabelas (Users, Accounts, BackupCodes, AuditLogs) criadas com sucesso!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())