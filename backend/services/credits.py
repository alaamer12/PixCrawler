"""
Credit and billing service for PixCrawler.

This module provides business logic for credit management,
including balance tracking, transactions, and usage metrics.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.credits import CreditAccount, CreditTransaction
from backend.schemas.credits import (
    CreditAccountResponse,
    CreditTransactionResponse,
    TransactionType,
    TransactionStatus,
)
from .base import BaseService

__all__ = ['CreditService']


# noinspection PyTypeChecker
class CreditService(BaseService):
    """
    Service for managing credit accounts and transactions.

    Handles credit balance tracking, transaction recording,
    and usage metrics calculation.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize credit service.

        Args:
            session: Database session
        """
        super().__init__()
        self.session = session

    async def get_or_create_account(self, user_id: UUID) -> CreditAccount:
        """
        Get or create credit account for user.

        Args:
            user_id: User ID

        Returns:
            Credit account
        """
        # Try to get existing account
        result = await self.session.execute(
            select(CreditAccount).where(CreditAccount.user_id == user_id)
        )
        account = result.scalar_one_or_none()

        if account:
            return account

        # Create new account with default values
        account = CreditAccount(
            user_id=user_id,
            current_balance=0,
            monthly_usage=0,
            average_daily_usage=Decimal("0.00"),
            auto_refill_enabled=False,
            refill_threshold=100,
            refill_amount=500,
            monthly_limit=2000,
        )

        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)

        self.log_operation("create_credit_account", user_id=str(user_id))
        return account

    async def get_balance(self, user_id: UUID) -> CreditAccountResponse:
        """
        Get credit balance for user.

        Args:
            user_id: User ID

        Returns:
            Credit account response

        Raises:
            NotFoundError: If account not found
        """
        account = await self.get_or_create_account(user_id)
        return CreditAccountResponse.model_validate(account)

    async def get_transactions(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        transaction_type: Optional[TransactionType] = None,
    ) -> tuple[list[CreditTransaction], int]:
        """
        Get credit transactions for user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            transaction_type: Filter by transaction type

        Returns:
            Tuple of (transactions list, total count)
        """
        # Build query
        query = select(CreditTransaction).where(
            CreditTransaction.user_id == user_id
        )

        if transaction_type:
            query = query.where(CreditTransaction.type_ == transaction_type.value)

        # Get total count
        count_query = select(func.count()).select_from(CreditTransaction).where(
            CreditTransaction.user_id == user_id
        )
        if transaction_type:
            count_query = count_query.where(CreditTransaction.type_ == transaction_type.value)

        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated results
        query = query.order_by(CreditTransaction.created_at.desc())
        query = query.offset(skip).limit(limit)

        result = await self.session.execute(query)
        transactions = result.scalars().all()

        return list(transactions), total

    async def create_transaction(
        self,
        user_id: UUID,
        transaction_type: TransactionType,
        amount: int,
        description: str,
        metadata: Optional[dict] = None,
    ) -> CreditTransaction:
        """
        Create a credit transaction.

        Args:
            user_id: User ID
            transaction_type: Type of transaction
            amount: Credit amount (positive for additions, negative for usage)
            description: Transaction description
            metadata: Additional transaction data

        Returns:
            Created transaction

        Raises:
            ValidationError: If insufficient balance for usage
        """
        # Get or create account
        account = await self.get_or_create_account(user_id)

        # Calculate new balance
        new_balance = account.current_balance + amount

        # Validate balance
        if new_balance < 0:
            raise ValidationError(
                f"Insufficient credits. Current balance: {account.current_balance}, "
                f"Required: {abs(amount)}"
            )

        # Create transaction
        transaction = CreditTransaction(
            account_id=account.id,
            user_id=user_id,
            type_=transaction_type.value,
            description=description,
            amount=amount,
            balance_after=new_balance,
            status=TransactionStatus.COMPLETED.value,
            metadata_=metadata,
        )

        # Update account balance
        account.current_balance = new_balance

        # Update monthly usage if this is a usage transaction
        if transaction_type == TransactionType.USAGE:
            account.monthly_usage += abs(amount)

        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)

        self.log_operation(
            "create_transaction",
            user_id=str(user_id),
            type=transaction_type.value,
            amount=amount,
        )

        return transaction

    async def get_usage_metrics(self, user_id: UUID, days: int = 30) -> dict:
        """
        Get usage metrics for user.

        Args:
            user_id: User ID
            days: Number of days to analyze

        Returns:
            Usage metrics dictionary
        """
        # Get account
        account = await self.get_or_create_account(user_id)

        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get usage transactions in period
        result = await self.session.execute(
            select(
                func.sum(CreditTransaction.amount).label('total_usage'),
                func.count(CreditTransaction.id).label('transaction_count'),
            )
            .where(
                and_(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.type_ == TransactionType.USAGE.value,
                    CreditTransaction.created_at >= start_date,
                )
            )
        )

        row = result.one()
        total_usage = abs(row.total_usage or 0)
        transaction_count = row.transaction_count or 0

        # Calculate average daily usage
        avg_daily_usage = total_usage / days if days > 0 else 0

        return {
            "current_balance": account.current_balance,
            "monthly_usage": account.monthly_usage,
            "period_usage": total_usage,
            "period_days": days,
            "average_daily_usage": round(avg_daily_usage, 2),
            "transaction_count": transaction_count,
            "auto_refill_enabled": account.auto_refill_enabled,
            "refill_threshold": account.refill_threshold,
        }
