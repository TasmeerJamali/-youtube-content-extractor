"""
Cache management with Redis and in-memory fallback.
"""

import json
import pickle
import hashlib
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import asyncio
import logging

# import aioredis
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class CacheManager:
    """
    Intelligent cache manager with Redis backend and in-memory fallback.
    """
    
    def __init__(self):
        self.redis_client: Optional[Any] = None  # Disabled for now
        self.memory_cache: Dict[str, Dict[str, Any]] = {}
        self.memory_cache_max_size = settings.cache_max_size
        self.default_ttl = settings.cache_ttl_seconds
        self.connected = False
        
    async def connect(self):
        """Initialize Redis connection with fallback to memory cache."""
        if not settings.enable_caching:
            logger.info("Caching is disabled")
            return
        
        # For now, just use memory cache
        logger.info("Using in-memory cache (Redis temporarily disabled)")
        self.redis_client = None
        self.connected = False
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first for better readability
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception:
            # Fallback to pickle
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # Fallback to pickle
            return pickle.loads(data)
    
    def _generate_cache_key(self, key: str, prefix: str = "ytce") -> str:
        """Generate a cache key with prefix and validation."""
        # Ensure key is not too long and contains only valid characters
        if len(key) > 200:
            key = hashlib.md5(key.encode()).hexdigest()
        
        return f"{prefix}:{key}"
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        if not settings.enable_caching:
            return default
        
        cache_key = self._generate_cache_key(key)
        
        # Try Redis first
        if self.redis_client and self.connected:
            try:
                data = await self.redis_client.get(cache_key)
                if data:
                    return self._deserialize_value(data)
            except Exception as e:
                logger.warning(f"Redis get error for key {cache_key}: {e}")
                # Fall through to memory cache
        
        # Try memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if entry['expires_at'] > datetime.now():
                return entry['value']
            else:
                # Remove expired entry
                del self.memory_cache[cache_key]
        
        return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL."""
        if not settings.enable_caching:
            return False
        
        cache_key = self._generate_cache_key(key)
        ttl = ttl or self.default_ttl
        
        # Store in Redis
        if self.redis_client and self.connected:
            try:
                serialized_value = self._serialize_value(value)
                await self.redis_client.setex(cache_key, ttl, serialized_value)
                logger.debug(f"Cached value in Redis: {cache_key}")
                return True
            except Exception as e:
                logger.warning(f"Redis set error for key {cache_key}: {e}")
                # Fall through to memory cache
        
        # Store in memory cache
        self._cleanup_memory_cache()
        
        self.memory_cache[cache_key] = {
            'value': value,
            'expires_at': datetime.now() + timedelta(seconds=ttl)
        }
        logger.debug(f"Cached value in memory: {cache_key}")
        return True
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._generate_cache_key(key)
        deleted = False
        
        # Delete from Redis
        if self.redis_client and self.connected:
            try:
                result = await self.redis_client.delete(cache_key)
                deleted = result > 0
            except Exception as e:
                logger.warning(f"Redis delete error for key {cache_key}: {e}")
        
        # Delete from memory cache
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]
            deleted = True
        
        return deleted
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        cache_key = self._generate_cache_key(key)
        
        # Check Redis
        if self.redis_client and self.connected:
            try:
                result = await self.redis_client.exists(cache_key)
                if result:
                    return True
            except Exception as e:
                logger.warning(f"Redis exists error for key {cache_key}: {e}")
        
        # Check memory cache
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            if entry['expires_at'] > datetime.now():
                return True
            else:
                del self.memory_cache[cache_key]
        
        return False
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple values from cache."""
        result = {}
        
        for key in keys:
            value = await self.get(key)
            if value is not None:
                result[key] = value
        
        return result
    
    async def set_many(
        self, 
        items: Dict[str, Any], 
        ttl: Optional[int] = None
    ) -> int:
        """Set multiple values in cache."""
        successful = 0
        
        for key, value in items.items():
            if await self.set(key, value, ttl):
                successful += 1
        
        return successful
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern."""
        cleared = 0
        
        # Clear from Redis
        if self.redis_client and self.connected:
            try:
                cache_pattern = self._generate_cache_key(pattern)
                keys = await self.redis_client.keys(cache_pattern)
                if keys:
                    cleared += await self.redis_client.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis clear pattern error: {e}")
        
        # Clear from memory cache
        cache_pattern = self._generate_cache_key(pattern)
        keys_to_delete = [
            key for key in self.memory_cache.keys() 
            if key.startswith(cache_pattern.replace('*', ''))
        ]
        
        for key in keys_to_delete:
            del self.memory_cache[key]
            cleared += 1
        
        return cleared
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries and enforce size limit."""
        now = datetime.now()
        
        # Remove expired entries
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry['expires_at'] <= now
        ]
        
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Enforce size limit (remove oldest entries)
        if len(self.memory_cache) >= self.memory_cache_max_size:
            # Sort by expiration time and remove oldest
            sorted_items = sorted(
                self.memory_cache.items(),
                key=lambda x: x[1]['expires_at']
            )
            
            items_to_remove = len(sorted_items) - self.memory_cache_max_size + 1
            for i in range(items_to_remove):
                key = sorted_items[i][0]
                del self.memory_cache[key]
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'memory_cache_size': len(self.memory_cache),
            'memory_cache_max_size': self.memory_cache_max_size,
            'redis_connected': self.connected,
            'caching_enabled': settings.enable_caching
        }
        
        if self.redis_client and self.connected:
            try:
                info = await self.redis_client.info('memory')
                stats['redis_memory_used'] = info.get('used_memory_human', 'unknown')
                stats['redis_keys'] = await self.redis_client.dbsize()
            except Exception as e:
                logger.warning(f"Failed to get Redis stats: {e}")
        
        return stats
    
    async def warm_cache(self, warm_data: Dict[str, Any]):
        """Pre-populate cache with common data."""
        logger.info("Starting cache warming...")
        
        successful = await self.set_many(warm_data)
        
        logger.info(f"Cache warming completed. {successful}/{len(warm_data)} items cached successfully")
    
    async def close(self):
        """Close Redis connection and clean up."""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")
        
        self.memory_cache.clear()


# Global cache manager instance
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """Get cache manager instance."""
    if not cache_manager.connected and settings.enable_caching:
        await cache_manager.connect()
    return cache_manager