"""Initialize the database and create tables."""

import os
from app.database import engine, Base
from app.config import settings


def init_db() -> None:
    """Initialize the database and create all tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    print(f"Connecting to database: {settings.DATABASE_URL}")
    init_db()
