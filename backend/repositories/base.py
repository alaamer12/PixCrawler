"""
Base repository class with common database operations.

This module provides the abstract base repository class that all
repository implementations should extend. It defines the standard
CRUD interface and ensures consistent data access patterns across
the application.

Classes:
    BaseRepository: Abstract base class for all repositories

Features:
    - Generic type support for type-safe operations
    - Standard CRUD operations (Create, Read, Update, Delete)
    - Async/await support for non-blocking database operations
    - Automatic session management and transaction handling
"""

from abc import ABC
from typing import Any, Generic, TypeVar, Optional

from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class BaseRepository(ABC, Generic[ModelT]):
    """
    Abstract base repository class with common CRUD operations.

    This class provides the foundation for all repository implementations
    in the application. It defines standard database operations that work
    with SQLAlchemy models and async sessions.

    Type Parameters:
        ModelT: The SQLAlchemy model type this repository manages

    Attributes:
        session: Async database session for executing queries
        model: SQLAlchemy model class this repository operates on

    Example:
        >>> class UserRepository(BaseRepository[User]):
        ...     def __init__(self, session: AsyncSession):
        ...         super().__init__(session, User)
        ...
        >>> repo = UserRepository(session)
        >>> user = await repo.create(email="user@example.com", name="John")
        >>> user = await repo.get_by_id(1)
        >>> user = await repo.update(user, name="Jane")
        >>> await repo.delete(user)
    """

    def __init__(self, session: AsyncSession, model: type[ModelT]) -> None:
        """
        Initialize the repository with a database session and model.

        Args:
            session: Async SQLAlchemy session for database operations
            model: SQLAlchemy model class this repository will manage
        """
        self.session = session
        self.model = model

    async def create(self, **kwargs: Any) -> ModelT:
        """
        Create a new record in the database.

        Creates a new instance of the model with the provided keyword
        arguments, adds it to the session, commits the transaction,
        and returns the created instance with all database-generated
        fields populated.

        Args:
            **kwargs: Field names and values for the new record

        Returns:
            The created model instance with all fields populated

        Raises:
            IntegrityError: If unique constraints are violated
            DataError: If data types are invalid

        Example:
            >>> user = await repo.create(
            ...     email="user@example.com",
            ...     name="John Doe",
            ...     is_active=True
            ... )
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def get_by_id(self, id: int) -> Optional[ModelT]:
        """
        Retrieve a record by its primary key ID.

        Fetches a single record from the database using the primary key.
        This is the most efficient way to retrieve a single record.

        Args:
            id: Primary key value of the record to retrieve

        Returns:
            The model instance if found, None otherwise

        Example:
            >>> user = await repo.get_by_id(1)
            >>> if user:
            ...     print(f"Found user: {user.email}")
            ... else:
            ...     print("User not found")
        """
        return await self.session.get(self.model, id)

    async def update(self, instance: ModelT, **kwargs: Any) -> ModelT:
        """
        Update an existing record with new values.

        Updates the provided instance with the given keyword arguments,
        commits the transaction, and returns the updated instance with
        all fields refreshed from the database.

        Args:
            instance: The model instance to update
            **kwargs: Field names and new values to update

        Returns:
            The updated model instance with all fields refreshed

        Raises:
            IntegrityError: If unique constraints are violated
            DataError: If data types are invalid

        Example:
            >>> user = await repo.get_by_id(1)
            >>> user = await repo.update(
            ...     user,
            ...     name="Jane Doe",
            ...     is_active=False
            ... )
        """
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelT) -> None:
        """
        Delete a record from the database.

        Removes the provided instance from the database and commits
        the transaction. This operation is permanent and cannot be undone.

        Args:
            instance: The model instance to delete

        Raises:
            IntegrityError: If foreign key constraints prevent deletion

        Example:
            >>> user = await repo.get_by_id(1)
            >>> await repo.delete(user)
        """
        await self.session.delete(instance)
        await self.session.commit()
