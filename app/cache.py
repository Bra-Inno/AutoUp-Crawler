import redis.asyncio as redis
import json
import asyncio
from typing import Optional, Dict, Any
from app.config import settings
from loguru import logger

class InMemoryCache:
    """
    简单的内存缓存实现（当 Redis 不可用时的备选方案）
    """
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        if key in self._cache:
            item = self._cache[key]
            # 检查是否过期
            import time
            if time.time() < item['expires_at']:
                return item['data']
            else:
                # 删除过期项
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Dict[str, Any], expire: int):
        import time
        self._cache[key] = {
            'data': value,
            'expires_at': time.time() + expire
        }
        # 清理过期项（简单实现）
        if len(self._cache) > 1000:  # 防止内存无限增长
            current_time = time.time()
            expired_keys = [k for k, v in self._cache.items() if current_time >= v['expires_at']]
            for k in expired_keys:
                del self._cache[k]

class CacheManager:
    """
    智能缓存管理器，优先使用 Redis，不可用时降级到内存缓存
    """
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis_client = None
        self.memory_cache = InMemoryCache()
        self.use_redis = True
        self._init_attempted = False

    async def _try_init_redis(self):
        """尝试初始化 Redis 连接"""
        if self._init_attempted:
            return
        
        self._init_attempted = True
        try:
            self.redis_client = redis.from_url(self.redis_url)
            # 测试连接
            await self.redis_client.ping()
            self.use_redis = True
            logger.info("✅ Redis 连接成功")
        except Exception as e:
            logger.error(f"⚠️  Redis 连接失败，使用内存缓存: {e}")
            self.use_redis = False
            self.redis_client = None

    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        await self._try_init_redis()
        
        if self.use_redis and self.redis_client:
            try:
                data = await self.redis_client.get(key)
                return json.loads(data) if data else None
            except Exception as e:
                logger.error(f"⚠️  Redis 读取失败，切换到内存缓存: {e}")
                self.use_redis = False
                # 降级到内存缓存
                return await self.memory_cache.get(key)
        else:
            return await self.memory_cache.get(key)

    async def set(self, key: str, value: Dict[str, Any], expire: int):
        await self._try_init_redis()
        
        if self.use_redis and self.redis_client:
            try:
                await self.redis_client.set(key, json.dumps(value), ex=expire)
            except Exception as e:
                logger.error(f"⚠️  Redis 写入失败，切换到内存缓存: {e}")
                self.use_redis = False
                # 降级到内存缓存
                await self.memory_cache.set(key, value, expire)
        else:
            await self.memory_cache.set(key, value, expire)

# 创建缓存管理器实例，供应用全局使用
cache_manager = CacheManager(settings.REDIS_URL)