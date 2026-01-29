import redis.asyncio as redis
from src.core.config import settings

REDIS_URL = settings.REDIS_URL

# Cria o pool de conexoes
redis_pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)


def get_redis():
    return redis.Redis(connection_pool=redis_pool)
