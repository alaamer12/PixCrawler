"""
API key service for PixCrawler.

This module provides business logic for API key management,
including creation, revocation, and usage tracking.
"""

import secrets
from datetime import datetime
from typing import Optional
from uuid import UUID

import bcrypt
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.api_keys import APIKey
from backend.schemas.api_keys import (
    APIKeyResponse,
    APIKeyStatus,
    APIKeyPermission,
)
from .base import BaseService

__all__ = ['APIKeyService']


class APIKeyService(BaseService):
    """
    Service for managing API keys.
    
    Handles API key creation, hashing, revocation,
    and usage tracking.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize API key service.
        
        Args:
            session: Database session
        """
        super().__init__()
        self.session = session
    
    def _generate_key(self) -> tuple[str, str, str]:
        """
        Generate a new API key with prefix and hash.
        
        Returns:
            Tuple of (full_key, prefix, hash)
        """
        # Generate random key
        random_part = secrets.token_urlsafe(32)
        prefix = "pk_live_"
        full_key = f"{prefix}{random_part}"
        
        # Hash the key
        key_hash = bcrypt.hashpw(full_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        return full_key, prefix, key_hash
    
    async def create_key(
        self,
        user_id: UUID,
        name: str,
        permissions: list[APIKeyPermission],
        rate_limit: int = 1000,
        expires_at: Optional[datetime] = None,
    ) -> tuple[APIKey, str]:
        """
        Create a new API key.
        
        Args:
            user_id: User ID
            name: Key name
            permissions: List of permissions
            rate_limit: Requests per hour limit
            expires_at: Optional expiration timestamp
            
        Returns:
            Tuple of (created key, full key string)
        """
        # Generate key
        full_key, prefix, key_hash = self._generate_key()
        
        # Create key record
        api_key = APIKey(
            user_id=user_id,
            name=name,
            key_hash=key_hash,
            key_prefix=prefix,
            status=APIKeyStatus.ACTIVE.value,
            permissions=[p.value for p in permissions],
            rate_limit=rate_limit,
            usage_count=0,
            expires_at=expires_at,
        )
        
        self.session.add(api_key)
        await self.session.commit()
        await self.session.refresh(api_key)
        
        self.log_operation(
            "create_api_key",
            user_id=str(user_id),
            key_id=str(api_key.id),
            name=name,
        )
        
        return api_key, full_key
    
    async def list_keys(
        self,
        user_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: Optional[APIKeyStatus] = None,
    ) -> tuple[list[APIKey], int]:
        """
        List API keys for user.
        
        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            status: Filter by status
            
        Returns:
            Tuple of (keys list, total count)
        """
        # Build query
        query = select(APIKey).where(APIKey.user_id == user_id)
        
        if status:
            query = query.where(APIKey.status == status.value)
        
        # Get total count
        count_query = select(func.count()).select_from(APIKey).where(
            APIKey.user_id == user_id
        )
        if status:
            count_query = count_query.where(APIKey.status == status.value)
        
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one()
        
        # Get paginated results
        query = query.order_by(APIKey.created_at.desc())
        query = query.offset(skip).limit(limit)
        
        result = await self.session.execute(query)
        keys = result.scalars().all()
        
        return list(keys), total
    
    async def get_key(self, key_id: UUID, user_id: UUID) -> Optional[APIKey]:
        """
        Get API key by ID.
        
        Args:
            key_id: Key ID
            user_id: User ID (for ownership check)
            
        Returns:
            API key or None if not found
        """
        result = await self.session.execute(
            select(APIKey).where(
                and_(
                    APIKey.id == key_id,
                    APIKey.user_id == user_id,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def revoke_key(self, key_id: UUID, user_id: UUID) -> APIKey:
        """
        Revoke an API key.
        
        Args:
            key_id: Key ID
            user_id: User ID (for ownership check)
            
        Returns:
            Revoked key
            
        Raises:
            NotFoundError: If key not found
        """
        key = await self.get_key(key_id, user_id)
        
        if not key:
            raise NotFoundError(f"API key not found: {key_id}")
        
        key.status = APIKeyStatus.REVOKED.value
        
        await self.session.commit()
        await self.session.refresh(key)
        
        self.log_operation(
            "revoke_api_key",
            user_id=str(user_id),
            key_id=str(key_id),
        )
        
        return key
    
    async def get_key_usage(
        self,
        key_id: UUID,
        user_id: UUID,
        days: int = 30,
    ) -> dict:
        """
        Get usage statistics for an API key.
        
        Args:
            key_id: Key ID
            user_id: User ID (for ownership check)
            days: Number of days to analyze
            
        Returns:
            Usage statistics dictionary
            
        Raises:
            NotFoundError: If key not found
        """
        key = await self.get_key(key_id, user_id)
        
        if not key:
            raise NotFoundError(f"API key not found: {key_id}")
        
        # Calculate average daily usage
        if key.created_at:
            days_since_creation = (datetime.utcnow() - key.created_at).days or 1
            avg_daily_usage = key.usage_count / days_since_creation
        else:
            avg_daily_usage = 0
        
        return {
            "key_id": str(key.id),
            "name": key.name,
            "total_usage": key.usage_count,
            "rate_limit": key.rate_limit,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "last_used_ip": key.last_used_ip,
            "average_daily_usage": round(avg_daily_usage, 2),
            "status": key.status,
            "created_at": key.created_at.isoformat() if key.created_at else None,
        }
