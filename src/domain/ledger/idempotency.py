import json
from src.infra.redis_client import get_redis


class IdempotencyHandler:
    # Tempo que a resposta fica salva no cache (24 horas = 86400 segundos)
    TTL_SECONDS = 86400

    @staticmethod
    async def get_cached_response(idempotency_key: str):
        """Busca se ja existe uma resposta salva para essa chave."""
        r = get_redis()
        cache_key = f"idempotency:{idempotency_key}"

        cached_data = await r.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None

    @staticmethod
    async def save_response(idempotency_key: str, response_data: dict):
        """Salva a resposta de sucesso no Redis."""
        r = get_redis()
        cache_key = f"idempotency:{idempotency_key}"

        await r.setex(
            name=cache_key,
            time=IdempotencyHandler.TTL_SECONDS,
            value=json.dumps(response_data, default=str),
        )
