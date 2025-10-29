"""简易数据库层（SQLite）：初始化、管理员创建、基本预订 CRUD。

不依赖第三方 ORM，使用内置 sqlite3。目标是提供最小可用实现，用于引导和测试。
"""
from __future__ import annotations

import sqlite3
from typing import Optional

from management.config import get_config, AdminAccount


def _parse_sqlite_path(db_url: str) -> str:
    """解析 sqlite:///path 或 file:path 之类的简单形式，返回文件路径。"""
    if db_url.startswith("sqlite:///"):
        return db_url[len("sqlite:///"):]
    # 支持文件路径直接传入
    return db_url


def get_connection(db_url: str) -> sqlite3.Connection:
    path = _parse_sqlite_path(db_url)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_url: str) -> sqlite3.Connection:
    """初始化数据库并创建所需表，返回 sqlite3.Connection。"""
    conn = get_connection(db_url)
    cur = conn.cursor()
    # 用户表（管理员和普通用户）
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            salt TEXT,
            is_admin INTEGER DEFAULT 0
        )
        """
    )

    # 教师表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    # 学生表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    # 预订/占用表：记录教师或学生的时间段占用
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_type TEXT NOT NULL, -- 'teacher' or 'student'
            owner_id INTEGER NOT NULL,
            course_id INTEGER,
            start INTEGER NOT NULL,
            end INTEGER NOT NULL
        )
        """
    )

    conn.commit()
    return conn


def create_admin_if_missing(conn: sqlite3.Connection, admin: AdminAccount) -> None:
    """如果不存在管理员账户，则创建。admin.password_hash 和 salt 应该可用以直接写入。

    如果传入的 admin 只有 username 且没有 hash，则跳过创建并返回（调用方可选择创建空管理员）。
    """
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (admin.username,))
    row = cur.fetchone()
    if row:
        return
    if not admin.password_hash or not admin.salt:
        # 没有提供密码哈希，跳过创建（可按需改为抛出或记录警告）
        return
    cur.execute(
        "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (?, ?, ?, 1)",
        (admin.username, admin.password_hash, admin.salt),
    )
    conn.commit()


def create_user(conn: sqlite3.Connection, username: str, password_hash: str, salt: str, is_admin: bool = False) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password_hash, salt, is_admin) VALUES (?, ?, ?, ?)",
        (username, password_hash, salt, 1 if is_admin else 0),
    )
    conn.commit()
    return cur.lastrowid


def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[sqlite3.Row]:
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    return cur.fetchone()


def add_teacher(conn: sqlite3.Connection, name: str, email: Optional[str] = None, user_id: Optional[int] = None) -> int:
    cur = conn.cursor()
    cur.execute("INSERT INTO teachers (name, email, user_id) VALUES (?, ?, ?)", (name, email, user_id))
    conn.commit()
    return cur.lastrowid


def add_student(conn: sqlite3.Connection, name: str, email: Optional[str] = None, user_id: Optional[int] = None) -> int:
    cur = conn.cursor()
    cur.execute("INSERT INTO students (name, email, user_id) VALUES (?, ?, ?)", (name, email, user_id))
    conn.commit()
    return cur.lastrowid


def booking_conflict(conn: sqlite3.Connection, start: int, end: int) -> bool:
    """检查是否存在与给定区间有重叠的 booking。"""
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) as c FROM bookings WHERE NOT (end <= ? OR start >= ?)",
        (start, end),
    )
    row = cur.fetchone()
    return row["c"] > 0


def get_bookings_for_owner(conn: sqlite3.Connection, owner_type: str, owner_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE owner_type = ? AND owner_id = ? ORDER BY start", (owner_type, owner_id))
    return cur.fetchall()


def get_bookings_in_range(conn: sqlite3.Connection, start: int, end: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM bookings WHERE NOT (end <= ? OR start >= ?) ORDER BY start", (start, end))
    return cur.fetchall()


def book_slot(conn: sqlite3.Connection, owner_type: str, owner_id: int, start: int, end: int, course_id: Optional[int] = None) -> bool:
    """尝试为 owner 预订 [start, end)。若无冲突则插入并返回 True。
    注意：此处为简化实现，未做事务隔离以防并发冲突。
    """
    if booking_conflict(conn, start, end):
        return False
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bookings (owner_type, owner_id, course_id, start, end) VALUES (?, ?, ?, ?, ?)",
        (owner_type, owner_id, course_id, start, end),
    )
    conn.commit()
    return True


def unbook_slot(conn: sqlite3.Connection, booking_id: int) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()


if __name__ == "__main__":
    # 从环境变量读取配置并初始化数据库，然后尝试创建初始管理员
    cfg = get_config()
    if not cfg.db.url:
        print("no db url configured")
        raise SystemExit(1)
    conn = init_db(cfg.db.url)
    create_admin_if_missing(conn, cfg.admin)
    print("database initialized and admin ensured (if hash provided)")
