"""
Credit and billing API endpoints.

This module provides API endpoints for credit management,
including balance checking, transaction history, and usage metrics.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_session, get_current_user
from backend.api.types import CurrentUser
from backend.api.v1.response_models import get_common_responses
from backend.core.exceptions import NotFoundError, ValidationError
from backend.schemas.credits import (
    CreditAccountResponse,
    CreditTransactionResponse,
    CreditTransactionListResponse,
    TransactionType,
)
from backend.services.credits import CreditService

__all__ = ['router']

router = APIRouter(
    tags=["Credits & Billing"],
    responses=get_common_responses(401, 404, 500),
)


def get_credit_service(session: AsyncSession = Depends(get_session)) -> CreditService:
    """
    Dependency injection for CreditService.
    
    Args:
        session: Database session (injected by FastAPI)
        
    Returns:
        CreditService instance
    """
    return CreditService(session)


@router.get(
    "/balance",
    response_model=CreditAccountResponse,
    summary="Get Credit Balance",
    description="Retrieve the current credit balance and account settings for the authenticated user.",
    response_description="Credit account information with balance and settings",
    operation_id="getCreditBalance",
    responses={
        200: {
            "description": "Successfully retrieved credit balance",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "user_id": "123e4567-e89b-12d3-a456-426614174000",
                        "current_balance": 1500,
                        "monthly_usage": 250,
                        "average_daily_usage": "8.33",
                        "auto_refill_enabled": True,
                        "refill_threshold": 100,
                        "refill_amount": 500,
                        "monthly_limit": 2000,
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-27T10:00:00Z",
                        "is_low_balance": False,
                        "days_until_depleted": 180.0
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_credit_balance(
    current_user: CurrentUser,
    service: CreditService = Depends(get_credit_service),
) -> CreditAccountResponse:
    """
    Get credit balance for the current user.
    
    Returns the user's credit account information including:
    - Current balance
    - Monthly usage
    - Average daily usage
    - Auto-refill settings
    - Computed fields (is_low_balance, days_until_depleted)
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Credit service instance (injected)
        
    Returns:
        Credit account information
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if query fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        balance = await service.get_balance(user_id)
        return balance
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve credit balance: {str(e)}"
        )


@router.get(
    "/transactions",
    response_model=CreditTransactionListResponse,
    summary="Get Credit Transactions",
    description="Retrieve transaction history for the authenticated user with pagination and filtering.",
    response_description="Paginated list of credit transactions",
    operation_id="getCreditTransactions",
    responses={
        200: {
            "description": "Successfully retrieved transactions",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "account_id": "123e4567-e89b-12d3-a456-426614174000",
                                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                                "type": "purchase",
                                "description": "Credit purchase via Lemon Squeezy",
                                "amount": 500,
                                "balance_after": 1500,
                                "status": "completed",
                                "metadata": {"lemonsqueezy_order_id": "order_123"},
                                "created_at": "2024-01-27T10:00:00Z",
                                "is_credit": True,
                                "is_debit": False
                            }
                        ],
                        "meta": {
                            "total": 25,
                            "skip": 0,
                            "limit": 50
                        }
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_credit_transactions(
    current_user: CurrentUser,
    service: CreditService = Depends(get_credit_service),
    skip: int = Query(0, ge=0, description="Number of items to skip for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Maximum items to return (max: 100)"),
    type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
) -> CreditTransactionListResponse:
    """
    Get credit transaction history for the current user.
    
    Returns a paginated list of all credit transactions including:
    - Purchases (credit additions)
    - Usage (credit deductions)
    - Refunds
    - Bonuses
    
    **Query Parameters:**
    - `skip` (int): Pagination offset (default: 0)
    - `limit` (int): Items per page (default: 50, max: 100)
    - `type` (str): Filter by type (purchase, usage, refund, bonus)
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Credit service instance (injected)
        skip: Number of items to skip
        limit: Maximum items to return
        type: Transaction type filter
        
    Returns:
        Paginated list of credit transactions
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if query fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        transactions, total = await service.get_transactions(
            user_id=user_id,
            skip=skip,
            limit=limit,
            transaction_type=type,
        )
        
        # Transform to response model
        data = [CreditTransactionResponse.model_validate(t) for t in transactions]
        
        return CreditTransactionListResponse(
            data=data,
            meta={"total": total, "skip": skip, "limit": limit}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve transactions: {str(e)}"
        )


@router.post(
    "/purchase",
    response_model=CreditTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Purchase Credits",
    description="Purchase credits via payment integration (Lemon Squeezy). This endpoint creates a transaction record.",
    response_description="Created transaction record",
    operation_id="purchaseCredits",
    responses={
        201: {
            "description": "Credit purchase successful",
            "content": {
                "application/json": {
                    "example": {
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
                    }
                }
            }
        },
        **get_common_responses(401, 422, 500)
    }
)
async def purchase_credits(
    current_user: CurrentUser,
    service: CreditService = Depends(get_credit_service),
    amount: int = Query(..., gt=0, le=50000, description="Amount of credits to purchase"),
    payment_id: Optional[str] = Query(None, description="Lemon Squeezy order ID"),
) -> CreditTransactionResponse:
    """
    Purchase credits for the current user.
    
    Creates a credit transaction record for a successful payment.
    In production, this should be called after Lemon Squeezy payment confirmation.
    
    **Note:** This is a simplified implementation. In production:
    1. Frontend initiates Lemon Squeezy payment
    2. Lemon Squeezy webhook confirms payment
    3. Backend creates transaction via this endpoint
    
    **Query Parameters:**
    - `amount` (int): Credits to purchase (1-50000)
    - `payment_id` (str): Lemon Squeezy order ID for reference
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Credit service instance (injected)
        amount: Amount of credits to purchase
        payment_id: Payment provider transaction ID
        
    Returns:
        Created transaction record
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 422 if validation fails
        HTTPException: 500 if transaction creation fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        
        # Create purchase transaction
        transaction = await service.create_transaction(
            user_id=user_id,
            transaction_type=TransactionType.PURCHASE,
            amount=amount,
            description=f"Credit purchase of {amount} credits",
            metadata={"payment_id": payment_id} if payment_id else None,
        )
        
        return CreditTransactionResponse.model_validate(transaction)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to purchase credits: {str(e)}"
        )


@router.get(
    "/usage",
    response_model=dict,
    summary="Get Credit Usage Metrics",
    description="Retrieve usage statistics and metrics for the authenticated user over a specified period.",
    response_description="Usage metrics and statistics",
    operation_id="getCreditUsage",
    responses={
        200: {
            "description": "Successfully retrieved usage metrics",
            "content": {
                "application/json": {
                    "example": {
                        "current_balance": 1500,
                        "monthly_usage": 250,
                        "period_usage": 450,
                        "period_days": 30,
                        "average_daily_usage": 15.0,
                        "transaction_count": 12,
                        "auto_refill_enabled": True,
                        "refill_threshold": 100
                    }
                }
            }
        },
        **get_common_responses(401, 500)
    }
)
async def get_credit_usage(
    current_user: CurrentUser,
    service: CreditService = Depends(get_credit_service),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze (1-365)"),
) -> dict:
    """
    Get credit usage metrics for the current user.
    
    Returns usage statistics over a specified period including:
    - Current balance
    - Monthly usage
    - Period usage
    - Average daily usage
    - Transaction count
    - Auto-refill settings
    
    **Query Parameters:**
    - `days` (int): Analysis period in days (default: 30, max: 365)
    
    **Authentication Required:** Bearer token
    
    Args:
        current_user: Current authenticated user (injected)
        service: Credit service instance (injected)
        days: Number of days to analyze
        
    Returns:
        Usage metrics dictionary
        
    Raises:
        HTTPException: 401 if authentication fails
        HTTPException: 500 if query fails
    """
    try:
        user_id = UUID(current_user["user_id"])
        metrics = await service.get_usage_metrics(user_id, days)
        return metrics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage metrics: {str(e)}"
        )
