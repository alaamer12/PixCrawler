"""
API token generation endpoints.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel

from backend.api.dependencies import get_current_user
from backend.database.connection import get_session
from utility.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/tokens",
    tags=["API Tokens"],
)

class TokenResponse(BaseModel):
    """Response for token generation."""
    token: str
    token_type: str = "service"
    expires_at: str
    created_at: str

def generate_service_token() -> str:
    """Generate a secure service token."""
    # Generate 32 bytes of random data and encode as hex
    token_bytes = secrets.token_bytes(32)
    token = f"pk_live_{token_bytes.hex()}"
    return token

@router.post(
    "/generate",
    response_model=TokenResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Generate API Token",
    description="Generate a new API token for SDK access",
)
async def generate_token() -> TokenResponse:
    """Generate a new API token for the current user."""
    
    try:
        # Generate secure token
        token = generate_service_token()
        
        # Set expiration (1 year from now)
        expires_at = datetime.utcnow() + timedelta(days=365)
        created_at = datetime.utcnow()
        
        # TODO: Store token in database with user association
        # For now, just return the token
        
        logger.info(f"Generated API token for demo user")
        
        return TokenResponse(
            token=token,
            expires_at=expires_at.isoformat(),
            created_at=created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate API token"
        )

@router.get(
    "/current",
    response_model=TokenResponse,
    summary="Get Current Token",
    description="Get the current API token for the user",
)
async def get_current_token() -> TokenResponse:
    """Get the current API token for the user."""
    
    try:
        # TODO: Fetch from database
        # For now, generate a demo token
        token = generate_service_token()
        created_at = datetime.utcnow()
        expires_at = created_at + timedelta(days=365)
        
        return TokenResponse(
            token=token,
            expires_at=expires_at.isoformat(),
            created_at=created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to get current token: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get API token"
        )