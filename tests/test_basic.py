"""Basic tests for the course selection system"""
import pytest
from backend.common import (
    verify_password,
    get_password_hash,
    generate_totp_secret,
    TokenBucket,
    RateLimiter,
)


def test_password_hashing():
    """Test password hashing and verification"""
    password = "test_password_123"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong_password", hashed)


def test_totp_generation():
    """Test TOTP secret generation"""
    secret = generate_totp_secret()
    
    assert secret is not None
    assert len(secret) == 32
    assert secret.isalnum()


def test_token_bucket():
    """Test token bucket rate limiting"""
    bucket = TokenBucket(capacity=10, refill_rate=1.0)
    
    # Should be able to consume initial tokens
    assert bucket.consume(5) == True
    assert bucket.get_available_tokens() == 5
    
    # Should not be able to consume more than available
    assert bucket.consume(10) == False
    
    # Should still have 5 tokens
    assert bucket.get_available_tokens() == 5


def test_rate_limiter():
    """Test rate limiter"""
    limiter = RateLimiter(default_capacity=5, default_refill_rate=1.0)
    
    # Should allow first request
    assert limiter.check_rate_limit("user1", tokens=1) == True
    
    # Should track per-key
    assert limiter.check_rate_limit("user2", tokens=1) == True
    
    # Should respect capacity
    for _ in range(4):
        limiter.check_rate_limit("user1", tokens=1)
    
    # user1 should be at capacity
    assert limiter.check_rate_limit("user1", tokens=1) == False
    
    # user2 should still have tokens
    assert limiter.check_rate_limit("user2", tokens=1) == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
