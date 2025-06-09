"""
Rate Limiting Middleware for Agentical

This module provides a configurable rate limiting middleware to protect the
Agentical API from abuse, DoS attacks, and to ensure fair usage.

Features:
- Multiple rate limiting strategies (fixed window, sliding window, token bucket)
- Configurable limits by endpoint, method, and client
- Redis-based distributed rate limiting
- Memory-based fallback for development environments
- Custom response headers for limit information
"""

import time
import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union, Callable, Any, Set
from ipaddress import IPv4Address, IPv6Address
import logging
import hashlib

import logfire
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp
from fastapi import status

from agentical.core.exceptions import RateLimitError
from agentical.db.cache.redis_client import get_redis_client

# Logger setup
logger = logging.getLogger(__name__)


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies supported by the middleware."""
    FIXED_WINDOW = "fixed_window"  # Simple counter reset at regular intervals
    SLIDING_WINDOW = "sliding_window"  # Moving time window
    TOKEN_BUCKET = "token_bucket"  # Token bucket algorithm with refill
    LEAKY_BUCKET = "leaky_bucket"  # Leaky bucket algorithm with constant outflow


class RateLimitConfig:
    """Configuration for rate limits."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst: int = 5,
        strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
        exclude_paths: Optional[List[str]] = None,
        exclude_ips: Optional[List[str]] = None,
        exclude_methods: Optional[List[str]] = None,
        include_paths: Optional[List[str]] = None,
        per_endpoint: bool = False,
        per_method: bool = False,
        headers_enabled: bool = True,
        use_redis: bool = True,
        key_prefix: str = "rl:",
        window_seconds: int = 60,
    ):
        """Initialize rate limit configuration.
        
        Args:
            requests_per_minute: Maximum number of requests per minute
            burst: Additional requests allowed in bursts
            strategy: Rate limiting strategy to use
            exclude_paths: List of path prefixes to exclude from rate limiting
            exclude_ips: List of IP addresses to exclude from rate limiting
            exclude_methods: List of HTTP methods to exclude from rate limiting
            include_paths: List of path prefixes to include (if specified, only these paths are rate-limited)
            per_endpoint: Whether to apply rate limits per endpoint rather than globally
            per_method: Whether to apply rate limits per HTTP method
            headers_enabled: Whether to include rate limit headers in responses
            use_redis: Whether to use Redis for distributed rate limiting
            key_prefix: Prefix for Redis keys
            window_seconds: Time window in seconds for rate limiting
        """
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.strategy = strategy
        self.exclude_paths = exclude_paths or []
        self.exclude_ips = exclude_ips or []
        self.exclude_methods = exclude_methods or []
        self.include_paths = include_paths or []
        self.per_endpoint = per_endpoint
        self.per_method = per_method
        self.headers_enabled = headers_enabled
        self.use_redis = use_redis
        self.key_prefix = key_prefix
        self.window_seconds = window_seconds
        
        # Convert string IPs to IP objects for efficient comparison
        self._exclude_ip_objects: Set[Union[IPv4Address, IPv6Address]] = set()
        for ip in self.exclude_ips:
            try:
                if ":" in ip:
                    self._exclude_ip_objects.add(IPv6Address(ip))
                else:
                    self._exclude_ip_objects.add(IPv4Address(ip))
            except ValueError:
                logger.warning(f"Invalid IP address in exclude_ips: {ip}")


class MemoryRateLimiter:
    """In-memory rate limiter for development environments."""
    
    def __init__(self):
        """Initialize the in-memory rate limiter."""
        self.counters: Dict[str, Tuple[int, float]] = {}
        self.tokens: Dict[str, Tuple[int, float]] = {}
        self.leaky_buckets: Dict[str, Tuple[int, float]] = {}
    
    async def increment_fixed_window(
        self, key: str, window_seconds: int, limit: int
    ) -> Tuple[bool, int, int]:
        """Increment a counter in a fixed window.
        
        Args:
            key: The rate limit key
            window_seconds: The window size in seconds
            limit: The maximum count allowed
            
        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        now = time.time()
        current_window = int(now / window_seconds)
        counter_key = f"{key}:{current_window}"
        
        # Check if we need to reset the counter
        if counter_key in self.counters:
            count, _ = self.counters[counter_key]
            if count >= limit:
                return False, count, 0
            
            # Increment the counter
            self.counters[counter_key] = (count + 1, now)
            return True, count + 1, limit - (count + 1)
        else:
            # First request in this window
            self.counters[counter_key] = (1, now)
            return True, 1, limit - 1
    
    async def increment_sliding_window(
        self, key: str, window_seconds: int, limit: int
    ) -> Tuple[bool, int, int]:
        """Increment a counter in a sliding window.
        
        Args:
            key: The rate limit key
            window_seconds: The window size in seconds
            limit: The maximum count allowed
            
        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        now = time.time()
        cutoff = now - window_seconds
        
        # Clean up old entries and count recent ones
        count = 0
        for k in list(self.counters.keys()):
            if k.startswith(key):
                _, timestamp = self.counters[k]
                if timestamp < cutoff:
                    del self.counters[k]
                else:
                    count += 1
        
        if count >= limit:
            return False, count, 0
        
        # Add the new request
        counter_key = f"{key}:{now}"
        self.counters[counter_key] = (1, now)
        return True, count + 1, limit - (count + 1)
    
    async def check_token_bucket(
        self, key: str, capacity: int, refill_rate: float
    ) -> Tuple[bool, int, int]:
        """Check if a request is allowed using the token bucket algorithm.
        
        Args:
            key: The rate limit key
            capacity: The maximum number of tokens
            refill_rate: Tokens per second refill rate
            
        Returns:
            Tuple of (allowed, current_tokens, remaining)
        """
        now = time.time()
        
        if key in self.tokens:
            tokens, last_update = self.tokens[key]
            
            # Calculate token refill
            elapsed = now - last_update
            new_tokens = min(capacity, tokens + elapsed * refill_rate)
            
            if new_tokens < 1:
                return False, 0, int(new_tokens)
            
            # Consume a token
            self.tokens[key] = (new_tokens - 1, now)
            return True, int(new_tokens - 1), int(new_tokens - 1)
        else:
            # First request, initialize with full bucket minus one token
            self.tokens[key] = (capacity - 1, now)
            return True, capacity - 1, capacity - 1
    
    async def check_leaky_bucket(
        self, key: str, capacity: int, leak_rate: float
    ) -> Tuple[bool, int, int]:
        """Check if a request is allowed using the leaky bucket algorithm.
        
        Args:
            key: The rate limit key
            capacity: The maximum bucket size
            leak_rate: Units per second leak rate
            
        Returns:
            Tuple of (allowed, current_level, remaining)
        """
        now = time.time()
        
        if key in self.leaky_buckets:
            level, last_update = self.leaky_buckets[key]
            
            # Calculate leakage
            elapsed = now - last_update
            new_level = max(0, level - elapsed * leak_rate)
            
            if new_level >= capacity:
                return False, int(new_level), 0
            
            # Add to the bucket
            self.leaky_buckets[key] = (new_level + 1, now)
            return True, int(new_level + 1), int(capacity - new_level - 1)
        else:
            # First request, initialize with one unit
            self.leaky_buckets[key] = (1, now)
            return True, 1, capacity - 1


class RedisRateLimiter:
    """Redis-based distributed rate limiter."""
    
    def __init__(self, key_prefix: str = "rl:"):
        """Initialize the Redis rate limiter.
        
        Args:
            key_prefix: Prefix for Redis keys
        """
        self.key_prefix = key_prefix
        self.redis = None
    
    async def _get_redis(self):
        """Get or initialize Redis client."""
        if self.redis is None:
            self.redis = await get_redis_client()
        return self.redis
    
    async def increment_fixed_window(
        self, key: str, window_seconds: int, limit: int
    ) -> Tuple[bool, int, int]:
        """Increment a counter in a fixed window using Redis.
        
        Args:
            key: The rate limit key
            window_seconds: The window size in seconds
            limit: The maximum count allowed
            
        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        redis = await self._get_redis()
        current_window = int(time.time() / window_seconds)
        redis_key = f"{self.key_prefix}{key}:{current_window}"
        
        # Get current count
        current = await redis.incr(redis_key)
        
        # Set expiry if this is a new key
        if current == 1:
            await redis.expire(redis_key, window_seconds)
        
        # Check if limit exceeded
        if current > limit:
            return False, current, 0
        
        return True, current, limit - current
    
    async def increment_sliding_window(
        self, key: str, window_seconds: int, limit: int
    ) -> Tuple[bool, int, int]:
        """Increment a counter in a sliding window using Redis sorted sets.
        
        Args:
            key: The rate limit key
            window_seconds: The window size in seconds
            limit: The maximum count allowed
            
        Returns:
            Tuple of (allowed, current_count, remaining)
        """
        redis = await self._get_redis()
        now = time.time()
        redis_key = f"{self.key_prefix}{key}"
        
        # Remove old entries
        await redis.zremrangebyscore(redis_key, 0, now - window_seconds)
        
        # Count remaining entries
        count = await redis.zcard(redis_key)
        
        if count >= limit:
            return False, count, 0
        
        # Add new entry with timestamp score
        await redis.zadd(redis_key, {str(now): now})
        await redis.expire(redis_key, window_seconds * 2)  # Ensure cleanup
        
        return True, count + 1, limit - (count + 1)
    
    async def check_token_bucket(
        self, key: str, capacity: int, refill_rate: float
    ) -> Tuple[bool, int, int]:
        """Check if a request is allowed using the token bucket algorithm with Redis.
        
        Args:
            key: The rate limit key
            capacity: The maximum number of tokens
            refill_rate: Tokens per second refill rate
            
        Returns:
            Tuple of (allowed, current_tokens, remaining)
        """
        redis = await self._get_redis()
        redis_key = f"{self.key_prefix}{key}:token"
        now = time.time()
        
        # Get current bucket state with Lua script for atomicity
        script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local refill_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local bucket = redis.call('hmget', key, 'tokens', 'last_update')
        local tokens = tonumber(bucket[1] or capacity)
        local last_update = tonumber(bucket[2] or now)
        
        -- Calculate token refill
        local elapsed = now - last_update
        local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)
        
        -- Attempt to consume a token
        if new_tokens < 1 then
            -- Update state but don't allow request
            redis.call('hmset', key, 'tokens', new_tokens, 'last_update', now)
            redis.call('expire', key, 300)  -- 5 minute expiry
            return {0, new_tokens, 0}
        else
            -- Consume a token and allow request
            redis.call('hmset', key, 'tokens', new_tokens - 1, 'last_update', now)
            redis.call('expire', key, 300)  -- 5 minute expiry
            return {1, new_tokens - 1, new_tokens - 1}
        end
        """
        
        result = await redis.eval(
            script,
            keys=[redis_key],
            args=[capacity, refill_rate, now]
        )
        
        allowed, current, remaining = result
        return bool(allowed), int(current), int(remaining)
    
    async def check_leaky_bucket(
        self, key: str, capacity: int, leak_rate: float
    ) -> Tuple[bool, int, int]:
        """Check if a request is allowed using the leaky bucket algorithm with Redis.
        
        Args:
            key: The rate limit key
            capacity: The maximum bucket size
            leak_rate: Units per second leak rate
            
        Returns:
            Tuple of (allowed, current_level, remaining)
        """
        redis = await self._get_redis()
        redis_key = f"{self.key_prefix}{key}:leaky"
        now = time.time()
        
        # Get current bucket state with Lua script for atomicity
        script = """
        local key = KEYS[1]
        local capacity = tonumber(ARGV[1])
        local leak_rate = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        
        local bucket = redis.call('hmget', key, 'level', 'last_update')
        local level = tonumber(bucket[1] or 0)
        local last_update = tonumber(bucket[2] or now)
        
        -- Calculate leakage
        local elapsed = now - last_update
        local new_level = math.max(0, level - elapsed * leak_rate)
        
        -- Attempt to add to the bucket
        if new_level >= capacity then
            -- Update state but don't allow request
            redis.call('hmset', key, 'level', new_level, 'last_update', now)
            redis.call('expire', key, 300)  -- 5 minute expiry
            return {0, new_level, 0}
        else
            -- Add to bucket and allow request
            redis.call('hmset', key, 'level', new_level + 1, 'last_update', now)
            redis.call('expire', key, 300)  -- 5 minute expiry
            return {1, new_level + 1, capacity - new_level - 1}
        end
        """
        
        result = await redis.eval(
            script,
            keys=[redis_key],
            args=[capacity, leak_rate, now]
        )
        
        allowed, current, remaining = result
        return bool(allowed), int(current), int(remaining)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[RateLimitConfig] = None,
    ):
        """Initialize the rate limiting middleware.
        
        Args:
            app: The ASGI application
            config: Rate limiting configuration
        """
        super().__init__(app)
        self.config = config or RateLimitConfig()
        
        # Initialize rate limiters
        self.memory_limiter = MemoryRateLimiter()
        self.redis_limiter = RedisRateLimiter(key_prefix=self.config.key_prefix)
    
    def should_rate_limit(self, request: Request) -> bool:
        """Determine if the request should be rate-limited.
        
        Args:
            request: The incoming request
            
        Returns:
            True if the request should be rate limited, False otherwise
        """
        # Check if path is in exclude list
        path = request.url.path
        for excluded_path in self.config.exclude_paths:
            if path.startswith(excluded_path):
                return False
        
        # If include paths are specified, check if path is included
        if self.config.include_paths:
            included = False
            for included_path in self.config.include_paths:
                if path.startswith(included_path):
                    included = True
                    break
            if not included:
                return False
        
        # Check if method is excluded
        if request.method in self.config.exclude_methods:
            return False
        
        # Check if client IP is excluded
        client_ip = request.client.host if request.client else None
        if client_ip:
            try:
                # Convert client IP to appropriate IP object for comparison
                ip_obj = IPv6Address(client_ip) if ":" in client_ip else IPv4Address(client_ip)
                if ip_obj in self.config._exclude_ip_objects:
                    return False
            except ValueError:
                # If IP parsing fails, continue with rate limiting
                pass
        
        return True
    
    def get_rate_limit_key(self, request: Request) -> str:
        """Generate a rate limit key based on the request.
        
        Args:
            request: The incoming request
            
        Returns:
            A key string for rate limiting
        """
        components = []
        
        # Always include client IP in the key
        client_ip = request.client.host if request.client else "unknown"
        components.append(f"ip:{client_ip}")
        
        # Get authenticated user if available
        user = getattr(request.state, "user", None)
        if user and getattr(user, "id", None):
            components.append(f"user:{user.id}")
        
        # Include endpoint if configured
        if self.config.per_endpoint:
            path = request.url.path
            # Create a hash of the path to avoid very long keys
            path_hash = hashlib.md5(path.encode()).hexdigest()[:8]
            components.append(f"path:{path_hash}")
        
        # Include method if configured
        if self.config.per_method:
            components.append(f"method:{request.method}")
        
        return ":".join(components)
    
    async def rate_limit_request(self, key: str) -> Tuple[bool, int, int]:
        """Apply rate limiting based on the configured strategy.
        
        Args:
            key: The rate limit key
            
        Returns:
            Tuple of (allowed, current, remaining)
        """
        # Use Redis if configured, otherwise use memory limiter
        limiter = self.redis_limiter if self.config.use_redis else self.memory_limiter
        
        try:
            if self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
                return await limiter.increment_fixed_window(
                    key, 
                    self.config.window_seconds, 
                    self.config.requests_per_minute
                )
            
            elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
                return await limiter.increment_sliding_window(
                    key,
                    self.config.window_seconds,
                    self.config.requests_per_minute
                )
            
            elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
                # Calculate refill rate from requests per minute
                refill_rate = self.config.requests_per_minute / self.config.window_seconds
                capacity = self.config.requests_per_minute + self.config.burst
                
                return await limiter.check_token_bucket(
                    key,
                    capacity,
                    refill_rate
                )
            
            elif self.config.strategy == RateLimitStrategy.LEAKY_BUCKET:
                # Calculate leak rate from requests per minute
                leak_rate = self.config.requests_per_minute / self.config.window_seconds
                capacity = self.config.burst
                
                return await limiter.check_leaky_bucket(
                    key,
                    capacity,
                    leak_rate
                )
            
            else:
                # Default to sliding window if strategy is unknown
                return await limiter.increment_sliding_window(
                    key,
                    self.config.window_seconds,
                    self.config.requests_per_minute
                )
        
        except Exception as e:
            # Log error but don't block request in case of rate limiting failure
            logfire.error(
                "Rate limiting error",
                error=str(e),
                key=key,
                strategy=self.config.strategy
            )
            return True, 0, self.config.requests_per_minute
    
    async def add_rate_limit_headers(
        self, response: Response, allowed: bool, current: int, remaining: int
    ) -> None:
        """Add rate limit headers to the response.
        
        Args:
            response: The response object
            allowed: Whether the request was allowed
            current: Current usage count
            remaining: Remaining requests allowed
        """
        if not self.config.headers_enabled:
            return
        
        response.headers["X-RateLimit-Limit"] = str(self.config.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.config.window_seconds))
        
        if not allowed:
            response.headers["Retry-After"] = str(self.config.window_seconds)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through rate limiting.
        
        Args:
            request: The incoming request
            call_next: The next middleware in the chain
            
        Returns:
            The response from the application
        """
        if not self.should_rate_limit(request):
            # Skip rate limiting for excluded requests
            return await call_next(request)
        
        # Generate rate limit key
        key = self.get_rate_limit_key(request)
        
        # Apply rate limiting
        with logfire.span("Rate limiting", key=key, strategy=self.config.strategy):
            allowed, current, remaining = await self.rate_limit_request(key)
            
            if not allowed:
                # Request is rate limited
                logfire.warning(
                    "Rate limit exceeded",
                    key=key,
                    current=current,
                    limit=self.config.requests_per_minute,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown"
                )
                
                # Create rate limit error
                error = RateLimitError(
                    retry_after=self.config.window_seconds,
                    message=f"Rate limit exceeded. Try again in {self.config.window_seconds} seconds."
                )
                
                # Create response
                content = error.to_dict()
                response = Response(
                    content=content,
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    media_type="application/json"
                )
                
                # Add rate limit headers
                await self.add_rate_limit_headers(response, False, current, 0)
                
                return response
        
        # Process the request
        response = await call_next(request)
        
        # Add rate limit headers to the response
        await self.add_rate_limit_headers(response, True, current, remaining)
        
        return response