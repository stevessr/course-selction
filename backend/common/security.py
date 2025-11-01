"""Common security utilities for authentication and authorization"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
import pyotp
import secrets
import hashlib
import os

# Debug mode flag - disables password encryption when true (FOR DEBUGGING ONLY!)
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() in ("true", "1", "yes")

# Password hashing
# Prefer pbkdf2_sha256 which doesn't rely on the native bcrypt C extension
# (avoids issues with broken bcrypt installs). Keep bcrypt_sha256/bcrypt as
# fallbacks for compatibility.
pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt_sha256", "bcrypt"], deprecated="auto")

# JWT configuration
# CRITICAL: Change SECRET_KEY in production via environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    if DEBUG_MODE:
        # Debug mode: compare plain text passwords
        print(f"WARNING: DEBUG MODE ENABLED - Plain text password comparison!")
        return plain_password == hashed_password

    # Normalize long passwords to avoid bcrypt 72-byte limitation
    pw = _normalize_password(plain_password)
    return pwd_context.verify(pw, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    if DEBUG_MODE:
        # Debug mode: return plain text password (NOT SECURE!)
        print(f"WARNING: DEBUG MODE ENABLED - Password '{password}' stored in PLAIN TEXT!")
        return password

    pw = _normalize_password(password)
    return pwd_context.hash(pw)


def _normalize_password(password: str) -> str:
    """Ensure the password length is compatible with bcrypt backends.

    If the UTF-8 encoded password exceeds 72 bytes, pre-hash it with SHA-256
    and return the hex digest (64 chars), which avoids bcrypt's 72-byte limit
    while remaining deterministic for verify operations.
    """
    if not isinstance(password, (bytes, str)):
        password = str(password)
    pw_bytes = password.encode() if isinstance(password, str) else password
    if len(pw_bytes) > 72:
        return hashlib.sha256(pw_bytes).hexdigest()
    return password


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_totp_secret() -> str:
    """Generate a TOTP secret for 2FA"""
    return pyotp.random_base32()


def verify_totp(secret: str, code: str) -> bool:
    """Verify a TOTP code"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


def get_totp_uri(secret: str, username: str, issuer: str = "Course Selection") -> str:
    """Get TOTP provisioning URI for QR code"""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_registration_code() -> str:
    """Generate a random registration code"""
    return secrets.token_urlsafe(24)


def generate_reset_code() -> str:
    """Generate a random 2FA reset code"""
    return secrets.token_urlsafe(24)


def hash_token(token: str) -> str:
    """Hash a token for storage"""
    return hashlib.sha256(token.encode()).hexdigest()


def generate_internal_token() -> str:
    """Generate an internal service authentication token"""
    return secrets.token_urlsafe(32)
