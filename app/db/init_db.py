"""Create all database tables."""

from pathlib import Path
from app.db.session import engine
from app.db.models import Base
from app.utils.config import get_settings


def init_db() -> None:
    """Create database directory and all tables."""
    settings = get_settings()

    # Ensure data directory exists for SQLite file
    db_path = settings.database_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables created.")


if __name__ == "__main__":
    init_db()
