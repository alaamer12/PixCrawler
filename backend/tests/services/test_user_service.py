"""
Unit tests for UserService.

Tests business logic for user management including creation,
retrieval, updates, and deletion.
"""

import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from datetime import datetime

from backend.core.exceptions import NotFoundError, ValidationError, ExternalServiceError
from backend.models import Profile
from backend.services.user import UserService


@pytest.fixture
def mock_user_repo():
    """Create mock user repository."""
    return AsyncMock()


@pytest.fixture
def user_service(mock_user_repo):
    """Create user service with mocked repository."""
    return UserService(mock_user_repo)


@pytest.fixture
def sample_user():
    """Create sample user for testing."""
    user = Profile(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        role="user"
    )
    user.created_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    return user


# ============================================================================
# CREATE USER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_create_user_success(user_service, mock_user_repo, sample_user):
    """Test successful user creation."""
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.create.return_value = sample_user
    
    result = await user_service.create_user(
        email="test@example.com",
        full_name="Test User",
        role="user"
    )
    
    assert result["email"] == "test@example.com"
    assert result["full_name"] == "Test User"
    mock_user_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_email(user_service, mock_user_repo, sample_user):
    """Test user creation with duplicate email."""
    mock_user_repo.get_by_email.return_value = sample_user
    
    with pytest.raises(ValidationError) as exc:
        await user_service.create_user(email="test@example.com")
    
    assert "already registered" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_create_user_empty_email(user_service, mock_user_repo):
    """Test user creation with empty email."""
    with pytest.raises(ValidationError) as exc:
        await user_service.create_user(email="")
    
    assert "required" in str(exc.value).lower()


# ============================================================================
# GET USER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_get_user_by_id_success(user_service, mock_user_repo, sample_user):
    """Test successful user retrieval by ID."""
    mock_user_repo.get_by_uuid.return_value = sample_user
    
    result = await user_service.get_user_by_id(sample_user.id)
    
    assert result["id"] == str(sample_user.id)
    assert result["email"] == sample_user.email
    mock_user_repo.get_by_uuid.assert_called_once_with(sample_user.id)


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(user_service, mock_user_repo):
    """Test user retrieval when user doesn't exist."""
    user_id = uuid4()
    mock_user_repo.get_by_uuid.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await user_service.get_user_by_id(user_id)
    
    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_get_user_by_email_success(user_service, mock_user_repo, sample_user):
    """Test successful user retrieval by email."""
    mock_user_repo.get_by_email.return_value = sample_user
    
    result = await user_service.get_user_by_email("test@example.com")
    
    assert result["email"] == "test@example.com"
    mock_user_repo.get_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_get_user_by_email_not_found(user_service, mock_user_repo):
    """Test user retrieval by email when user doesn't exist."""
    mock_user_repo.get_by_email.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await user_service.get_user_by_email("nonexistent@example.com")
    
    assert "not found" in str(exc.value).lower()


# ============================================================================
# LIST USERS TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_list_users(user_service, mock_user_repo):
    """Test listing users with pagination."""
    mock_users = []
    for i in range(5):
        user = Profile(
            id=uuid4(),
            email=f"user{i}@example.com",
            full_name=f"User {i}",
            role="user"
        )
        user.created_at = datetime.utcnow()
        mock_users.append(user)
    
    mock_user_repo.list_users.return_value = mock_users
    
    result = await user_service.list_users(skip=0, limit=10)
    
    assert len(result) == 5
    assert all("email" in user for user in result)
    mock_user_repo.list_users.assert_called_once_with(offset=0, limit=10)


# ============================================================================
# UPDATE USER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_update_user_success(user_service, mock_user_repo, sample_user):
    """Test successful user update."""
    updated_user = Profile(
        id=sample_user.id,
        email=sample_user.email,
        full_name="Updated Name",
        role=sample_user.role
    )
    updated_user.created_at = sample_user.created_at
    updated_user.updated_at = datetime.utcnow()
    
    mock_user_repo.get_by_uuid.return_value = sample_user
    mock_user_repo.get_by_email.return_value = None
    mock_user_repo.update.return_value = updated_user
    
    result = await user_service.update_user(
        user_id=sample_user.id,
        full_name="Updated Name"
    )
    
    assert result["full_name"] == "Updated Name"
    mock_user_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_user_not_found(user_service, mock_user_repo):
    """Test update when user doesn't exist."""
    user_id = uuid4()
    mock_user_repo.get_by_uuid.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await user_service.update_user(user_id=user_id, full_name="New Name")
    
    assert "not found" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_update_user_duplicate_email(user_service, mock_user_repo, sample_user):
    """Test update with email that's already in use."""
    other_user = Profile(
        id=uuid4(),
        email="other@example.com",
        full_name="Other User",
        role="user"
    )
    
    mock_user_repo.get_by_uuid.return_value = sample_user
    mock_user_repo.get_by_email.return_value = other_user
    
    with pytest.raises(ValidationError) as exc:
        await user_service.update_user(
            user_id=sample_user.id,
            email="other@example.com"
        )
    
    assert "already in use" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_update_user_same_email(user_service, mock_user_repo, sample_user):
    """Test update with same email (should succeed)."""
    updated_user = Profile(
        id=sample_user.id,
        email=sample_user.email,
        full_name="Updated Name",
        role=sample_user.role
    )
    updated_user.created_at = sample_user.created_at
    updated_user.updated_at = datetime.utcnow()
    
    mock_user_repo.get_by_uuid.return_value = sample_user
    mock_user_repo.update.return_value = updated_user
    
    result = await user_service.update_user(
        user_id=sample_user.id,
        email=sample_user.email,
        full_name="Updated Name"
    )
    
    assert result["full_name"] == "Updated Name"


# ============================================================================
# DELETE USER TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_delete_user_success(user_service, mock_user_repo, sample_user):
    """Test successful user deletion."""
    mock_user_repo.get_by_uuid.return_value = sample_user
    mock_user_repo.delete.return_value = True
    
    result = await user_service.delete_user(str(sample_user.id))
    
    assert result is True
    mock_user_repo.delete.assert_called_once_with(sample_user)


@pytest.mark.asyncio
async def test_delete_user_not_found(user_service, mock_user_repo):
    """Test delete when user doesn't exist."""
    user_id = str(uuid4())
    mock_user_repo.get_by_uuid.return_value = None
    
    with pytest.raises(NotFoundError) as exc:
        await user_service.delete_user(user_id)
    
    assert "not found" in str(exc.value).lower()
