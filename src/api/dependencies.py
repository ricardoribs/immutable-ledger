from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.database import async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Cria uma sessao de banco de dados para cada requisicao
    e a fecha automaticamente quando termina.
    """
    async with async_session() as session:
        yield session
