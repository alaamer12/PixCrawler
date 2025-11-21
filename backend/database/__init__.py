"""
Database configuration and session management.
"""

from backend.database.connection import get_session
from backend.models import Base

__all__ = ["get_session", "Base"]
