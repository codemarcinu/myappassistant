"""
Cache Manager for FoodSave AI using Redis
"""

import asyncio
import json
import logging
import pickle
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis cache manager with automatic serialization/deserialization"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        self.default_ttl = 3600  # 1 hour default

    async def connect(self) -> bool:
        """Connect to Redis"""
        try:
            if not REDIS_AVAILABLE:
                logger.warning("Redis not available - cache disabled")
                return False

            if settings.REDIS_USE_CACHE:
                self.redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD or None,
                    decode_responses=False,  # Keep as bytes for pickle
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30,
                )

                # Test connection
                await self.redis_client.ping()
                self.is_connected = True
                logger.info("Redis cache connected successfully")
                return True
            else:
                logger.info("Redis cache disabled in settings")
                return False

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            return False

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Redis cache disconnected")

    async def set(
        self, key: str, value: Any, ttl: Optional[int] = None, serialize: bool = True
    ) -> bool:
        """Set value in cache"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            if serialize:
                if isinstance(value, BaseModel):
                    data = value.model_dump_json()
                elif isinstance(value, (dict, list)):
                    data = json.dumps(value, ensure_ascii=False)
                else:
                    data = pickle.dumps(value)
            else:
                data = str(value).encode("utf-8")

            ttl = ttl or self.default_ttl
            await self.redis_client.setex(key, ttl, data)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def get(self, key: str, deserialize: bool = True, default: Any = None) -> Any:
        """Get value from cache"""
        if not self.is_connected or not self.redis_client:
            return default

        try:
            data = await self.redis_client.get(key)
            if data is None:
                return default

            if deserialize:
                try:
                    # Try JSON first
                    return json.loads(data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    try:
                        # Try pickle
                        return pickle.loads(data)
                    except pickle.UnpicklingError:
                        # Return as string
                        return data.decode("utf-8")
            else:
                return data.decode("utf-8")

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return default

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            result = await self.redis_client.delete(key)
            logger.debug(f"Cache delete: {key}")
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for key"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self.is_connected or not self.redis_client:
            return -1

        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1

    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching pattern"""
        if not self.is_connected or not self.redis_client:
            return 0

        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Cleared {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.is_connected or not self.redis_client:
            return {"connected": False}

        try:
            info = await self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}

    async def health_check(self) -> bool:
        """Health check for cache"""
        if not self.is_connected or not self.redis_client:
            return False

        try:
            await self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Cache health check failed: {e}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


# Cache decorator for functions
def cache_result(
    key_prefix: str, ttl: int = 3600, key_builder: Optional[callable] = None
):
    """Decorator to cache function results"""

    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Simple key based on function name and arguments
                key_parts = [key_prefix, func.__name__]
                key_parts.extend([str(arg) for arg in args])
                key_parts.extend([f"{k}:{v}" for k, v in sorted(kwargs.items())])
                cache_key = ":".join(key_parts)

            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            logger.debug(f"Cache miss for {cache_key}, stored result")

            return result

        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async cache directly
            # This would need to be handled differently
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
