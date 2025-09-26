# app/cache.py
import redis.asyncio as redis
import json
from app.config import settings

class CacheManager:
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    async def get(self, key: str):
        data = await self.redis_client.get(key)
        return json.loads(data) if data else None

    async def set(self, key: str, value, expire: int):
        await self.redis_client.set(key, json.dumps(value), ex=expire)

cache_manager = CacheManager(settings.REDIS_URL)