"""
Redis Cache Manager - Hot layer for speed-optimized caching
Handles routing shortcuts, conversation history, and performance hints
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import redis.asyncio as redis
import structlog
from pydantic import BaseModel

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class CacheKey:
    """Cache key constants and generators"""
    ROUTE_PREFIX = "route:"
    PATTERN_PREFIX = "pattern:"
    SHORTCUT_PREFIX = "shortcut:"
    EXPECT_PREFIX = "expect:"
    MODEL_PREFIX = "model:"
    BUDGET_PREFIX = "budget:"
    RATE_PREFIX = "rate:"
    CONTEXT_PREFIX = "context:"
    PREFS_PREFIX = "prefs:"
    CONVERSATION_PREFIX = "conv:"
    METRICS_PREFIX = "metrics:"
    STATS_PREFIX = "stats:"

    @staticmethod
    def query_hash(query: str) -> str:
        return hashlib.md5(query.encode()).hexdigest()[:16]

    @staticmethod
    def route_key(query: str) -> str:
        return f"{CacheKey.ROUTE_PREFIX}{CacheKey.query_hash(query)}"

    @staticmethod
    def pattern_key(user_id: str) -> str:
        return f"{CacheKey.PATTERN_PREFIX}{user_id}"

    @staticmethod
    def conversation_key(session_id: str) -> str:
        return f"{CacheKey.CONVERSATION_PREFIX}{session_id}"

    @staticmethod
    def budget_key(user_id: str) -> str:
        return f"{CacheKey.BUDGET_PREFIX}{user_id}"

    @staticmethod
    def rate_key(user_id: str) -> str:
        return f"{CacheKey.RATE_PREFIX}{user_id}"


class CacheStrategy:
    """Cache strategy definitions"""
    TTL_SHORT = 300  # 5 minutes
    TTL_MEDIUM = 1800  # 30 minutes
    TTL_LONG = 3600  # 1 hour
    TTL_DAY = 86400  # 24 hours
    STRATEGIES = {
        "routing": {"ttl": TTL_SHORT, "max_size": 10000},
        "responses": {"ttl": TTL_MEDIUM, "max_size": 5000},
        "conversations": {"ttl": TTL_DAY, "max_size": 100},
        "patterns": {"ttl": TTL_LONG, "max_size": 1000},
        "metrics": {"ttl": TTL_SHORT, "max_size": 500},
    }


class CacheMetrics(BaseModel):
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    avg_response_time: float = 0.0
    memory_usage: int = 0

    def update_hit(self, response_time: float):
        self.total_requests += 1
        self.cache_hits += 1
        self._update_hit_rate()
        self._update_avg_response_time(response_time)

    def update_miss(self, response_time: float):
        self.total_requests += 1
        self.cache_misses += 1
        self._update_hit_rate()
        self._update_avg_response_time(response_time)

    def _update_hit_rate(self):
        if self.total_requests > 0:
            self.hit_rate = self.cache_hits / self.total_requests

    def _update_avg_response_time(self, response_time: float):
        if self.total_requests == 1:
            self.avg_response_time = response_time
        else:
            self.avg_response_time = (
                self.avg_response_time * (self.total_requests - 1) + response_time
            ) / self.total_requests


class CacheManager:
    """Redis-based cache manager for hot layer"""
    def __init__(self, redis_url: str, max_connections: int = 20):
        self.redis_url = redis_url
        self.max_connections = max_connections
        self.settings = get_settings()
        self.redis: Optional[redis.Redis] = None
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.metrics = CacheMetrics()
        self._local_cache: Dict[str, tuple[Any, datetime]] = {}
        self._local_cache_max_size = 1000
    async def initialize(self):
        try:
            self.redis_pool = redis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )
            self.redis = redis.Redis(connection_pool=self.redis_pool)
            await self.redis.ping()
            logger.info("Redis cache manager initialized", url=self.redis_url)
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            logger.warning("Falling back to local cache only")
    async def cleanup(self):
        if self.redis:
            await self.redis.aclose()
        if self.redis_pool:
            await self.redis_pool.disconnect()
    async def health_check(self) -> bool:
        try:
            if self.redis:
                await self.redis.ping()
                return True
            return False
        except Exception:
            return False
    async def get(self, key: str, default: Any = None) -> Any:
        start_time = datetime.now()
        try:
            if self.redis:
                value = await self.redis.get(key)
                if value is not None:
                    response_time = (datetime.now() - start_time).total_seconds()
                    self.metrics.update_hit(response_time)
                    return json.loads(value)
            if key in self._local_cache:
                value, expiry = self._local_cache[key]
                if datetime.now() < expiry:
                    response_time = (datetime.now() - start_time).total_seconds()
                    self.metrics.update_hit(response_time)
                    return value
                else:
                    del self._local_cache[key]
            response_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update_miss(response_time)
            return default
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            response_time = (datetime.now() - start_time).total_seconds()
            self.metrics.update_miss(response_time)
            return default
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            serialized_value = json.dumps(value)
            if self.redis:
                if ttl:
                    await self.redis.setex(key, ttl, serialized_value)
                else:
                    await self.redis.set(key, serialized_value)
            expiry = datetime.now() + timedelta(seconds=ttl or CacheStrategy.TTL_MEDIUM)
            self._local_cache[key] = (value, expiry)
            self._cleanup_local_cache()
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            try:
                expiry = datetime.now() + timedelta(seconds=ttl or CacheStrategy.TTL_MEDIUM)
                self._local_cache[key] = (value, expiry)
                self._cleanup_local_cache()
                return True
            except Exception as local_e:
                logger.error(f"Local cache set error: {local_e}")
                return False
    def _cleanup_local_cache(self):
        if len(self._local_cache) > self._local_cache_max_size:
            now = datetime.now()
            expired_keys = [
                key for key, (_, expiry) in self._local_cache.items() if now >= expiry
            ]
            for key in expired_keys:
                del self._local_cache[key]
            if len(self._local_cache) > self._local_cache_max_size:
                sorted_items = sorted(
                    self._local_cache.items(),
                    key=lambda x: x[1][1],
                )
                self._local_cache = dict(sorted_items[-self._local_cache_max_size :])
