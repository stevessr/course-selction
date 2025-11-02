"""Common database utilities"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator
import os


def get_database_url(db_name: str = "course_data.db") -> str:
    """Get database URL from environment or default"""
    return os.getenv("DATABASE_URL", f"sqlite:///./{db_name}")


def create_db_engine(database_url: str):
    """Create a database engine"""
    return create_engine(
        database_url,
        connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
        pool_pre_ping=True,
    )


def create_session_factory(engine):
    """Create a session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session(SessionLocal) -> Generator[Session, None, None]:
    """Get a database session"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_database(engine, Base):
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
