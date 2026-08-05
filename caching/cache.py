import json
import redis.asyncio as redis

REDIS_URL = "redis://localhost:6379/0"
_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

async def get_cached(key: str):
    value = await _client.get(key)
    if value is None:
        return None
    return json.loads(value)

async def set_cached(key: str, value: dict, tti_seconds: int = 60):
    await _client.set(key, json.dumps(value), ex=tti_seconds)
