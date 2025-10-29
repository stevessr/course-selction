"""应用配置：数据库、限速（rate limit）和初始管理员账户。

使用环境变量进行预配置，提供 `get_config()` 返回一个配置对象。

支持的环境变量（示例）：
	# 数据库：优先使用 DB_URL（例如 sqlite:///./data.db 或 postgresql://user:pass@host:port/dbname）
	DB_URL             # 可选，完整的数据库连接字符串
	DB_DRIVER          # 可选，'sqlite'|'postgres'|'mysql'（仅作记录；当 DB_URL 未设置，才使用下面字段）
	DB_HOST
	DB_PORT
	DB_USER
	DB_PASSWORD
	DB_NAME

	# 限速（每分钟请求数）
	RATE_LIMIT_RPM     # 可选，整数，默认 60

	# 初始管理员账户（用于首次启动时创建管理员）
	ADMIN_USERNAME     # 可选，默认 'admin'
	ADMIN_PASSWORD     # 可选，明文密码（如果提供，会用 PBKDF2-HMAC-SHA256 派生），建议仅在引导时使用一次
	ADMIN_PASSWORD_HASH# 可选，已派生的密码哈希（hex），优先于 ADMIN_PASSWORD
	ADMIN_SALT         # 可选，hex 格式的 salt，与 ADMIN_PASSWORD_HASH 配合使用（若只提供 ADMIN_PASSWORD 则自动生成 salt）

简要说明：
	- 本模块不引入额外第三方依赖，使用标准库实现密码派生（PBKDF2-HMAC-SHA256）。
	- 仅在需要时（例如应用第一次启动）使用 `get_config()` 返回的 `admin` 信息来创建初始管理员。
	- 如果需要更强的密码策略或第三方库（bcrypt/argon2），建议在部署时替换相关函数。
"""

from __future__ import annotations

import os
import binascii
from dataclasses import dataclass
from typing import Optional
import hashlib


def _int_env(name: str, default: int) -> int:
	v = os.environ.get(name)
	if v is None:
		return default
	try:
		return int(v)
	except ValueError:
		return default


def _hex_bytes(b: bytes) -> str:
	return binascii.hexlify(b).decode()


def _from_hex(s: str) -> bytes:
	return binascii.unhexlify(s.encode())


def generate_salt(length: int = 16) -> bytes:
	return os.urandom(length)


def hash_password(password: str, salt: Optional[bytes] = None, iterations: int = 100_000) -> tuple[str, str]:
	"""使用 PBKDF2-HMAC-SHA256 对明文密码派生哈希。

	返回 (hash_hex, salt_hex)
	"""
	if salt is None:
		salt = generate_salt()
	dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
	return _hex_bytes(dk), _hex_bytes(salt)


def verify_password(password: str, hash_hex: str, salt_hex: str, iterations: int = 100_000) -> bool:
	try:
		salt = _from_hex(salt_hex)
	except Exception:
		return False
	dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
	return binascii.hexlify(dk).decode() == hash_hex


@dataclass
class DatabaseConfig:
	url: Optional[str] = None
	driver: Optional[str] = None
	host: Optional[str] = None
	port: Optional[int] = None
	user: Optional[str] = None
	password: Optional[str] = None
	name: Optional[str] = None


@dataclass
class RateLimitConfig:
	requests_per_minute: int = 60


@dataclass
class AdminAccount:
	username: str
	password_hash: Optional[str] = None
	salt: Optional[str] = None


@dataclass
class Config:
	db: DatabaseConfig
	rate_limit: RateLimitConfig
	admin: AdminAccount


def get_config() -> Config:
	"""从环境变量读取配置并返回 Config 对象（带简单校验和默认值）。"""
	# 数据库：优先 DB_URL
	db_url = os.environ.get("DB_URL")
	db_driver = os.environ.get("DB_DRIVER")

	if db_url:
		db = DatabaseConfig(url=db_url, driver=db_driver)
	else:
		# 支持 sqlite 默认文件数据库
		driver = (db_driver or "sqlite").lower()
		if driver == "sqlite":
			# 默认文件路径
			default_sqlite = os.environ.get("SQLITE_PATH", "./data.db")
			db = DatabaseConfig(url=f"sqlite:///{default_sqlite}", driver="sqlite")
		else:
			host = os.environ.get("DB_HOST")
			port = os.environ.get("DB_PORT")
			user = os.environ.get("DB_USER")
			password = os.environ.get("DB_PASSWORD")
			name = os.environ.get("DB_NAME")
			port_int = None
			try:
				port_int = int(port) if port else None
			except ValueError:
				port_int = None
			db = DatabaseConfig(
				url=None,
				driver=driver,
				host=host,
				port=port_int,
				user=user,
				password=password,
				name=name,
			)

	# 限速
	rpm = _int_env("RATE_LIMIT_RPM", 60)
	rate = RateLimitConfig(requests_per_minute=rpm)

	# 管理员账户
	admin_username = os.environ.get("ADMIN_USERNAME", "admin")
	admin_hash = os.environ.get("ADMIN_PASSWORD_HASH")
	admin_salt = os.environ.get("ADMIN_SALT")
	admin_password = os.environ.get("ADMIN_PASSWORD")

	if admin_hash and admin_salt:
		admin = AdminAccount(username=admin_username, password_hash=admin_hash, salt=admin_salt)
	elif admin_password:
		h, s = hash_password(admin_password)
		admin = AdminAccount(username=admin_username, password_hash=h, salt=s)
	else:
		# 没有提供密码信息：保留用户名，但哈希为空，调用方需在启动时检查并创建管理员
		admin = AdminAccount(username=admin_username, password_hash=None, salt=None)

	cfg = Config(db=db, rate_limit=rate, admin=admin)

	# 简单验证（可扩展）
	if cfg.db.url is None and cfg.db.driver != "sqlite":
		# 非 sqlite 且没有完整 url，确保必要字段存在
		missing = []
		if not cfg.db.host:
			missing.append("DB_HOST")
		if not cfg.db.user:
			missing.append("DB_USER")
		if not cfg.db.name:
			missing.append("DB_NAME")
		if missing:
			# 这里只是轻量提示，实际调用方可以捕获并处理
			raise RuntimeError(f"数据库配置不完整，缺少环境变量：{', '.join(missing)}")

	return cfg


if __name__ == "__main__":
	# 本地快速调试
	cfg = get_config()
	print("DB:", cfg.db)
	print("Rate limit:", cfg.rate_limit)
	print("Admin:", cfg.admin)

