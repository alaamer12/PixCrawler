"""
Credit and billing models for PixCrawler.

This module defines SQLAlchemy ORM models for the credit system,
including credit accounts, transactions, and usage tracking.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    Numeric,
    String,
    Text,
    func,
    UUID as SQLAlchemyUUID,
    CheckConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

__all__ = [
    'CreditAccount',
    'CreditTransaction',
]


class CreditAccount(Base, TimestampMixin):
    """
    Credit account model for user billing.
    
    Tracks user credit balance, usage, and auto-refill settings.
    
    Attributes:
        id: UUID primary key
        user_id: Reference to profiles.id
        current_balance: Current credit balance (non-negative)
        monthly_usage: Credits used this month
        average_daily_usage: Average daily usage for forecasting
        auto_refill_enabled: Whether auto-refill is active
        refill_threshold: Balance threshold to trigger refill
        refill_amount: Amount to add when refilling
        monthly_limit: Maximum credits per month
    """
    
    __tablename__ = "credit_accounts"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign key
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
    )
    
    # Balance tracking
    current_balance: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    monthly_usage: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    
    average_daily_usage: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        default=Decimal("0.00"),
        server_default="0.00",
    )
    
    # Auto-refill settings
    auto_refill_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )
    
    refill_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=100,
        server_default="100",
    )
    
    refill_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
        server_default="500",
    )
    
    monthly_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=2000,
        server_default="2000",
    )
    
    # Relationships
    transactions: Mapped[list["CreditTransaction"]] = relationship(
        "CreditTransaction",
        back_populates="account",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint("current_balance >= 0", name="ck_credit_accounts_balance_positive"),
        CheckConstraint("monthly_usage >= 0", name="ck_credit_accounts_monthly_usage_positive"),
        CheckConstraint("refill_threshold > 0", name="ck_credit_accounts_refill_threshold_positive"),
        CheckConstraint("refill_amount > 0", name="ck_credit_accounts_refill_amount_positive"),
        CheckConstraint("monthly_limit > 0", name="ck_credit_accounts_monthly_limit_positive"),
        Index("ix_credit_accounts_user_id", "user_id"),
    )


class CreditTransaction(Base):
    """
    Credit transaction model for billing history.
    
    Records all credit-related transactions including purchases,
    usage, refunds, and bonuses.
    
    Attributes:
        id: UUID primary key
        account_id: Reference to credit_accounts.id
        user_id: Reference to profiles.id (denormalized for queries)
        type: Transaction type (purchase, usage, refund, bonus)
        description: Human-readable description
        amount: Credit amount (positive for additions, negative for usage)
        balance_after: Account balance after transaction
        status: Transaction status (completed, pending, failed)
        metadata_: Additional transaction data (JSON)
        created_at: Transaction timestamp
    """
    
    __tablename__ = "credit_transactions"
    
    # Primary key
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    
    # Foreign keys
    account_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    user_id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    
    # Transaction details
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    balance_after: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="completed",
        server_default="completed",
        index=True,
    )
    
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Relationships
    account: Mapped["CreditAccount"] = relationship(
        "CreditAccount",
        back_populates="transactions",
        lazy="joined",
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "type IN ('purchase', 'usage', 'refund', 'bonus')",
            name="ck_credit_transactions_type_valid",
        ),
        CheckConstraint(
            "status IN ('completed', 'pending', 'failed', 'cancelled')",
            name="ck_credit_transactions_status_valid",
        ),
        CheckConstraint("balance_after >= 0", name="ck_credit_transactions_balance_positive"),
        Index("ix_credit_transactions_account_id", "account_id"),
        Index("ix_credit_transactions_user_id", "user_id"),
        Index("ix_credit_transactions_type", "type"),
        Index("ix_credit_transactions_status", "status"),
        Index("ix_credit_transactions_created_at", "created_at"),
        Index("ix_credit_transactions_user_created", "user_id", "created_at"),
    )
