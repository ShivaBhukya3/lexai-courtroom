"""Database connection and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from loguru import logger
from pathlib import Path

from database.models import Base

# Use SQLite as default for development (no PostgreSQL setup required)
_DEFAULT_DB = f"sqlite:///{Path(__file__).parent.parent / 'data' / 'lexai.db'}"
DATABASE_URL = os.getenv("DATABASE_URL", _DEFAULT_DB)

# Use in-memory SQLite for tests
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database initialized: {DATABASE_URL.split('://')[0]}")


def get_db() -> Session:
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
