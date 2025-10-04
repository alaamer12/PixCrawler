"""
Authentication service for user authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from jose import JWTError, jwt
from passlib.context import CryptContext

from backend.core.config import get_settings
from backend.core.exceptions import AuthenticationError
from backend.models.user import TokenResponse
from .base import BaseService

__all__ = [
    'AuthService'
]


class AuthService(BaseService):
    """Service for handling authentication and authorization."""

    def __init__(self) -> None:
        super().__init__()
        self.settings = get_settings()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against its hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database

        Returns:
            True if password matches, False otherwise
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hash a plain password.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return self.pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT access token.

        Args:
            data: Token payload data

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            minutes=self.settings.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})

        return jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create a JWT refresh token.

        Args:
            data: Token payload data

        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=self.settings.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})

        return jwt.encode(
            to_encode,
            self.settings.secret_key,
            algorithm=self.settings.algorithm
        )

    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm]
            )

            if payload.get("type") != token_type:
                raise AuthenticationError("Invalid token type")

            return payload

        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

    def create_tokens(self, user_id: int, email: str) -> TokenResponse:
        """
        Create access and refresh tokens for a user.

        Args:
            user_id: User ID
            email: User email

        Returns:
            Token response with access and refresh tokens
        """
        token_data = {"sub": str(user_id), "email": email}

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )
