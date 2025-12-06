"""
Unit tests for PolicyService and PolicyExecutionService.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from backend.core.exceptions import ValidationError, NotFoundError
from backend.models.dataset import Dataset
from backend.models.policy import ArchivalPolicy, CleanupPolicy, PolicyExecutionLog
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyUpdate,
    StorageTier,
    CleanupTarget,
)
from backend.services.policy import PolicyService, PolicyExecutionService


@pytest.fixture
def mock_archival_repo():
    return AsyncMock()


@pytest.fixture
def mock_cleanup_repo():
    return AsyncMock()


@pytest.fixture
def mock_log_repo():
    return AsyncMock()


@pytest.fixture
def mock_dataset_repo():
    return AsyncMock()


@pytest.fixture
def policy_service(mock_archival_repo, mock_cleanup_repo, mock_log_repo):
    return PolicyService(mock_archival_repo, mock_cleanup_repo, mock_log_repo)


@pytest.fixture
def execution_service(mock_dataset_repo, mock_archival_repo, mock_cleanup_repo, mock_log_repo):
    return PolicyExecutionService(
        mock_dataset_repo, mock_archival_repo, mock_cleanup_repo, mock_log_repo
    )


# --- PolicyService Tests ---

@pytest.mark.asyncio
async def test_create_archival_policy(policy_service, mock_archival_repo):
    mock_archival_repo.get_by_name.return_value = None
    mock_archival_repo.create.return_value = ArchivalPolicy(id=1, name="Test")
    
    policy_in = ArchivalPolicyCreate(
        name="Test",
        days_until_archive=30,
        target_tier=StorageTier.COLD
    )
    
    result = await policy_service.create_archival_policy(policy_in)
    assert result.id == 1
    mock_archival_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_archival_policy_duplicate(policy_service, mock_archival_repo):
    mock_archival_repo.get_by_name.return_value = ArchivalPolicy(id=1, name="Test")
    
    policy_in = ArchivalPolicyCreate(
        name="Test",
        days_until_archive=30,
        target_tier=StorageTier.COLD
    )
    
    with pytest.raises(ValidationError):
        await policy_service.create_archival_policy(policy_in)


@pytest.mark.asyncio
async def test_create_cleanup_policy(policy_service, mock_cleanup_repo):
    mock_cleanup_repo.get_by_name.return_value = None
    mock_cleanup_repo.create.return_value = CleanupPolicy(id=1, name="Test")
    
    policy_in = CleanupPolicyCreate(
        name="Test",
        days_until_cleanup=30,
        cleanup_target=CleanupTarget.TEMP_FILES
    )
    
    result = await policy_service.create_cleanup_policy(policy_in)
    assert result.id == 1
    mock_cleanup_repo.create.assert_called_once()


# --- PolicyExecutionService Tests ---

@pytest.mark.asyncio
async def test_execute_archival_policies(
    execution_service, 
    mock_dataset_repo, 
    mock_archival_repo,
    mock_log_repo
):
    # Setup policy
    policy = ArchivalPolicy(
        id=1,
        name="Archive Old",
        days_until_archive=30,
        target_tier="cold",
        is_active=True
    )
    mock_archival_repo.get_active_policies.return_value = [policy]
    
    # Setup datasets
    old_dataset = Dataset(
        id=1,
        created_at=datetime.now() - timedelta(days=40),
        last_accessed_at=datetime.now() - timedelta(days=40),
        storage_tier="hot"
    )
    new_dataset = Dataset(
        id=2,
        created_at=datetime.now(),
        last_accessed_at=datetime.now(),
        storage_tier="hot"
    )
    mock_dataset_repo.list.return_value = [old_dataset, new_dataset]
    
    # Execute
    stats = await execution_service.execute_archival_policies()
    
    assert stats["processed"] == 2
    assert stats["archived"] == 1
    
    # Verify update called for old dataset
    mock_dataset_repo.update.assert_called_once()
    call_args = mock_dataset_repo.update.call_args
    assert call_args[0][0] == 1  # dataset_id
    assert call_args[0][1]["storage_tier"] == "cold"
    
    # Verify log created
    mock_log_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_execute_cleanup_policies(
    execution_service, 
    mock_dataset_repo, 
    mock_cleanup_repo,
    mock_log_repo
):
    # Setup policy
    policy = CleanupPolicy(
        id=1,
        name="Cleanup Failed",
        days_until_cleanup=7,
        cleanup_target="failed_jobs",
        is_active=True
    )
    mock_cleanup_repo.get_active_policies.return_value = [policy]
    
    # Setup datasets
    old_failed_dataset = Dataset(
        id=1,
        created_at=datetime.now() - timedelta(days=10),
        status="failed"
    )
    new_failed_dataset = Dataset(
        id=2,
        created_at=datetime.now(),
        status="failed"
    )
    old_success_dataset = Dataset(
        id=3,
        created_at=datetime.now() - timedelta(days=10),
        status="completed"
    )
    
    mock_dataset_repo.list.return_value = [
        old_failed_dataset, 
        new_failed_dataset, 
        old_success_dataset
    ]
    
    # Execute
    stats = await execution_service.execute_cleanup_policies()
    
    assert stats["processed"] == 3
    assert stats["cleaned"] == 1
    
    # Verify delete called for old failed dataset
    mock_dataset_repo.delete.assert_called_once_with(1)
    
    # Verify log created
    mock_log_repo.create.assert_called_once()
