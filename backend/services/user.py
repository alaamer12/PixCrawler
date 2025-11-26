"""
User service for user management operations.
"""
from typing import Optional, List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
from backend.repositories import UserRepository
from .base import BaseService


class UserService(BaseService):
    """Service for handling user operations."""

    def __init__(self, user_repository: UserRepository, session: Optional[AsyncSession] = None) -> None:
        """
        Initialize user service with required repositories.

        Args:
            user_repository: User repository instance
            session: Optional database session (for backward compatibility)
        """
        super().__init__()
        self._repository = user_repository
        self._session = session
        
    @property
    def repository(self) -> UserRepository:
        """Get user repository."""
        return self._repository

    async def create_user(self, email: str, full_name: Optional[str] = None, role: str = "user") -> dict:
        """
        Create a new user.

        Args:
            email: User email
            full_name: User full name
            role: User role

        Returns:
            Created user information

        Raises:
            ValidationError: If user data is invalid
            ExternalServiceError: If creation fails
        """
        self.log_operation("create_user", email=email)

        if not email:
            raise ValidationError("Email is required")

        async with self.repository.get_session() as session:
            try:
                async with session.begin():
                    existing_user = await self.repository.get_by_email(email, session=session)
                    if existing_user:
                        raise ValidationError(f"Email already registered: {email}")

                    user = await self.repository.create(
                        email=email,
                        full_name=full_name,
                        role=role,
                        session=session
                    )
                    
                    return {
                        "id": str(user.id),
                        "email": user.email,
                        "full_name": user.full_name,
                        "role": user.role,
                        "created_at": user.created_at.isoformat()
                    }
                    
            except ValidationError:
                raise
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to create user: {str(e)}")
                raise ExternalServiceError("Failed to create user") from e

    async def get_user_by_id(self, user_id: UUID) -> dict:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User information

        Raises:
            NotFoundError: If user not found
        """
        self.log_operation("get_user_by_id", user_id=user_id)

        user = await self.repository.get_by_uuid(user_id)
        if not user:
            raise NotFoundError(f"User not found: {user_id}")

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }

    async def get_user_by_email(self, email: str) -> dict:
        """
        Get user by email.

        Args:
            email: User email

        Returns:
            User information

        Raises:
            NotFoundError: If user not found
        """
        self.log_operation("get_user_by_email", email=email)

        user = await self.repository.get_by_email(email)
        if not user:
            raise NotFoundError(f"User not found with email: {email}")

        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "created_at": user.created_at.isoformat(),
            "updated_at": user.updated_at.isoformat()
        }



    async def list_users(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """
        List users with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of users
        """
        self.log_operation("list_users", skip=skip, limit=limit)

        users = await self.repository.list_users(offset=skip, limit=limit)
        return [
            {
                "id": str(u.id),
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "created_at": u.created_at.isoformat() if hasattr(u, 'created_at') else None
            }
            for u in users
        ]
        
    async def update_user(
        self,
        user_id: UUID,
        email: Optional[str] = None,
        full_name: Optional[str] = None,
        role: Optional[str] = None
    ) -> dict:
        """
        Update user information.

        Args:
            user_id: ID of the user to update
            email: New email (optional)
            full_name: New full name (optional)
            role: New role (optional)

        Returns:
            Updated user information

        Raises:
            NotFoundError: If user not found
            ValidationError: If update data is invalid
            ExternalServiceError: If update fails
        """
        self.log_operation("update_user", user_id=user_id, email=email, full_name=full_name, role=role)

        async with self.repository.get_session() as session:
            try:
                async with session.begin():
                    user = await self.repository.get_by_uuid(user_id, session=session)
                    if not user:
                        raise NotFoundError(f"User not found: {user_id}")
                        
                    if email and email != user.email:
                        existing_user = await self.repository.get_by_email(email, session=session)
                        if existing_user and existing_user.id != user_id:
                            raise ValidationError(f"Email already in use: {email}")

                    updated_user = await self.repository.update(
                        user_id=user_id,
                        email=email,
                        full_name=full_name,
                        role=role,
                        session=session
                    )
                    
                    return {
                        "id": str(updated_user.id),
                        "email": updated_user.email,
                        "full_name": updated_user.full_name,
                        "role": updated_user.role,
                        "created_at": updated_user.created_at.isoformat(),
                        "updated_at": updated_user.updated_at.isoformat()
                    }
                    
            except (NotFoundError, ValidationError) as e:
                self.logger.error(f"Validation error updating user {user_id}: {str(e)}")
                raise
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Failed to update user {user_id}: {str(e)}")
                raise ExternalServiceError("Failed to update user") from e
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete a user by ID.

        Args:
            user_id: User ID

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If user not found
            ExternalServiceError: If deletion fails
        """
        self.log_operation("delete_user", user_id=user_id)

        try:
            async with self.repository.get_session() as session:
                try:
                    async with session.begin():
                        # Verify user exists
                        user = await self.repository.get_by_uuid(user_id, session=session)
                        if not user:
                            self.logger.warning(f"User not found during deletion: {user_id}")
                            raise NotFoundError(f"User not found: {user_id}")
                        
                        # Delete user
                        try:
                            await self.repository.delete(user, session=session)
                            return True
                        except Exception as e:
                            self.logger.error(f"Repository error deleting user {user_id}: {str(e)}")
                            raise ExternalServiceError("Failed to delete user due to a database error") from e
                            
                except Exception as e:
                    if not isinstance(e, (NotFoundError, ExternalServiceError)):
                        self.logger.error(f"Unexpected error in user deletion transaction: {str(e)}")
                        raise ExternalServiceError("Failed to complete user deletion") from e
                    raise
                    
        except Exception as e:
            if not isinstance(e, (NotFoundError, ExternalServiceError)):
                self.logger.error(f"Failed to establish database session for user deletion: {str(e)}")
                raise ExternalServiceError("Failed to process user deletion") from e
            raise