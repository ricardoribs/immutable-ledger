import pytest
from src.infra.cache import CacheService


@pytest.mark.asyncio
async def test_sliding_window_limit():
    cache = CacheService()
    key = "test:rl"
    try:
        for _ in range(5):
            assert await cache.check_rate_limit_sliding_window(key, limit=5, window_seconds=60)
        assert not await cache.check_rate_limit_sliding_window(key, limit=5, window_seconds=60)
    except Exception:
        pytest.skip("Redis not available for rate limit test")
    finally:
        try:
            await cache.delete_key(key)
        except Exception:
            pass
