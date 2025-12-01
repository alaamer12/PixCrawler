"""
Credit and billing schemas for PixCrawler.

This module defines Pydantic schemas for credit system validation,
including accounts, transactions, and usage tracking.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, computed_field

__all__ = [
    'TransactionType',
    'TransactionStatus',
    'CreditAccountBase',
    'CreditAccountCreate',
    'CreditAccountUpdate',
    'CreditAccountResponse',
    'CreditTransactionBase',
    'CreditTransactionCreate',
    'CreditTransactionResponse',
    'CreditTransactionListResponse',
    'AutoRefillSettings',
]


class TransactionType(str, Enum):
    """Credit transaction types."""
    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"


class TransactionStatus(str, Enum):
    """Credit transaction statuses."""
    COMPLETED = "completed"
    PENDING = "pending"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CreditAccountBase(BaseModel):
    """Base schema for credit accounts."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        use_enum_values=True,
    )
    
    current_balance: int = Field(
        default=0,
        ge=0,
        description="Current credit balance",
        examples=[1000, 500, 0],
    )
    
    monthly_usage: int = Field(
        default=0,
        ge=0,
        description="Credits used this month",
        examples=[250, 1500],
    )
    
    average_daily_usage: Decimal = Field(
        default=Decimal("0.00"),
        ge=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        description="Average daily credit usage",
        examples=[Decimal("10.50"), Decimal("25.75")],
    )


class AutoRefillSettings(BaseModel):
    """Auto-refill configuration schema."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    auto_refill_enabled: bool = Field(
        default=False,
        description="Enable automatic refill",
    )
    
    refill_threshold: int = Field(
        default=100,
        gt=0,
        le=10000,
        description="Balance threshold to trigger refill",
        examples=[100, 500],
    )
    
    refill_amount: int = Field(
        default=500,
        gt=0,
        le=50000,
        description="Amount to add when refilling",
        examples=[500, 1000, 5000],
    )
    
    monthly_limit: int = Field(
        default=2000,
        gt=0,
        le=100000,
        description="Maximum credits per month",
        examples=[2000, 10000],
    )
    
    @field_validator('refill_amount')
    @classmethod
    def validate_refill_amount(cls, v: int, info) -> int:
        """Ensure refill amount is greater than threshold."""
        if 'refill_threshold' in info.data and v <= info.data['refill_threshold']:
            raise ValueError('refill_amount must be greater than refill_threshold')
        return v


class CreditAccountCreate(CreditAccountBase, AutoRefillSettings):
    """Schema for creating credit accounts."""
    
    user_id: UUID = Field(
        description="User ID",
    )


class CreditAccountUpdate(BaseModel):
    """Schema for updating credit accounts."""
    
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
    )
    
    auto_refill_enabled: Optional[bool] = Field(
        default=None,
        description="Enable automatic refill",
    )
    
    refill_threshold: Optional[int] = Field(
        default=None,
        gt=0,
        le=10000,
        description="Balance threshold to trigger refill",
    )
    
    refill_amount: Optional[int] = Field(
        default=None,
        gt=0,
        le=50000,
        description="Amount to add when refilling",
    )
    
    monthly_limit: Optional[int] = Field(
        default=None,
        gt=0,
        le=100000,
        description="Maximum credits per month",
    )


class CreditAccountResponse(CreditAccountBase, AutoRefillSettings):
    """Schema for credit account responses."""
    
    id: UUID = Field(description="Account ID")
    user_id: UUID = Field(description="User ID")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    
    @computed_field
    @property
    def is_low_balance(self) -> bool:
        """Check if balance is below refill threshold."""
        return self.current_balance < self.refill_threshold
    
    @computed_field
    @property
    def days_until_depleted(self) -> Optional[float]:
        """Estimate days until balance depleted based on average usage."""
        if self.average_daily_usage <= 0:
            return None
        return float(self.current_balance) / float(self.average_daily_usage)


class CreditTransactionBase(BaseModel):
    """Base schema for credit transactions."""
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        use_enum_values=True,
    )
    
    type: TransactionType = Field(
        description="Transaction type",
        examples=["purchase", "usage"],
    )
    
    description: str = Field(
        min_length=1,
        max_length=1000,
        description="Transaction description",
        examples=["Credit purchase via Lemon Squeezy", "Image processing usage"],
    )
    
    amount: int = Field(
        description="Credit amount (positive for additions, negative for usage)",
        examples=[500, -50],
    )
    
    metadata_: Optional[dict] = Field(
        default=None,
        alias="metadata",
        description="Additional transaction data",
        examples=[{"lemonsqueezy_order_id": "order_123", "invoice_id": "inv_456"}],
    )


class CreditTransactionCreate(CreditTransactionBase):
    """Schema for creating credit transactions."""
    
    account_id: UUID = Field(description="Credit account ID")
    user_id: UUID = Field(description="User ID")
    balance_after: int = Field(ge=0, description="Balance after transaction")
    status: TransactionStatus = Field(
        default=TransactionStatus.COMPLETED,
        description="Transaction status",
    )


class CreditTransactionResponse(CreditTransactionBase):
    """Schema for credit transaction responses."""
    
    id: UUID = Field(description="Transaction ID")
    account_id: UUID = Field(description="Credit account ID")
    user_id: UUID = Field(description="User ID")
    balance_after: int = Field(description="Balance after transaction")
    status: TransactionStatus = Field(description="Transaction status")
    created_at: datetime = Field(description="Transaction timestamp")
    
    @computed_field
    @property
    def is_credit(self) -> bool:
        """Check if transaction adds credits."""
        return self.amount > 0
    
    @computed_field
    @property
    def is_debit(self) -> bool:
        """Check if transaction removes credits."""
        return self.amount < 0


class CreditTransactionListResponse(BaseModel):
    """Schema for credit transaction list response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    data: list[CreditTransactionResponse] = Field(
        description="List of credit transactions",
        examples=[[{
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "account_id": "123e4567-e89b-12d3-a456-426614174000",
            "user_id": "123e4567-e89b-12d3-a456-426614174000",
            "type": "purchase",
            "description": "Credit purchase via Lemon Squeezy",
            "amount": 500,
            "balance_after": 1500,
            "status": "completed",
            "metadata": {"lemonsqueezy_order_id": "order_123"},
            "created_at": "2024-01-27T10:00:00Z"
        }]]
    )
    
    meta: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 50},
        description="Pagination metadata",
        examples=[{"total": 100, "skip": 0, "limit": 50}]
    )
