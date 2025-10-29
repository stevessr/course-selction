"""management.database package

提供 sqlite3 的轻量封装接口（具体实现见 main.py）。
"""

from .main import init_db, get_connection, create_admin_if_missing, book_slot

__all__ = ["init_db", "get_connection", "create_admin_if_missing", "book_slot"]
import sqlite3