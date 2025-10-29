"""JWT 工具：生成与验证访问令牌。

本模块使用 PyJWT（在 requirements.txt 中声明）。提供两类函数：
- 低级函数：`create_access_token(payload, secret, expires_in)` / `decode_access_token(token, secret)`；
- 便捷函数：从环境读取 SECRET_KEY，并生成/解码（`create_token_from_env`, `decode_token_from_env`）。

返回类型在验证失败时为 None，便于上层决定如何处理认证错误。
"""
from __future__ import annotations

import time
import os
from typing import Dict, Any, Optional

import jwt


def create_access_token(data: Dict[str, Any], secret: str, expires_in: int = 3600) -> str:
    """Create a JWT with given payload and secret.

    - data: payload (will be copied)
    - secret: HMAC secret
    - expires_in: seconds until expiration
    """
    payload = data.copy()
    now = int(time.time())
    payload.setdefault("iat", now)
    payload.setdefault("exp", now + expires_in)
    return jwt.encode(payload, secret, algorithm="HS256")


def decode_access_token(token: str, secret: str) -> Optional[Dict[str, Any]]:
    """Decode JWT with given secret. Returns payload dict or None on failure."""
    try:
        decoded = jwt.decode(token, secret, algorithms=["HS256"])  # raises on failure
        return decoded
    except Exception:
        return None


def _get_secret_from_env(default: str = "dev-secret") -> str:
    return os.environ.get("SECRET_KEY") or default


def create_token_from_env(data: Dict[str, Any], expires_minutes: int = 60) -> str:
    """Create a JWT using SECRET_KEY from the environment (or default)."""
    secret = _get_secret_from_env()
    return create_access_token(data, secret, expires_in=expires_minutes * 60)


def decode_token_from_env(token: str) -> Optional[Dict[str, Any]]:
    """Decode a JWT using SECRET_KEY from the environment (or default).

    Returns payload dict on success or None on failure.
    """
    secret = _get_secret_from_env()
    return decode_access_token(token, secret)


__all__ = [
    "create_access_token",
    "decode_access_token",
    "create_token_from_env",
    "decode_token_from_env",
]
