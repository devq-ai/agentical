"""
Bot Protection Middleware for Agentical

This module provides middleware for detecting and mitigating automated bot attacks,
credential stuffing, and other automated threats to the Agentical API.

Features:
- Bot detection based on request patterns
- Protection against credential stuffing and brute force attacks
- Challenge-response mechanisms for suspicious requests
- IP reputation checking
- Device fingerprinting
- Rate limiting for suspicious activity
"""

import time
import re
import hashlib
import ipaddress
from typing import Dict, List, Optional, Set, Tuple, Callable, Any
import logging
from datetime import datetime, timedelta
import json
import uuid

import logfire
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.types import ASGIApp
from fastapi import status

from agentical.core.exceptions import RateLimitError
from agentical.db.cache.redis_client import get_redis_client

# Logger setup
logger = logging.getLogger(__name__)


class BotDetectionConfig:
    """Configuration for bot detection."""
    
    def __init__(
        self,
        enabled: bool = True,
        challenge_suspicious: bool = True,
        block_confirmed_bots: bool = True,
        suspicious_threshold: int = 70,  # 0-100 score
        bot_threshold: int = 90,  # 0-100 score
        exclude_paths: Optional[List[str]] = None,
        exclude_ips: Optional[List[str]] = None,
        tracking_cookie_name: str = "agentical_device",
        tracking_cookie_max_age: int = 86400 * 30,  # 30 days
        suspicious_headers: Optional[List[str]] = None,
        check_ip_reputation: bool = True,
        honeypot_field_names: Optional[List[str]] = None,
        use_redis: bool = True,
        redis_key_prefix: str = "bot:",
    ):
        """Initialize bot detection configuration.
        
        Args:
            enabled: Whether bot protection is enabled
            challenge_suspicious: Whether to issue challenges for suspicious requests
            block_confirmed_bots: Whether to block confirmed bots
            suspicious_threshold: Score threshold for suspicious requests
            bot_threshold: Score threshold for confirmed bots
            exclude_paths: List of paths to exclude from bot detection
            exclude_ips: List of IPs to exclude from bot detection
            tracking_cookie_name: Name of the cookie for device tracking
            tracking_cookie_max_age: Max age of the tracking cookie in seconds
            suspicious_headers: List of headers that indicate suspicious behavior
            check_ip_reputation: Whether to check IP reputation
            honeypot_field_names: List of honeypot field names
            use_redis: Whether to use Redis for state storage
            redis_key_prefix: Prefix for Redis keys
        """
        self.enabled = enabled
        self.challenge_suspicious = challenge_suspicious
        self.block_confirmed_bots = block_confirmed_bots
        self.suspicious_threshold = suspicious_threshold
        self.bot_threshold = bot_threshold
        self.exclude_paths = exclude_paths or ["/health", "/metrics", "/api/v1/health"]
        self.exclude_ips = exclude_ips or []
        self.tracking_cookie_name = tracking_cookie_name
        self.tracking_cookie_max_age = tracking_cookie_max_age
        self.suspicious_headers = suspicious_headers or [
            "PhantomJS", "HeadlessChrome", "Headless", "Python", "curl", "Go-http-client", "Java"
        ]
        self.check_ip_reputation = check_ip_reputation
        self.honeypot_field_names = honeypot_field_names or ["email_confirm", "website", "phone2", "address2"]
        self.use_redis = use_redis
        self.redis_key_prefix = redis_key_prefix
        
        # Convert IPs to network objects for efficient checking
        self._exclude_networks = []
        for ip in self.exclude_ips:
            try:
                if "/" in ip:  # CIDR notation
                    self._exclude_networks.append(ipaddress.ip_network(ip, strict=False))
                else:
                    self._exclude_networks.append(ipaddress.ip_address(ip))
            except ValueError:
                logger.warning(f"Invalid IP address in exclude_ips: {ip}")


class BotProtectionMiddleware(BaseHTTPMiddleware):
    """Middleware for detecting and blocking bot traffic."""
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[BotDetectionConfig] = None,
    ):
        """Initialize the bot protection middleware.
        
        Args:
            app: The ASGI application
            config: Bot detection configuration
        """
        super().__init__(app)
        self.config = config or BotDetectionConfig()
        self.redis = None
        
        # Patterns for bot detection
        self.bot_ua_pattern = re.compile(
            r"(?i)(bot|crawl|spider|slurp|scrape|http|curl|fetch|phantom|headless|python|java|go|ruby|wget|playwright)"
        )
        
        # Known bad IP ranges (example - should be replaced with actual data in production)
        self.known_bad_ip_ranges = [
            ipaddress.ip_network("192.0.2.0/24"),  # TEST-NET-1 for example purposes
        ]
    
    async def _get_redis(self):
        """Get or initialize Redis client."""
        if self.redis is None and self.config.use_redis:
            self.redis = await get_redis_client()
        return self.redis
    
    def _is_excluded(self, request: Request) -> bool:
        """Check if the request should be excluded from bot detection.
        
        Args:
            request: The incoming request
            
        Returns:
            True if the request should be excluded, False otherwise
        """
        # Check if path is excluded
        path = request.url.path
        for excluded_path in self.config.exclude_paths:
            if path.startswith(excluded_path):
                return True
        
        # Check if client IP is excluded
        client_ip = request.client.host if request.client else None
        if client_ip:
            try:
                ip_obj = ipaddress.ip_address(client_ip)
                # Check against excluded IPs/networks
                for network in self._exclude_networks:
                    if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network):
                        if ip_obj in network:
                            return True
                    elif ip_obj == network:
                        return True
            except ValueError:
                pass
        
        return False
    
    async def _get_device_fingerprint(self, request: Request) -> str:
        """Generate or retrieve a device fingerprint from cookies or request data.
        
        Args:
            request: The incoming request
            
        Returns:
            Device fingerprint string
        """
        # Check if fingerprint cookie exists
        fingerprint = request.cookies.get(self.config.tracking_cookie_name)
        if fingerprint:
            return fingerprint
        
        # Generate a new fingerprint based on request data
        ua = request.headers.get("user-agent", "")
        accept = request.headers.get("accept", "")
        accept_lang = request.headers.get("accept-language", "")
        accept_encoding = request.headers.get("accept-encoding", "")
        ip = request.client.host if request.client else "unknown"
        
        # Combine data to create fingerprint
        fingerprint_data = f"{ua}|{accept}|{accept_lang}|{accept_encoding}|{ip}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()
    
    async def _check_honeypot_fields(self, request: Request) -> bool:
        """Check if honeypot fields are filled in the request.
        
        Args:
            request: The incoming request
            
        Returns:
            True if honeypot fields are filled (bot detected), False otherwise
        """
        if request.method not in ["POST", "PUT", "PATCH"]:
            return False
        
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type.lower():
            try:
                body = await request.body()
                if body:
                    data = json.loads(body)
                    
                    # Check if any honeypot fields are filled
                    for field in self.config.honeypot_field_names:
                        if field in data and data[field]:
                            logfire.warning(
                                "Honeypot field filled",
                                field=field,
                                client_ip=request.client.host if request.client else "unknown",
                                path=request.url.path
                            )
                            return True
            except Exception:
                pass
        
        return False
    
    async def _check_suspicious_headers(self, request: Request) -> int:
        """Check request headers for suspicious bot indicators.
        
        Args:
            request: The incoming request
            
        Returns:
            Score indicating suspiciousness (0-100)
        """
        score = 0
        ua = request.headers.get("user-agent", "")
        
        # Check for missing or suspicious user agent
        if not ua:
            score += 30
        elif self.bot_ua_pattern.search(ua):
            score += 40
        
        # Check for suspicious headers
        for header in self.config.suspicious_headers:
            if header.lower() in ua.lower():
                score += 30
                break
        
        # Check for missing or inconsistent accept headers
        if not request.headers.get("accept"):
            score += 10
        if not request.headers.get("accept-language"):
            score += 10
        if not request.headers.get("accept-encoding"):
            score += 10
        
        # Check for unusual header combinations
        if "cookie" not in request.headers and "referer" not in request.headers:
            score += 20
        
        # Keep score within bounds
        return min(score, 100)
    
    async def _check_request_pattern(self, request: Request, fingerprint: str) -> int:
        """Check request patterns for bot-like behavior.
        
        Args:
            request: The incoming request
            fingerprint: Device fingerprint
            
        Returns:
            Score indicating suspiciousness (0-100)
        """
        score = 0
        
        # Check request velocity if Redis is available
        if self.config.use_redis:
            redis = await self._get_redis()
            if redis:
                now = time.time()
                key = f"{self.config.redis_key_prefix}req:{fingerprint}"
                
                # Get previous request times
                try:
                    # Store up to 20 most recent timestamps
                    await redis.zadd(key, {str(now): now})
                    await redis.zremrangebyrank(key, 0, -21)  # Keep only 20 most recent
                    await redis.expire(key, 3600)  # 1 hour expiry
                    
                    # Get timestamps within the last minute
                    timestamps = await redis.zrangebyscore(
                        key, now - 60, now, withscores=True
                    )
                    
                    # Check request frequency
                    if len(timestamps) > 30:  # More than 30 requests in a minute
                        score += 40
                    elif len(timestamps) > 15:  # More than 15 requests in a minute
                        score += 20
                    
                    # Check for perfectly timed requests (bot-like behavior)
                    if len(timestamps) >= 3:
                        intervals = []
                        last_time = None
                        for _, ts in timestamps:
                            if last_time is not None:
                                intervals.append(ts - last_time)
                            last_time = ts
                        
                        # Calculate standard deviation of intervals
                        if intervals:
                            mean = sum(intervals) / len(intervals)
                            variance = sum((i - mean) ** 2 for i in intervals) / len(intervals)
                            std_dev = variance ** 0.5
                            
                            # Very low standard deviation indicates automated requests
                            if std_dev < 0.1 and mean < 2.0:
                                score += 40
                            elif std_dev < 0.5 and mean < 5.0:
                                score += 20
                except Exception as e:
                    logfire.error("Error checking request patterns", error=str(e))
        
        return min(score, 100)
    
    async def _check_ip_reputation(self, request: Request) -> int:
        """Check IP reputation against known bad IP lists.
        
        Args:
            request: The incoming request
            
        Returns:
            Score indicating suspiciousness (0-100)
        """
        if not self.config.check_ip_reputation:
            return 0
        
        score = 0
        client_ip = request.client.host if request.client else None
        
        if not client_ip:
            return 0
        
        try:
            ip_obj = ipaddress.ip_address(client_ip)
            
            # Check against known bad IP ranges
            for bad_range in self.known_bad_ip_ranges:
                if ip_obj in bad_range:
                    score += 60
                    break
            
            # Check IP reputation in Redis if available
            if self.config.use_redis:
                redis = await self._get_redis()
                if redis:
                    key = f"{self.config.redis_key_prefix}ip:{client_ip}"
                    reputation = await redis.get(key)
                    if reputation:
                        score += min(int(reputation), 50)
        except ValueError:
            pass
        
        return min(score, 100)
    
    async def _update_ip_reputation(self, request: Request, score: int):
        """Update IP reputation based on detected score.
        
        Args:
            request: The incoming request
            score: Bot detection score
        """
        if not self.config.use_redis:
            return
        
        client_ip = request.client.host if request.client else None
        if not client_ip:
            return
        
        try:
            redis = await self._get_redis()
            if redis:
                key = f"{self.config.redis_key_prefix}ip:{client_ip}"
                
                # Get current reputation
                current = await redis.get(key)
                current_score = int(current) if current else 0
                
                # Update reputation based on new score
                if score >= self.config.bot_threshold:
                    # Confirmed bot - significant reputation penalty
                    new_score = min(current_score + 30, 100)
                elif score >= self.config.suspicious_threshold:
                    # Suspicious - moderate reputation penalty
                    new_score = min(current_score + 10, 100)
                else:
                    # Normal - small reputation improvement
                    new_score = max(current_score - 1, 0)
                
                # Store updated reputation with 24-hour expiry
                await redis.set(key, str(new_score), ex=86400)
        except Exception as e:
            logfire.error("Error updating IP reputation", error=str(e))
    
    async def _generate_challenge(self, request: Request, fingerprint: str) -> Response:
        """Generate a challenge response for suspicious requests.
        
        Args:
            request: The incoming request
            fingerprint: Device fingerprint
            
        Returns:
            Challenge response
        """
        # Generate a challenge token
        challenge_token = str(uuid.uuid4())
        
        # Store the challenge in Redis if available
        if self.config.use_redis:
            redis = await self._get_redis()
            if redis:
                key = f"{self.config.redis_key_prefix}challenge:{fingerprint}"
                await redis.set(key, challenge_token, ex=300)  # 5-minute expiry
        
        # Return challenge response
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "error": "challenge_required",
                "message": "Please complete the challenge to continue",
                "challenge_token": challenge_token,
                "type": "simple"  # For a real implementation, you might use CAPTCHA or other challenge types
            }
        )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request through bot protection middleware.
        
        Args:
            request: The incoming request
            call_next: The next middleware in the chain
            
        Returns:
            The response from the application
        """
        if not self.config.enabled or self._is_excluded(request):
            # Skip bot detection for excluded requests
            return await call_next(request)
        
        # Get device fingerprint
        fingerprint = await self._get_device_fingerprint(request)
        
        with logfire.span("Bot detection", fingerprint=fingerprint):
            # Perform bot detection checks
            headers_score = await self._check_suspicious_headers(request)
            pattern_score = await self._check_request_pattern(request, fingerprint)
            ip_score = await self._check_ip_reputation(request)
            honeypot_triggered = await self._check_honeypot_fields(request)
            
            # Calculate overall bot score
            bot_score = max(headers_score, pattern_score, ip_score)
            if honeypot_triggered:
                bot_score = 100  # Immediate bot classification
            
            # Log detection metrics
            logfire.info(
                "Bot detection metrics",
                fingerprint=fingerprint,
                headers_score=headers_score,
                pattern_score=pattern_score,
                ip_score=ip_score,
                honeypot_triggered=honeypot_triggered,
                overall_score=bot_score,
                path=request.url.path,
                method=request.method,
                client_ip=request.client.host if request.client else "unknown"
            )
            
            # Update IP reputation based on score
            await self._update_ip_reputation(request, bot_score)
            
            # Handle detected bots
            if bot_score >= self.config.bot_threshold and self.config.block_confirmed_bots:
                logfire.warning(
                    "Blocking confirmed bot",
                    score=bot_score,
                    fingerprint=fingerprint,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown"
                )
                
                # Return bot blocking response
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={
                        "error": "access_denied",
                        "message": "Automated access to this resource is not allowed"
                    }
                )
            
            # Issue challenge for suspicious requests
            if bot_score >= self.config.suspicious_threshold and self.config.challenge_suspicious:
                logfire.warning(
                    "Issuing challenge for suspicious request",
                    score=bot_score,
                    fingerprint=fingerprint,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown"
                )
                
                # Check if challenge token is provided in request
                challenge_token = request.headers.get("X-Challenge-Token")
                if not challenge_token:
                    # No challenge token provided, issue challenge
                    return await self._generate_challenge(request, fingerprint)
                
                # Verify challenge token if Redis is available
                if self.config.use_redis:
                    redis = await self._get_redis()
                    if redis:
                        key = f"{self.config.redis_key_prefix}challenge:{fingerprint}"
                        stored_token = await redis.get(key)
                        
                        if not stored_token or stored_token.decode() != challenge_token:
                            # Invalid challenge token
                            return await self._generate_challenge(request, fingerprint)
                        
                        # Valid token, remove it and proceed
                        await redis.delete(key)
        
        # Process the request
        response = await call_next(request)
        
        # Set tracking cookie if not already present
        if self.config.tracking_cookie_name not in request.cookies:
            response.set_cookie(
                key=self.config.tracking_cookie_name,
                value=fingerprint,
                max_age=self.config.tracking_cookie_max_age,
                httponly=True,
                secure=request.url.scheme == "https",
                samesite="lax"
            )
        
        return response