"""
Cache manager for FoodSave AI using Redis
"""

import json
import logging
import pickle
from datetime import timedelta
from typing import Any, Optional, Union

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from ..config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager for performance optimization"""

    def __init__(self):
        self.redis_client = None
        self.is_available = False

        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                )
                self.is_available = True
                logger.info("Redis cache initialized successfully")
            except Exception as e:
                logger.warning(f"Redis cache not available: {e}")
                self.is_available = False
        else:
            logger.warning("Redis not installed. Cache disabled.")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.is_available or not self.redis_client:
            return None

        try:
            value = await self.redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(
        self, key: str, value: Any, expire: Optional[Union[int, timedelta]] = None
    ) -> bool:
        """Set value in cache"""
        if not self.is_available or not self.redis_client:
            return False

        try:
            serialized_value = json.dumps(value, default=str)
            if expire:
                if isinstance(expire, timedelta):
                    expire = int(expire.total_seconds())
                await self.redis_client.setex(key, expire, serialized_value)
            else:
                await self.redis_client.set(key, serialized_value)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.is_available or not self.redis_client:
            return False

        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_available or not self.redis_client:
            return False

        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        if not self.is_available or not self.redis_client:
            return False

        try:
            return await self.redis_client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting cache expiration: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.is_available or not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0

    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if not self.is_available or not self.redis_client:
            return {"available": False}

        try:
            info = await self.redis_client.info()
            return {
                "available": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"available": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Check if cache is healthy"""
        if not self.is_available or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False


# Global cache instance
cache_manager = CacheManager()


# Cache decorators
def cache_result(expire: Optional[Union[int, timedelta]] = None, key_prefix: str = ""):
    """Decorator to cache function results"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, expire)
            logger.debug(f"Cached result for {cache_key}")

            return result

        return wrapper

    return decorator


def invalidate_cache(pattern: str):
    """Decorator to invalidate cache after function execution"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            await cache_manager.clear_pattern(pattern)
            logger.debug(f"Invalidated cache pattern: {pattern}")
            return result

        return wrapper

    return decorator
