"""认证辅助：用户注册与验证（使用 config 中的 hash/verify 函数）。"""
from __future__ import annotations


import sqlite3

from management.config import hash_password, verify_password
from management.database.main import create_user, get_user_by_username


def register_user(conn: sqlite3.Connection, username: str, password: str, is_admin: bool = False) -> int:
    h, s = hash_password(password)
    return create_user(conn, username, h, s, is_admin=is_admin)


def authenticate_user(conn: sqlite3.Connection, username: str, password: str) -> bool:
    row = get_user_by_username(conn, username)
    if not row:
        return False
    # row may be sqlite3.Row
    stored_hash = row["password_hash"]
    salt = row["salt"]
    return verify_password(password, stored_hash, salt)


__all__ = ["register_user", "authenticate_user"]
