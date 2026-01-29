import redis.asyncio as redis
import time
from src.core.config import settings
from src.core.money import to_minor_units, from_minor_units

REDIS_URL = settings.REDIS_URL


class CacheService:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

    # --- BASICO ---
    async def get_value(self, key: str):
        try:
            return await self.redis.get(key)
        except Exception:
            return None

    async def set_value(self, key: str, value: str, expire_in_seconds: int = 60):
        try:
            await self.redis.set(key, value, ex=expire_in_seconds)
        except Exception:
            return None

    async def delete_key(self, key: str):
        try:
            await self.redis.delete(key)
        except Exception:
            return None

    # --- BLACKLIST (LEGADO: token inteiro) ---
    async def add_to_blacklist(self, token: str, expire_in_seconds: int):
        try:
            await self.redis.set(f"bl:{token}", "revoked", ex=expire_in_seconds)
        except Exception:
            return None

    async def is_blacklisted(self, token: str) -> bool:
        try:
            return (await self.redis.get(f"bl:{token}")) is not None
        except Exception:
            return False

    # --- BLACKLIST (NOVO: por JTI) ---
    async def add_jti_to_blacklist(self, jti: str, expire_in_seconds: int):
        try:
            await self.redis.set(f"bl:jti:{jti}", "revoked", ex=expire_in_seconds)
        except Exception:
            return None

    async def is_jti_blacklisted(self, jti: str) -> bool:
        try:
            return (await self.redis.get(f"bl:jti:{jti}")) is not None
        except Exception:
            return False

    # --- RATE LIMITING (FIXED WINDOW) ---
    async def check_rate_limit(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window_seconds)
            return current <= limit
        except Exception:
            return True

    # --- RATE LIMITING (SLIDING WINDOW) ---
    async def check_rate_limit_sliding_window(self, key: str, limit: int, window_seconds: int) -> bool:
        try:
            now_ms = int(time.time() * 1000)
            window_start = now_ms - (window_seconds * 1000)
            pipe = self.redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now_ms): now_ms})
            pipe.zcard(key)
            pipe.expire(key, window_seconds)
            _, _, count, _ = await pipe.execute()
            return count <= limit
        except Exception:
            return True

    async def incr_with_expire(self, key: str, ttl_seconds: int) -> int:
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, ttl_seconds)
            count, _ = await pipe.execute()
            return int(count)
        except Exception:
            return 0

    async def incr_float_with_expire(self, key: str, amount: float, ttl_seconds: int) -> float:
        try:
            pipe = self.redis.pipeline()
            pipe.incrbyfloat(key, amount)
            pipe.expire(key, ttl_seconds)
            total, _ = await pipe.execute()
            return float(total)
        except Exception:
            return 0.0

    async def incr_money_with_expire(self, key: str, amount, ttl_seconds: int):
        try:
            cents = to_minor_units(amount)
            pipe = self.redis.pipeline()
            pipe.incrby(key, cents)
            pipe.expire(key, ttl_seconds)
            total_cents, _ = await pipe.execute()
            return from_minor_units(int(total_cents))
        except Exception:
            return from_minor_units(0)

    async def close(self):
        try:
            await self.redis.close()
        except Exception:
            return None


cache = CacheService()
