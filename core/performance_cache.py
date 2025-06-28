"""
Performance Cache Module for Agentical

High-performance caching system designed to optimize agent operations,
database queries, and MCP server responses for sub-100ms response times.

Features:
- Memory-based LRU cache for hot data
- Redis integration for distributed caching
- Cache warming and invalidation strategies
- Performance metrics and monitoring
"""

import asyncio
import json
import time
import hashlib
from typing import Any, Dict, Optional, Union, Callable, List
from functools import wraps
from datetime import datetime, timedelta
import logging

import logfire
from cachetools import TTLCache, LRUCache

logger = logging.getLogger(__name__)


class PerformanceCache:
    """High-performance caching system for Agentical framework"""
    
    def __init__(self, 
                 max_size: int = 10000,
                 ttl_seconds: int = 3600,
                 redis_client: Optional[Any] = None):
        """
        Initialize performance cache
        
        Args:
            max_size: Maximum number of items in memory cache
            ttl_seconds: Time-to-live for cache entries
            redis_client: Optional Redis client for distributed caching
        """
        self.memory_cache = TTLCache(maxsize=max_size, ttl=ttl_seconds)
        self.lru_cache = LRUCache(maxsize=max_size // 2)
        self.redis_client = redis_client
        
        # Performance metrics
        self.hits = 0
        self.misses = 0
        self.sets = 0
        
        logfire.info("Performance cache initialized", 
                    max_size=max_size, ttl_seconds=ttl_seconds)
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_string = f"{prefix}:{json.dumps(key_data, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        # Try memory cache first
        value = self.memory_cache.get(key)
        if value is not None:
            self.hits += 1
            return value
        
        # Try LRU cache
        value = self.lru_cache.get(key)
        if value is not None:
            self.hits += 1
            return value
        
        # Try Redis if available
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value is not None:
                    # Deserialize and store in memory cache
                    deserialized = json.loads(value)
                    self.memory_cache[key] = deserialized
                    self.hits += 1
                    return deserialized
            except Exception as e:
                logger.warning(f"Redis cache get failed: {e}")
        
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        # Store in memory cache
        self.memory_cache[key] = value
        
        # Store in LRU cache for frequently accessed items
        self.lru_cache[key] = value
        
        # Store in Redis if available
        if self.redis_client:
            try:
                serialized = json.dumps(value, default=str)
                if ttl:
                    self.redis_client.setex(key, ttl, serialized)
                else:
                    self.redis_client.set(key, serialized)
            except Exception as e:
                logger.warning(f"Redis cache set failed: {e}")
        
        self.sets += 1
    
    def delete(self, key: str) -> None:
        """Delete item from cache"""
        self.memory_cache.pop(key, None)
        self.lru_cache.pop(key, None)
        
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis cache delete failed: {e}")
    
    def clear(self) -> None:
        """Clear all cache"""
        self.memory_cache.clear()
        self.lru_cache.clear()
        
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except Exception as e:
                logger.warning(f"Redis cache clear failed: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "hit_rate": hit_rate,
            "memory_cache_size": len(self.memory_cache),
            "lru_cache_size": len(self.lru_cache)
        }


# Global cache instance
_global_cache: Optional[PerformanceCache] = None


def get_cache() -> PerformanceCache:
    """Get or create global cache instance"""
    global _global_cache
    if _global_cache is None:
        _global_cache = PerformanceCache()
    return _global_cache


def cached(prefix: str, ttl: Optional[int] = None):
    """
    Decorator for caching function results
    
    Args:
        prefix: Cache key prefix
        ttl: Time-to-live override
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            with logfire.span("Cache lookup", key=cache_key):
                result = cache.get(cache_key)
                
            if result is not None:
                logfire.info("Cache hit", key=cache_key)
                return result
            
            # Execute function and cache result
            with logfire.span("Function execution", function=func.__name__):
                start_time = time.time()
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                logfire.info("Function executed", 
                           function=func.__name__, 
                           execution_time=execution_time)
            
            # Cache the result
            with logfire.span("Cache store", key=cache_key):
                cache.set(cache_key, result, ttl)
                logfire.info("Cache miss - stored result", key=cache_key)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            cache_key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Execute function and cache result
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            cache.set(cache_key, result, ttl)
            return result
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class AgentResponseCache:
    """Specialized cache for agent operation responses"""
    
    def __init__(self, cache: Optional[PerformanceCache] = None):
        self.cache = cache or get_cache()
    
    async def get_agent_response(self, agent_id: str, operation: str, 
                                parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached agent response"""
        cache_key = self.cache._generate_key("agent_response", agent_id, operation, parameters)
        return self.cache.get(cache_key)
    
    async def store_agent_response(self, agent_id: str, operation: str,
                                  parameters: Dict[str, Any], response: Dict[str, Any],
                                  ttl: int = 300) -> None:
        """Store agent response in cache"""
        cache_key = self.cache._generate_key("agent_response", agent_id, operation, parameters)
        self.cache.set(cache_key, response, ttl)


class KnowledgeQueryCache:
    """Specialized cache for knowledge base queries"""
    
    def __init__(self, cache: Optional[PerformanceCache] = None):
        self.cache = cache or get_cache()
    
    async def get_knowledge_result(self, query: str, source: str = "ptolemies") -> Optional[Dict[str, Any]]:
        """Get cached knowledge query result"""
        cache_key = self.cache._generate_key("knowledge", source, query)
        return self.cache.get(cache_key)
    
    async def store_knowledge_result(self, query: str, result: Dict[str, Any], 
                                    source: str = "ptolemies", ttl: int = 1800) -> None:
        """Store knowledge query result in cache"""
        cache_key = self.cache._generate_key("knowledge", source, query)
        self.cache.set(cache_key, result, ttl)


class MCPToolCache:
    """Specialized cache for MCP tool responses"""
    
    def __init__(self, cache: Optional[PerformanceCache] = None):
        self.cache = cache or get_cache()
    
    async def get_tool_response(self, tool_name: str, 
                               parameters: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached MCP tool response"""
        cache_key = self.cache._generate_key("mcp_tool", tool_name, parameters)
        return self.cache.get(cache_key)
    
    async def store_tool_response(self, tool_name: str, parameters: Dict[str, Any],
                                 response: Dict[str, Any], ttl: int = 600) -> None:
        """Store MCP tool response in cache"""
        cache_key = self.cache._generate_key("mcp_tool", tool_name, parameters)
        self.cache.set(cache_key, response, ttl)


# Cache warming functions
async def warm_agent_cache():
    """Pre-populate cache with common agent responses"""
    logfire.info("Warming agent cache")
    # Implementation would populate cache with common operations


async def warm_knowledge_cache():
    """Pre-populate cache with common knowledge queries"""
    logfire.info("Warming knowledge cache")
    # Implementation would populate cache with frequent queries


# Performance monitoring
def get_cache_performance_report() -> Dict[str, Any]:
    """Get comprehensive cache performance report"""
    cache = get_cache()
    stats = cache.get_stats()
    
    return {
        "cache_stats": stats,
        "timestamp": datetime.utcnow().isoformat(),
        "performance_metrics": {
            "avg_response_time": "TBD",  # Would be implemented with actual timing
            "cache_efficiency": stats["hit_rate"],
            "memory_usage": f"{stats['memory_cache_size']} items"
        }
    }