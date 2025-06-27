"""
Dependency providers for FastAPI DI: ModelManager and CacheManager singletons.
"""
from functools import lru_cache
from typing import Any, Optional

from app.cache.redis_client import CacheManager
from app.core.config import get_settings
from app.models.manager import ModelManager

# Global references to initialized instances
_initialized_model_manager: Optional[ModelManager] = None
_initialized_cache_manager: Optional[CacheManager] = None


def set_initialized_model_manager(model_manager: ModelManager) -> None:
    """Set the initialized ModelManager instance for dependency injection."""
    global _initialized_model_manager
    _initialized_model_manager = model_manager


def set_initialized_cache_manager(cache_manager: CacheManager) -> None:
    """Set the initialized CacheManager instance for dependency injection."""
    global _initialized_cache_manager
    _initialized_cache_manager = cache_manager


def get_model_manager(request: Any = None) -> ModelManager:
    """Get the ModelManager instance, preferring the initialized one."""
    global _initialized_model_manager
    if _initialized_model_manager is not None:
        return _initialized_model_manager
    
    # Fallback: create new instance (for startup or testing)
    settings = get_settings()
    return ModelManager(ollama_host=settings.ollama_host)


def get_cache_manager() -> CacheManager:
    """Get the CacheManager instance, preferring the initialized one."""
    global _initialized_cache_manager
    if _initialized_cache_manager is not None:
        return _initialized_cache_manager
    
    # Fallback: create new instance (for startup or testing)
    settings = get_settings()
    return CacheManager(
        redis_url=settings.redis_url, max_connections=settings.redis_max_connections
    )
