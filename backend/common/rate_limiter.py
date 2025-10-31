"""Rate limiting using token bucket algorithm"""
import time
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: int  # Maximum tokens in bucket
    refill_rate: float  # Tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    lock: Lock = field(default_factory=Lock, init=False)

    def __post_init__(self):
        self.tokens = self.capacity
        self.last_refill = time.time()

    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens, return True if successful"""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_available_tokens(self) -> int:
        """Get number of available tokens"""
        with self.lock:
            self._refill()
            return int(self.tokens)

    def get_wait_time(self, tokens: int = 1) -> float:
        """Get time to wait until tokens are available"""
        with self.lock:
            self._refill()
            if self.tokens >= tokens:
                return 0
            shortage = tokens - self.tokens
            return shortage / self.refill_rate


class RateLimiter:
    """Rate limiter managing multiple token buckets"""

    def __init__(self, default_capacity: int = 10, default_refill_rate: float = 1.0):
        self.default_capacity = default_capacity
        self.default_refill_rate = default_refill_rate
        self.buckets: Dict[str, TokenBucket] = {}
        self.lock = Lock()

    def get_bucket(self, key: str) -> TokenBucket:
        """Get or create a token bucket for a key"""
        with self.lock:
            if key not in self.buckets:
                self.buckets[key] = TokenBucket(
                    capacity=self.default_capacity,
                    refill_rate=self.default_refill_rate
                )
            return self.buckets[key]

    def check_rate_limit(self, key: str, tokens: int = 1) -> bool:
        """Check if request is allowed under rate limit"""
        bucket = self.get_bucket(key)
        return bucket.consume(tokens)

    def get_available_tokens(self, key: str) -> int:
        """Get available tokens for a key"""
        bucket = self.get_bucket(key)
        return bucket.get_available_tokens()

    def get_wait_time(self, key: str, tokens: int = 1) -> float:
        """Get wait time for tokens to be available"""
        bucket = self.get_bucket(key)
        return bucket.get_wait_time(tokens)

    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """Remove buckets that haven't been used recently"""
        with self.lock:
            now = time.time()
            keys_to_remove = [
                key for key, bucket in self.buckets.items()
                if now - bucket.last_refill > max_age_seconds
            ]
            for key in keys_to_remove:
                del self.buckets[key]


class IPRateLimiter:
    """Rate limiter with IP-based tracking and X-Forwarded-For support"""

    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        self.rate_limiter = RateLimiter(capacity, refill_rate)

    def get_client_ip(self, request_headers: Dict[str, str]) -> str:
        """Extract client IP from headers, supporting X-Forwarded-For"""
        # Check X-Forwarded-For header
        forwarded_for = request_headers.get("x-forwarded-for", "")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct connection IP
        return request_headers.get("x-real-ip", "unknown")

    def check_rate_limit(
        self, 
        request_headers: Dict[str, str], 
        user_id: Optional[int] = None,
        tokens: int = 1
    ) -> bool:
        """Check rate limit based on IP and optionally user ID"""
        ip = self.get_client_ip(request_headers)
        
        # Use IP-based rate limiting
        ip_key = f"ip:{ip}"
        if not self.rate_limiter.check_rate_limit(ip_key, tokens):
            return False
        
        # Additional user-based rate limiting if user_id provided
        if user_id is not None:
            user_key = f"user:{user_id}"
            if not self.rate_limiter.check_rate_limit(user_key, tokens):
                return False
        
        return True

    def get_wait_time(
        self,
        request_headers: Dict[str, str],
        user_id: Optional[int] = None,
        tokens: int = 1
    ) -> float:
        """Get wait time until request can be processed"""
        ip = self.get_client_ip(request_headers)
        ip_key = f"ip:{ip}"
        wait_time = self.rate_limiter.get_wait_time(ip_key, tokens)
        
        if user_id is not None:
            user_key = f"user:{user_id}"
            user_wait = self.rate_limiter.get_wait_time(user_key, tokens)
            wait_time = max(wait_time, user_wait)
        
        return wait_time


# Global rate limiters for different purposes
course_selection_limiter = IPRateLimiter(capacity=10, refill_rate=0.1)  # 10 requests, refill 1 per 10 sec
api_limiter = IPRateLimiter(capacity=60, refill_rate=1.0)  # 60 requests per minute
