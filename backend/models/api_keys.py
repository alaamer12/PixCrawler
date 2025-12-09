"""
API key models for PixCrawler.

This module defines SQLAlchemy ORM models for API key management,
including key storage, permissions, and usage tracking.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from uuid import UUID

# noinspection PyPep8Naming
from sqlalchemy import (
    DateTime,
    Integer,
    String,
    func,
    UUID as SQLAlchemyUUID,
    CheckConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from database.models import Profile

__all__ = [
    'APIKey',
]


class APIKey(Base, TimestampMixin):
    """
    API key model for programmatic access.

    Stores hashed API keys with permissions, rate limits,
    and usage tracking.

    Attributes:
        id: UUID primary key
        user_id: Reference to profiles.id
        name: User-friendly key name
        key_hash: Hashed API key (bcrypt/argon2)
        key_prefix: Key prefix for identification (e.g., 'pk_live_')
        status: Key status (active, revoked, expired)
        permissions: JSON array of permissions
        rate_limit: Requests per hour limit
        usage_count: Total number of uses
        last_used_at: Last usage timestamp
        last_used_ip: Last IP address used from
        expires_at: Optional expiration timestamp
    """

    __tablename__ = "api_keys"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Key identification
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    key_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    key_prefix: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        server_default="active",
        index=True,
    )

    # Permissions and limits
    permissions: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default="[]",
    )

    rate_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000,
        server_default="1000",
    )

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    last_used_ip: Mapped[Optional[str]] = mapped_column(
        String(45),  # IPv6 max length
        nullable=True,
    )

    # Expiration
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    # Relationships
    user: Mapped["Profile"] = relationship(
        "Profile",
        back_populates="api_keys",
        lazy="joined",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'revoked', 'expired')",
            name="ck_api_keys_status_valid",
        ),
        CheckConstraint("rate_limit > 0", name="ck_api_keys_rate_limit_positive"),
        CheckConstraint("usage_count >= 0", name="ck_api_keys_usage_count_positive"),
        Index("ix_api_keys_user_id", user_id),
        Index("ix_api_keys_key_hash", key_hash),
        Index("ix_api_keys_key_prefix", key_prefix),
        Index("ix_api_keys_status", status),
        Index("ix_api_keys_last_used_at", last_used_at),
        Index("ix_api_keys_expires_at", expires_at),
        Index("ix_api_keys_user_status", user_id, status),
    )
