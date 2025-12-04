"""
Environment Manager - ZombieCoder Local AI
Agent Workstation Layer - "যেখানে কোড ও কথা বলে"
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


@dataclass
class EnvironmentConfig:
    """Complete environment configuration"""
    
    # Environment settings
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    
    # Security settings
    secret_key: str = ""
    session_timeout: int = 1800
    
    # Cache settings
    cache_ttl: int = 3600
    
    # Database settings
    database_url: str = "./data/zombiecoder.db"
    chroma_path: str = "./data/chroma"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    proxy_host: str = "0.0.0.0"
    proxy_port: int = 3000
    chat_service_port: int = 3003
    monitoring_service_port: int = 3002
    rag_service_port: int = 3001
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.secret_key:
            self.secret_key = Fernet.generate_key().decode()


class EnvironmentManager:
    """Manage environment configuration and API keys"""
    
    def __init__(self, config_path: str = "./config"):
        self.config_path = Path(config_path)
        self.config = EnvironmentConfig()
        self.api_keys = {}
        self.encrypted_keys = {}
        self.cipher_suite = None
        
    async def initialize(self) -> bool:
        """Initialize environment manager"""
        try:
            # Load configuration files
            await self._load_config_files()
            
            # Initialize encryption
            await self._initialize_encryption()
            
            # Load API keys
            await self._load_api_keys()
            
            logger.info("🔧 Environment manager initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize environment manager: {e}")
            return False
    
    async def _load_config_files(self):
        """Load configuration from YAML files"""
        config_files = [
            self.config_path / "config.yaml",
            self.config_path / "config.local.yaml",
            self.config_path / "config.production.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f)
                        if config_data:
                            self._merge_config(config_data)
                            logger.info(f"Loaded config from {config_file}")
                except Exception as e:
                    logger.warning(f"Failed to load config file {config_file}: {e}")
    
    def _merge_config(self, config_data: Dict[str, Any]):
        """Merge configuration data"""
        # Merge top-level settings
        for key, value in config_data.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        
        # Merge nested configurations
        if 'server' in config_data:
            server_config = config_data['server']
            for key, value in server_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        if 'database' in config_data:
            db_config = config_data['database']
            for key, value in db_config.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)
        
        if 'cache' in config_data:
            cache_config = config_data['cache']
            if 'default_ttl' in cache_config:
                self.config.cache_ttl = cache_config['default_ttl']
    
    async def _initialize_encryption(self):
        """Initialize encryption for sensitive data"""
        try:
            # Generate or load encryption key
            key_file = self.config_path / ".secret.key"
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions
                os.chmod(key_file, 0o600)
            
            self.cipher_suite = Fernet(key)
            logger.info("🔒 Encryption initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
    
    async def _load_api_keys(self):
        """Load API keys from environment and files"""
        # Load from environment variables
        env_keys = {
            'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
            'ANTHROPIC_API_KEY': os.getenv('ANTHROPIC_API_KEY'),
            'HUGGINGFACE_TOKEN': os.getenv('HUGGINGFACE_TOKEN'),
            'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY')
        }
        
        # Filter out None values
        self.api_keys = {k: v for k, v in env_keys.items() if v}
        
        # Load from .env file if exists
        env_file = self.config_path.parent / ".env"
        if env_file.exists():
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() in env_keys:
                                self.api_keys[key.strip()] = value.strip()
            except Exception as e:
                logger.warning(f"Failed to load .env file: {e}")
        
        # Encrypt API keys for secure storage
        await self._encrypt_api_keys()
        
        if self.api_keys:
            logger.info(f"🔑 Loaded {len(self.api_keys)} API keys")
    
    async def _encrypt_api_keys(self):
        """Encrypt API keys for secure storage"""
        if not self.cipher_suite:
            return
            
        try:
            for key, value in self.api_keys.items():
                encrypted_value = self.cipher_suite.encrypt(value.encode())
                self.encrypted_keys[key] = encrypted_value
        except Exception as e:
            logger.error(f"Failed to encrypt API keys: {e}")
    
    def get_config(self) -> EnvironmentConfig:
        """Get environment configuration"""
        return self.config
    
    def get_server_config(self) -> Dict[str, Any]:
        """Get server configuration"""
        return {
            'host': self.config.host,
            'port': self.config.port,
            'proxy_host': self.config.proxy_host,
            'proxy_port': self.config.proxy_port,
            'chat_service_port': self.config.chat_service_port,
            'monitoring_service_port': self.config.monitoring_service_port,
            'rag_service_port': self.config.rag_service_port
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'url': self.config.database_url,
            'chroma_path': self.config.chroma_path
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'secret_key': self.config.secret_key,
            'session_timeout': self.config.session_timeout,
            'debug': self.config.debug
        }
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get decrypted API key for provider"""
        if not self.cipher_suite:
            return self.api_keys.get(provider)
        
        encrypted_key = self.encrypted_keys.get(provider)
        if encrypted_key:
            try:
                decrypted_key = self.cipher_suite.decrypt(encrypted_key)
                return decrypted_key.decode()
            except Exception as e:
                logger.error(f"Failed to decrypt API key for {provider}: {e}")
                return None
        return self.api_keys.get(provider)
    
    def get_all_api_keys(self) -> Dict[str, str]:
        """Get all API keys (decrypted)"""
        keys = {}
        for provider in self.api_keys.keys():
            key = self.get_api_key(provider)
            if key:
                keys[provider] = key
        return keys
    
    def set_api_key(self, provider: str, key: str):
        """Set API key for provider"""
        self.api_keys[provider] = key
        if self.cipher_suite:
            try:
                encrypted_key = self.cipher_suite.encrypt(key.encode())
                self.encrypted_keys[provider] = encrypted_key
            except Exception as e:
                logger.error(f"Failed to encrypt API key for {provider}: {e}")
    
    def validate_environment(self) -> List[str]:
        """Validate environment configuration"""
        issues = []
        
        # Check required directories
        required_dirs = ['./data', './logs', './workspace']
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                issues.append(f"Missing required directory: {dir_path}")
        
        # Check required API keys based on environment
        if self.config.environment == 'production':
            required_keys = ['OPENAI_API_KEY']
            for key in required_keys:
                if not self.get_api_key(key):
                    issues.append(f"Missing required API key: {key}")
        
        # Validate ports
        ports = [
            self.config.port,
            self.config.proxy_port,
            self.config.chat_service_port,
            self.config.monitoring_service_port,
            self.config.rag_service_port
        ]
        
        for port in ports:
            if not (1 <= port <= 65535):
                issues.append(f"Invalid port number: {port}")
        
        return issues
    
    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            'environment': self.config.environment,
            'debug': self.config.debug,
            'log_level': self.config.log_level,
            'server_config': self.get_server_config(),
            'database_config': self.get_database_config(),
            'security_config': self.get_security_config(),
            'available_providers': list(self.api_keys.keys()),
            'validation_issues': self.validate_environment()
        }


def create_environment_manager(config_path: str = "./config") -> EnvironmentManager:
    """Factory function to create environment manager"""
    return EnvironmentManager(config_path)