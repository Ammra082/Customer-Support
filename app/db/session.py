"""Database session factory and dependency injection."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.utils.config import get_settings

settings = get_settings()

# SQLite engine — check_same_thread=False required for FastAPI threading
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI dependency that yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
