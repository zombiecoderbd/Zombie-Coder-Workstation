"""
AI Model Router - Handles routing between different AI models
Supports OpenAI, Anthropic, and Local models with fallback logic
"""

import asyncio
import logging
import aiohttp
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import time
from abc import ABC, abstractmethod


@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: str
    model_name: str
    api_key: Optional[str]
    base_url: str
    max_tokens: int
    temperature: float
    timeout: int = 30


@dataclass
class CompletionRequest:
    """Request for model completion"""
    prompt: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    agent_id: Optional[str] = None


@dataclass
class CompletionResponse:
    """Response from model completion"""
    content: str
    model: str
    provider: str
    tokens_used: Optional[int] = None
    response_time: float = 0.0
    success: bool = True
    error: Optional[str] = None


class ModelProvider(ABC):
    """Abstract base class for model providers"""
    
    @abstractmethod
    async def get_completion(self, request: CompletionRequest, config: ModelConfig) -> CompletionResponse:
        """Get completion from the model"""
        pass
    
    @abstractmethod
    async def health_check(self, config: ModelConfig) -> bool:
        """Check if the provider is healthy"""
        pass


class OpenAIProvider(ModelProvider):
    """OpenAI API provider"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".OpenAI")
    
    async def get_completion(self, request: CompletionRequest, config: ModelConfig) -> CompletionResponse:
        """Get completion from OpenAI API"""
        start_time = time.time()
        
        try:
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config.model_name,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ],
                "max_tokens": request.max_tokens or config.max_tokens,
                "temperature": request.temperature or config.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data["choices"][0]["message"]["content"]
                        tokens_used = data.get("usage", {}).get("total_tokens")
                        
                        return CompletionResponse(
                            content=content,
                            model=config.model_name,
                            provider="openai",
                            tokens_used=tokens_used,
                            response_time=time.time() - start_time,
                            success=True
                        )
                    else:
                        error_text = await response.text()
                        return CompletionResponse(
                            content="",
                            model=config.model_name,
                            provider="openai",
                            response_time=time.time() - start_time,
                            success=False,
                            error=f"HTTP {response.status}: {error_text}"
                        )
        
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return CompletionResponse(
                content="",
                model=config.model_name,
                provider="openai",
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def health_check(self, config: ModelConfig) -> bool:
        """Check OpenAI API health"""
        try:
            headers = {
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{config.base_url}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"OpenAI health check failed: {e}")
            return False


class AnthropicProvider(ModelProvider):
    """Anthropic Claude API provider"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".Anthropic")
    
    async def get_completion(self, request: CompletionRequest, config: ModelConfig) -> CompletionResponse:
        """Get completion from Anthropic API"""
        start_time = time.time()
        
        try:
            headers = {
                "x-api-key": config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            payload = {
                "model": config.model_name,
                "max_tokens": request.max_tokens or config.max_tokens,
                "temperature": request.temperature or config.temperature,
                "messages": [
                    {"role": "user", "content": request.prompt}
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data["content"][0]["text"]
                        tokens_used = data.get("usage", {}).get("input_tokens") + data.get("usage", {}).get("output_tokens")
                        
                        return CompletionResponse(
                            content=content,
                            model=config.model_name,
                            provider="anthropic",
                            tokens_used=tokens_used,
                            response_time=time.time() - start_time,
                            success=True
                        )
                    else:
                        error_text = await response.text()
                        return CompletionResponse(
                            content="",
                            model=config.model_name,
                            provider="anthropic",
                            response_time=time.time() - start_time,
                            success=False,
                            error=f"HTTP {response.status}: {error_text}"
                        )
        
        except Exception as e:
            self.logger.error(f"Anthropic API error: {e}")
            return CompletionResponse(
                content="",
                model=config.model_name,
                provider="anthropic",
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def health_check(self, config: ModelConfig) -> bool:
        """Check Anthropic API health"""
        try:
            headers = {
                "x-api-key": config.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Simple health check - try to get a minimal completion
            payload = {
                "model": config.model_name,
                "max_tokens": 10,
                "messages": [
                    {"role": "user", "content": "Hi"}
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Anthropic health check failed: {e}")
            return False


class LocalProvider(ModelProvider):
    """Local model provider (for GGUF, ONNX, etc.)"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__ + ".Local")
    
    async def get_completion(self, request: CompletionRequest, config: ModelConfig) -> CompletionResponse:
        """Get completion from local model"""
        start_time = time.time()
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": config.model_name,
                "prompt": request.prompt,
                "max_tokens": request.max_tokens or config.max_tokens,
                "temperature": request.temperature or config.temperature
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{config.base_url}/completions",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=config.timeout)
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        content = data.get("choices", [{}])[0].get("text", "")
                        
                        return CompletionResponse(
                            content=content,
                            model=config.model_name,
                            provider="local",
                            response_time=time.time() - start_time,
                            success=True
                        )
                    else:
                        error_text = await response.text()
                        return CompletionResponse(
                            content="",
                            model=config.model_name,
                            provider="local",
                            response_time=time.time() - start_time,
                            success=False,
                            error=f"HTTP {response.status}: {error_text}"
                        )
        
        except Exception as e:
            self.logger.error(f"Local model error: {e}")
            return CompletionResponse(
                content="",
                model=config.model_name,
                provider="local",
                response_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    async def health_check(self, config: ModelConfig) -> bool:
        """Check local model health"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{config.base_url}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
        except Exception as e:
            self.logger.error(f"Local model health check failed: {e}")
            return False


class ModelRouter:
    """
    Main model router that handles fallback logic and provider selection
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize providers
        self.providers: Dict[str, ModelProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "local": LocalProvider()
        }
        
        # Model configurations
        self.model_configs: Dict[str, ModelConfig] = {}
        
        # Health status cache
        self.health_cache: Dict[str, bool] = {}
        self.last_health_check: Dict[str, float] = {}
        
        # Routing strategy
        self.routing_strategy = config.get('routing', {}).get('strategy', 'smart_fallback')
        self.primary_provider = config.get('routing', {}).get('primary_provider', 'openai')
        self.fallback_providers = config.get('routing', {}).get('fallback_providers', ['anthropic', 'local'])
        
    async def initialize(self) -> bool:
        """Initialize the model router"""
        try:
            self.logger.info("Initializing Model Router...")
            
            # Load model configurations
            await self._load_model_configurations()
            
            # Perform initial health checks
            await self._perform_health_checks()
            
            self.logger.info("Model Router initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Model Router: {e}")
            return False
    
    async def _load_model_configurations(self):
        """Load model configurations from config"""
        providers_config = self.config.get('providers', {})
        
        for provider_name, provider_config in providers_config.items():
            api_key = provider_config.get('api_key')
            if api_key and api_key.startswith('${') and api_key.endswith('}'):
                # Environment variable substitution
                env_var = api_key[2:-1]
                api_key = os.getenv(env_var)
            
            base_url = provider_config.get('base_url', '')
            models = provider_config.get('models', [])
            max_tokens = provider_config.get('max_tokens', 4096)
            temperature = provider_config.get('temperature', 0.7)
            timeout = provider_config.get('timeout', 30)
            
            for model_name in models:
                config_key = f"{provider_name}:{model_name}"
                self.model_configs[config_key] = ModelConfig(
                    provider=provider_name,
                    model_name=model_name,
                    api_key=api_key,
                    base_url=base_url,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout
                )
        
        self.logger.info(f"Loaded {len(self.model_configs)} model configurations")
    
    async def _perform_health_checks(self):
        """Perform health checks on all providers"""
        for provider_name, provider in self.providers.items():
            # Get a sample config for this provider
            sample_config = None
            for config in self.model_configs.values():
                if config.provider == provider_name:
                    sample_config = config
                    break
            
            if sample_config:
                is_healthy = await provider.health_check(sample_config)
                self.health_cache[provider_name] = is_healthy
                self.last_health_check[provider_name] = time.time()
                
                status = "healthy" if is_healthy else "unhealthy"
                self.logger.info(f"Provider {provider_name} is {status}")
    
    async def get_completion(self, prompt: str, config: Dict[str, Any]) -> CompletionResponse:
        """
        Get completion using smart routing and fallback logic
        """
        agent_id = config.get('agent_id', 'unknown')
        
        # Determine preferred models based on agent
        preferred_models = config.get('preferred_models', [])
        
        # Build list of models to try
        models_to_try = []
        
        # Add agent-preferred models first
        for model in preferred_models:
            models_to_try.append(model)
        
        # Add primary provider models
        primary_models = [f"{self.primary_provider}:{model}" 
                          for model in self.config.get('providers', {})
                          .get(self.primary_provider, {}).get('models', [])]
        models_to_try.extend(primary_models)
        
        # Add fallback models
        for fallback_provider in self.fallback_providers:
            fallback_models = [f"{fallback_provider}:{model}"
                              for model in self.config.get('providers', {})
                              .get(fallback_provider, {}).get('models', [])]
            models_to_try.extend(fallback_models)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_models = []
        for model in models_to_try:
            if model not in seen:
                unique_models.append(model)
                seen.add(model)
        
        # Try each model until successful
        last_error = None
        for model_key in unique_models:
            if model_key not in self.model_configs:
                continue
            
            model_config = self.model_configs[model_key]
            provider_name = model_config.provider
            
            # Check if provider is healthy
            if not await self._is_provider_healthy(provider_name):
                self.logger.warning(f"Provider {provider_name} is unhealthy, skipping")
                continue
            
            try:
                self.logger.info(f"Trying model: {model_key} for agent {agent_id}")
                
                # Create request
                request = CompletionRequest(
                    prompt=prompt,
                    max_tokens=config.get('max_tokens'),
                    temperature=config.get('temperature'),
                    agent_id=agent_id
                )
                
                # Get completion
                provider = self.providers[provider_name]
                response = await provider.get_completion(request, model_config)
                
                if response.success:
                    self.logger.info(f"Successfully used model: {model_key}")
                    return response
                else:
                    self.logger.warning(f"Model {model_key} failed: {response.error}")
                    last_error = response.error
                    
            except Exception as e:
                self.logger.error(f"Error with model {model_key}: {e}")
                last_error = str(e)
        
        # All models failed
        error_msg = f"All models failed. Last error: {last_error}"
        self.logger.error(error_msg)
        
        return CompletionResponse(
            content="I'm sorry, I'm experiencing technical difficulties. Please try again later.",
            model="none",
            provider="none",
            success=False,
            error=error_msg
        )
    
    async def _is_provider_healthy(self, provider_name: str) -> bool:
        """Check if provider is healthy (with caching)"""
        current_time = time.time()
        
        # Check cache (5-minute TTL)
        if (provider_name in self.health_cache and 
            provider_name in self.last_health_check and
            current_time - self.last_health_check[provider_name] < 300):
            return self.health_cache[provider_name]
        
        # Perform health check
        sample_config = None
        for config in self.model_configs.values():
            if config.provider == provider_name:
                sample_config = config
                break
        
        if sample_config:
            provider = self.providers[provider_name]
            is_healthy = await provider.health_check(sample_config)
            self.health_cache[provider_name] = is_healthy
            self.last_health_check[provider_name] = current_time
            
            return is_healthy
        
        return False
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers"""
        status = {
            'routing_strategy': self.routing_strategy,
            'primary_provider': self.primary_provider,
            'fallback_providers': self.fallback_providers,
            'providers': {}
        }
        
        for provider_name in self.providers.keys():
            is_healthy = await self._is_provider_healthy(provider_name)
            models = [config.model_name for config in self.model_configs.values() 
                     if config.provider == provider_name]
            
            status['providers'][provider_name] = {
                'healthy': is_healthy,
                'models': models,
                'last_health_check': self.last_health_check.get(provider_name)
            }
        
        return status
    
    async def shutdown(self):
        """Shutdown the model router"""
        self.logger.info("Shutting down Model Router...")
        self.health_cache.clear()
        self.last_health_check.clear()
        self.logger.info("Model Router shutdown complete")