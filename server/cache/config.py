"""
Cache Configuration - ZombieCoder Local AI
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import os


@dataclass
class CacheConfig:
    """Configuration for cache system"""
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Cache behavior
    default_ttl: int = 3600  # 1 hour
    max_ttl: int = 86400     # 24 hours
    cache_prefix: str = "zombiecoder"
    
    # Connection pooling
    redis_max_connections: int = 20
    redis_connection_timeout: int = 5
    
    # Session cache
    session_ttl: int = 1800  # 30 minutes
    
    # Response cache
    response_cache_ttl: int = 7200  # 2 hours
    
    def __post_init__(self):
        """Validate configuration"""
        if self.default_ttl <= 0:
            self.default_ttl = 3600
        if self.max_ttl <= 0:
            self.max_ttl = 86400
        if self.redis_max_connections <= 0:
            self.redis_max_connections = 20
            
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'CacheConfig':
        """Create CacheConfig from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Create CacheConfig from environment variables"""
        return cls(
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', 6379)),
            redis_db=int(os.getenv('REDIS_DB', 0)),
            redis_password=os.getenv('REDIS_PASSWORD'),
            default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', 3600)),
            max_ttl=int(os.getenv('CACHE_MAX_TTL', 86400)),
            cache_prefix=os.getenv('CACHE_PREFIX', 'zombiecoder'),
            redis_max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', 20)),
            redis_connection_timeout=int(os.getenv('REDIS_CONNECTION_TIMEOUT', 5)),
            session_ttl=int(os.getenv('SESSION_TTL', 1800)),
            response_cache_ttl=int(os.getenv('RESPONSE_CACHE_TTL', 7200))
        )