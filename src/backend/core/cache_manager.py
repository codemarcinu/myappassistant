"""
Cache Manager for FoodSave AI using Redis

This module provides caching functionality for expensive operations like RAG searches and internet queries.
"""

import asyncio
import hashlib
import json
import logging
import pickle
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar

try:
    import redis.asyncio as redis
    from redis.asyncio.client import Redis as RedisClient

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None  # type: ignore
    RedisClient = None  # type: ignore

from pydantic import BaseModel

from backend.config import settings

logger = logging.getLogger(__name__)

# Type for cached function return value
T = TypeVar("T")

# Cache configuration
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds
RAG_CACHE_TTL = 1800  # 30 minutes
INTERNET_CACHE_TTL = 600  # 10 minutes


class QueryCache:
    """Simple in-memory cache for query results"""

    def __init__(
        self, name: str, ttl: int = DEFAULT_CACHE_TTL, max_size: int = 100
    ) -> None:
        """
        Initialize a new query cache

        Args:
            name: Name of the cache for logging
            ttl: Time-to-live in seconds for cache entries
            max_size: Maximum number of items to store in cache
        """
        self.name = name
        self.ttl = ttl
        self.max_size = max_size
        self.cache: Dict[str, Tuple[Any, float]] = {}  # {key: (value, timestamp)}
        self.hits = 0
        self.misses = 0
        logger.info(f"Initialized {name} cache with TTL={ttl}s, max_size={max_size}")

    def _generate_key(self, query: str, **kwargs) -> str:
        """Generate a cache key from the query and additional parameters"""
        # Create a string representation of kwargs sorted by key
        kwargs_str = "&".join(
            f"{k}={v}" for k, v in sorted(kwargs.items()) if v is not None
        )
        key_str = f"{query}|{kwargs_str}" if kwargs_str else query
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, **kwargs) -> Optional[Any]:
        """
        Get a value from the cache

        Args:
            query: The query string
            **kwargs: Additional parameters that affect the result

        Returns:
            The cached value or None if not found or expired
        """
        key = self._generate_key(query, **kwargs)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp <= self.ttl:
                self.hits += 1
                logger.debug(f"{self.name} cache HIT: {query[:30]}...")
                return value
            else:
                # Expired
                del self.cache[key]

        self.misses += 1
        logger.debug(f"{self.name} cache MISS: {query[:30]}...")
        return None

    def set(self, query: str, value: Any, **kwargs) -> None:
        """
        Store a value in the cache

        Args:
            query: The query string
            value: The value to cache
            **kwargs: Additional parameters that affect the result
        """
        key = self._generate_key(query, **kwargs)

        # If cache is full, remove oldest entry
        if len(self.cache) >= self.max_size:
            oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
            del self.cache[oldest_key]

        self.cache[key] = (value, time.time())
        logger.debug(f"{self.name} cache SET: {query[:30]}...")

    def clear(self) -> None:
        """Clear the cache"""
        self.cache.clear()
        logger.info(f"{self.name} cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        return {
            "name": self.name,
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": hit_rate,
        }


class CacheManager:
    """Redis cache manager with automatic serialization/deserialization"""

    def __init__(self) -> None:
        self.redis_client: Optional["RedisClient"] = None  # type: ignore
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

    async def disconnect(self) -> None:
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
                    data = value.model_dump_json().encode("utf-8")
                elif isinstance(value, (dict, list)):
                    data = json.dumps(value, ensure_ascii=False).encode("utf-8")
                else:
                    data = pickle.dumps(value)
            else:
                data = str(value).encode("utf-8")

            ttl = ttl or self.default_ttl
            await self.redis_client.set(key, data, ex=ttl)
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Failed to set cache for key {key}: {e}")
            return False

    async def get(
        self,
        key: str,
        deserialize: bool = True,
        default: Any = None,
        expected_type: Optional[type] = None,
    ) -> None:
        """Get value from cache"""
        if not self.is_connected or not self.redis_client:
            return default

        try:
            data = await self.redis_client.get(key)
            if data is None:
                return default

            if deserialize:
                if expected_type and issubclass(expected_type, BaseModel):
                    return expected_type.model_validate_json(data.decode("utf-8"))
                try:
                    # Try JSON first
                    return json.loads(data.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # Fallback to pickle
                    return pickle.loads(data)
            else:
                return data.decode("utf-8")

        except Exception as e:
            logger.error(f"Failed to get cache for key {key}: {e}")
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

# Create global cache instances
rag_cache = QueryCache("RAG", ttl=RAG_CACHE_TTL)
internet_cache = QueryCache("Internet", ttl=INTERNET_CACHE_TTL)


def cached_async(cache_instance: QueryCache) -> None:
    """
    Decorator for caching async function results

    Args:
        cache_instance: The cache instance to use

    Returns:
        Decorated function
    """

    def decorator(func) -> None:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> None:
            # Extract query from args or kwargs
            query = None
            if len(args) > 1:  # Assuming first arg is self, second is query
                query = args[1]
            elif "query" in kwargs:
                query = kwargs["query"]

            if not query:
                return await func(*args, **kwargs)

            # Try to get from cache
            cache_result = cache_instance.get(query, **kwargs)
            if cache_result is not None:
                return cache_result

            # Not in cache, call function
            result = await func(*args, **kwargs)

            # Store in cache
            cache_instance.set(query, result, **kwargs)
            return result

        return wrapper

    return decorator


# Cache decorator for functions
def cache_result(
    key_prefix: str,
    ttl: int = 3600,
    key_builder: Optional[Callable] = None,
) -> None:
    """
    Decorator to cache the result of an async function in Redis.
    It automatically serializes/deserializes Pydantic models, dicts, lists, and other pickleable objects.
    """

    def decorator(func) -> None:
        async def async_wrapper(*args, **kwargs) -> None:
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

        def sync_wrapper(*args, **kwargs) -> None:
            # For sync functions, we can't use async cache directly
            # This would need to be handled differently
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
