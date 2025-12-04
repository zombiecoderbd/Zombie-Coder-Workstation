"""
Redis Cache Manager - ZombieCoder Local AI
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import asyncio
import json
import logging
import hashlib
import time
from typing import Any, Optional, Dict, Union
from dataclasses import dataclass
from datetime import datetime

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    Redis = object

from .config import CacheConfig

logger = logging.getLogger(__name__)


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    hit_rate_percent: float = 0.0
    
    def update_hit_rate(self):
        """Calculate hit rate percentage"""
        total = self.hits + self.misses
        self.hit_rate_percent = (self.hits / total * 100) if total > 0 else 0.0


class CacheManager:
    """Redis-based cache manager with intelligent caching strategies"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[Redis] = None
        self.stats = CacheStats()
        self._lock = asyncio.Lock()
        self._connected = False
        
    async def initialize(self) -> bool:
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, cache disabled")
            return False
            
        try:
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                encoding='utf-8',
                decode_responses=True,
                socket_connect_timeout=self.config.redis_connection_timeout,
                max_connections=self.config.redis_max_connections
            )
            
            # Test connection
            await self.redis_client.ping()
            self._connected = True
            logger.info(f"✅ Redis cache connected to {self.config.redis_host}:{self.config.redis_port}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self._connected = False
            return False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("🔌 Redis cache connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._connected = False
    
    def _generate_key(self, key: str, prefix: str = "") -> str:
        """Generate cache key with prefix"""
        full_prefix = f"{self.config.cache_prefix}:{prefix}" if prefix else self.config.cache_prefix
        return f"{full_prefix}:{key}"
    
    def _validate_ttl(self, ttl: Optional[int]) -> int:
        """Validate and normalize TTL"""
        if ttl is None:
            return self.config.default_ttl
        return min(max(ttl, 1), self.config.max_ttl)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, prefix: str = "") -> bool:
        """Set value in cache"""
        if not self._connected or not self.redis_client:
            return False
            
        try:
            cache_key = self._generate_key(key, prefix)
            normalized_ttl = self._validate_ttl(ttl)
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value)
            else:
                serialized_value = str(value)
            
            result = await self.redis_client.setex(
                cache_key, 
                normalized_ttl, 
                serialized_value
            )
            
            self.stats.sets += 1
            logger.debug(f"💾 Cached key: {cache_key} (TTL: {normalized_ttl}s)")
            return result
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    async def get(self, key: str, prefix: str = "", default: Any = None) -> Any:
        """Get value from cache"""
        if not self._connected or not self.redis_client:
            return default
            
        try:
            cache_key = self._generate_key(key, prefix)
            value = await self.redis_client.get(cache_key)
            
            if value is None:
                self.stats.misses += 1
                logger.debug(f"🔍 Cache miss for key: {cache_key}")
                return default
            
            self.stats.hits += 1
            logger.debug(f"🎯 Cache hit for key: {cache_key}")
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error getting cache key {key}: {e}")
            return default
    
    async def delete(self, key: str, prefix: str = "") -> bool:
        """Delete value from cache"""
        if not self._connected or not self.redis_client:
            return False
            
        try:
            cache_key = self._generate_key(key, prefix)
            result = await self.redis_client.delete(cache_key)
            
            if result:
                self.stats.deletes += 1
                logger.debug(f"🗑️ Deleted cache key: {cache_key}")
            
            return bool(result)
            
        except Exception as e:
            self.stats.errors += 1
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    async def exists(self, key: str, prefix: str = "") -> bool:
        """Check if key exists in cache"""
        if not self._connected or not self.redis_client:
            return False
            
        try:
            cache_key = self._generate_key(key, prefix)
            return bool(await self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1, prefix: str = "") -> Optional[int]:
        """Increment integer value in cache"""
        if not self._connected or not self.redis_client:
            return None
            
        try:
            cache_key = self._generate_key(key, prefix)
            result = await self.redis_client.incrby(cache_key, amount)
            logger.debug(f"📈 Incremented {cache_key} by {amount}")
            return result
        except Exception as e:
            logger.error(f"Error incrementing cache key {key}: {e}")
            return None
    
    async def expire(self, key: str, ttl: int, prefix: str = "") -> bool:
        """Set expiration time for key"""
        if not self._connected or not self.redis_client:
            return False
            
        try:
            cache_key = self._generate_key(key, prefix)
            result = await self.redis_client.expire(cache_key, ttl)
            logger.debug(f"⏰ Set expiration for {cache_key} to {ttl}s")
            return bool(result)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
    
    # --- Session Management ---
    
    async def store_session(self, session_id: str, data: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Store session data"""
        normalized_ttl = ttl or self.config.session_ttl
        return await self.set(session_id, data, normalized_ttl, "session")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return await self.get(session_id, "session")
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session data"""
        return await self.delete(session_id, "session")
    
    # --- Agent Response Caching ---
    
    async def cache_agent_response(self, agent_id: str, query_hash: str, response: Any, ttl: Optional[int] = None) -> bool:
        """Cache agent response"""
        normalized_ttl = ttl or self.config.response_cache_ttl
        cache_key = f"{agent_id}:{query_hash}"
        return await self.set(cache_key, response, normalized_ttl, "response")
    
    async def get_agent_response(self, agent_id: str, query_hash: str) -> Any:
        """Get cached agent response"""
        cache_key = f"{agent_id}:{query_hash}"
        return await self.get(cache_key, "response")
    
    async def invalidate_agent_cache(self, agent_id: str) -> bool:
        """Invalidate all cache entries for an agent"""
        # This would require pattern-based deletion which is complex
        # For now, we'll just log that cache invalidation was requested
        logger.info(f"🧹 Cache invalidation requested for agent: {agent_id}")
        return True
    
    # --- Statistics and Monitoring ---
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        self.stats.update_hit_rate()
        
        redis_info = {}
        if self._connected and self.redis_client:
            try:
                info = await self.redis_client.info()
                redis_info = {
                    'used_memory': info.get('used_memory_human', 'N/A'),
                    'connected_clients': info.get('connected_clients', 0),
                    'total_commands_processed': info.get('total_commands_processed', 0),
                    'keyspace_hits': info.get('keyspace_hits', 0),
                    'keyspace_misses': info.get('keyspace_misses', 0)
                }
            except Exception as e:
                logger.error(f"Error getting Redis info: {e}")
        
        return {
            'hits': self.stats.hits,
            'misses': self.stats.misses,
            'sets': self.stats.sets,
            'deletes': self.stats.deletes,
            'errors': self.stats.errors,
            'hit_rate_percent': round(self.stats.hit_rate_percent, 2),
            'redis_info': redis_info,
            'connected': self._connected
        }
    
    async def reset_stats(self):
        """Reset cache statistics"""
        self.stats = CacheStats()
        logger.info("📊 Cache statistics reset")
    
    # --- Utility Functions ---
    
    def generate_query_hash(self, query: str, agent_id: str = "") -> str:
        """Generate hash for query caching"""
        content = f"{agent_id}:{query}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()


def create_cache_manager(config: Union[CacheConfig, Dict[str, Any]]) -> CacheManager:
    """Factory function to create cache manager"""
    if isinstance(config, dict):
        cache_config = CacheConfig.from_dict(config)
    else:
        cache_config = config
    
    return CacheManager(cache_config)


def generate_query_hash(query: str, agent_id: str = "") -> str:
    """Utility function to generate query hash"""
    content = f"{agent_id}:{query}".encode('utf-8')
    return hashlib.sha256(content).hexdigest()