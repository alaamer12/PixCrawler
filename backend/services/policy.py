"""
Service for managing dataset lifecycle policies.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any

from backend.core.exceptions import NotFoundError, ValidationError
from backend.models.dataset import Dataset
from backend.models.policy import ArchivalPolicy, CleanupPolicy, PolicyExecutionLog
from backend.repositories.dataset_repository import DatasetRepository
from backend.repositories.policy_repository import (
    ArchivalPolicyRepository,
    CleanupPolicyRepository,
    PolicyExecutionLogRepository,
)
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyUpdate,
    StorageTier,
    CleanupTarget,
)
from .base import BaseService


class PolicyService(BaseService):
    """Service for managing policy definitions."""

    def __init__(
        self,
        archival_repo: ArchivalPolicyRepository,
        cleanup_repo: CleanupPolicyRepository,
        log_repo: PolicyExecutionLogRepository,
    ):
        super().__init__()
        self.archival_repo = archival_repo
        self.cleanup_repo = cleanup_repo
        self.log_repo = log_repo

    # --- Archival Policy Operations ---

    async def create_archival_policy(
        self, policy_data: ArchivalPolicyCreate
    ) -> ArchivalPolicy:
        """Create a new archival policy."""
        existing = await self.archival_repo.get_by_name(policy_data.name)
        if existing:
            raise ValidationError(f"Archival policy '{policy_data.name}' already exists")
        
        return await self.archival_repo.create(policy_data.model_dump())

    async def get_archival_policy(self, policy_id: int) -> ArchivalPolicy:
        """Get archival policy by ID."""
        policy = await self.archival_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Archival policy {policy_id} not found")
        return policy

    async def list_archival_policies(self) -> List[ArchivalPolicy]:
        """List all archival policies."""
        return await self.archival_repo.list()

    async def update_archival_policy(
        self, policy_id: int, policy_data: ArchivalPolicyUpdate
    ) -> ArchivalPolicy:
        """Update an archival policy."""
        policy = await self.get_archival_policy(policy_id)
        return await self.archival_repo.update(
            policy_id, policy_data.model_dump(exclude_unset=True)
        )

    async def delete_archival_policy(self, policy_id: int) -> None:
        """Delete an archival policy."""
        await self.get_archival_policy(policy_id)
        await self.archival_repo.delete(policy_id)

    # --- Cleanup Policy Operations ---

    async def create_cleanup_policy(
        self, policy_data: CleanupPolicyCreate
    ) -> CleanupPolicy:
        """Create a new cleanup policy."""
        existing = await self.cleanup_repo.get_by_name(policy_data.name)
        if existing:
            raise ValidationError(f"Cleanup policy '{policy_data.name}' already exists")
        
        return await self.cleanup_repo.create(policy_data.model_dump())

    async def get_cleanup_policy(self, policy_id: int) -> CleanupPolicy:
        """Get cleanup policy by ID."""
        policy = await self.cleanup_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Cleanup policy {policy_id} not found")
        return policy

    async def list_cleanup_policies(self) -> List[CleanupPolicy]:
        """List all cleanup policies."""
        return await self.cleanup_repo.list()

    async def update_cleanup_policy(
        self, policy_id: int, policy_data: CleanupPolicyUpdate
    ) -> CleanupPolicy:
        """Update a cleanup policy."""
        policy = await self.get_cleanup_policy(policy_id)
        return await self.cleanup_repo.update(
            policy_id, policy_data.model_dump(exclude_unset=True)
        )

    async def delete_cleanup_policy(self, policy_id: int) -> None:
        """Delete a cleanup policy."""
        await self.get_cleanup_policy(policy_id)
        await self.cleanup_repo.delete(policy_id)


class PolicyExecutionService(BaseService):
    """Service for executing policies against datasets."""

    def __init__(
        self,
        dataset_repo: DatasetRepository,
        archival_repo: ArchivalPolicyRepository,
        cleanup_repo: CleanupPolicyRepository,
        log_repo: PolicyExecutionLogRepository,
    ):
        super().__init__()
        self.dataset_repo = dataset_repo
        self.archival_repo = archival_repo
        self.cleanup_repo = cleanup_repo
        self.log_repo = log_repo

    async def execute_archival_policies(self) -> Dict[str, int]:
        """
        Execute all active archival policies.
        
        Returns:
            Summary of execution (e.g., {"processed": 10, "archived": 5})
        """
        policies = await self.archival_repo.get_active_policies()
        stats = {"processed": 0, "archived": 0, "errors": 0}

        for policy in policies:
            # Find candidate datasets
            # This is a simplified logic. In a real scenario, we might want to push this to the DB
            # via complex queries in the repository.
            datasets = await self.dataset_repo.list() # Potential performance bottleneck
            
            for dataset in datasets:
                try:
                    if await self._should_archive(dataset, policy):
                        await self._archive_dataset(dataset, policy)
                        stats["archived"] += 1
                    stats["processed"] += 1
                except Exception as e:
                    self.logger.error(f"Error executing archival policy {policy.id} on dataset {dataset.id}: {e}")
                    stats["errors"] += 1
                    await self._log_execution(
                        "archival", policy.id, dataset.id, "failed", {"error": str(e)}
                    )

        return stats

    async def execute_cleanup_policies(self) -> Dict[str, int]:
        """
        Execute all active cleanup policies.
        
        Returns:
            Summary of execution
        """
        policies = await self.cleanup_repo.get_active_policies()
        stats = {"processed": 0, "cleaned": 0, "errors": 0}

        for policy in policies:
            datasets = await self.dataset_repo.list()
            
            for dataset in datasets:
                try:
                    if await self._should_cleanup(dataset, policy):
                        await self._cleanup_dataset(dataset, policy)
                        stats["cleaned"] += 1
                    stats["processed"] += 1
                except Exception as e:
                    self.logger.error(f"Error executing cleanup policy {policy.id} on dataset {dataset.id}: {e}")
                    stats["errors"] += 1
                    await self._log_execution(
                        "cleanup", policy.id, dataset.id, "failed", {"error": str(e)}
                    )

        return stats

    async def _should_archive(self, dataset: Dataset, policy: ArchivalPolicy) -> bool:
        """Check if dataset matches archival policy criteria."""
        # Check storage tier
        if dataset.storage_tier == policy.target_tier:
            return False
            
        # Check age/access
        cutoff_date = datetime.now(dataset.last_accessed_at.tzinfo) - timedelta(days=policy.days_until_archive)
        
        # Use last_accessed_at if available, otherwise created_at
        reference_date = dataset.last_accessed_at or dataset.created_at
        
        if reference_date > cutoff_date:
            return False
            
        # Check filter criteria (simplified)
        if policy.filter_criteria:
            # Implement specific filtering logic here if needed
            pass
            
        return True

    async def _archive_dataset(self, dataset: Dataset, policy: ArchivalPolicy) -> None:
        """Perform archival action by moving dataset to target storage tier."""
        from backend.storage.factory import get_storage_provider
        from backend.storage.azure_blob_archive import AccessTier
        
        try:
            # Get storage provider
            storage = get_storage_provider()
            
            # Check if storage supports tiering (Azure Blob Archive)
            if hasattr(storage, 'set_blob_tier'):
                # Map policy tier to Azure tier
                tier_mapping = {
                    StorageTier.HOT: AccessTier.HOT,
                    StorageTier.COOL: AccessTier.COOL,
                    StorageTier.ARCHIVE: AccessTier.ARCHIVE
                }
                
                target_tier = tier_mapping.get(policy.target_tier)
                if target_tier:
                    # Get dataset file path in storage
                    # Assuming dataset files are stored as: datasets/{dataset_id}/dataset.zip
                    blob_name = f"datasets/{dataset.id}/dataset.zip"
                    
                    # Change blob tier
                    result = storage.set_blob_tier(blob_name, target_tier)
                    
                    self.log_operation(
                        "archive_dataset_storage_tier_changed",
                        dataset_id=dataset.id,
                        target_tier=policy.target_tier,
                        result=result
                    )
            else:
                # Storage provider doesn't support tiering (e.g., local storage)
                self.log_operation(
                    "archive_dataset_storage_tier_not_supported",
                    dataset_id=dataset.id,
                    storage_type=type(storage).__name__
                )
            
            # Update database to reflect archival status
            await self.dataset_repo.update(
                dataset.id,
                {
                    "storage_tier": policy.target_tier,
                    "archived_at": datetime.now(dataset.created_at.tzinfo)
                }
            )
            
            await self._log_execution(
                "archival", 
                policy.id, 
                dataset.id, 
                "success", 
                {
                    "target_tier": policy.target_tier,
                    "storage_tier_changed": hasattr(storage, 'set_blob_tier')
                }
            )
            
        except Exception as e:
            self.log_operation(
                "archive_dataset_failed",
                dataset_id=dataset.id,
                error=str(e)
            )
            await self._log_execution(
                "archival",
                policy.id,
                dataset.id,
                "failed",
                {"error": str(e)}
            )
            raise

    async def _should_cleanup(self, dataset: Dataset, policy: CleanupPolicy) -> bool:
        """Check if dataset matches cleanup policy criteria."""
        cutoff_date = datetime.now(dataset.created_at.tzinfo) - timedelta(days=policy.days_until_cleanup)
        
        if dataset.created_at > cutoff_date:
            return False
            
        # Check status for specific targets
        if policy.cleanup_target == CleanupTarget.FAILED_JOBS:
            if dataset.status != "failed":
                return False
                
        return True

    async def _cleanup_dataset(self, dataset: Dataset, policy: CleanupPolicy) -> None:
        """Perform cleanup action."""
        details = {}
        
        if policy.cleanup_target == CleanupTarget.FULL_DATASET:
            # Delete dataset completely
            await self.dataset_repo.delete(dataset.id)
            details["action"] = "deleted_dataset"
            
        elif policy.cleanup_target == CleanupTarget.TEMP_FILES:
            # Clean temporary files from storage
            from backend.storage.factory import get_storage_provider
            
            try:
                storage = get_storage_provider()
                
                # List and delete temp files for this dataset
                # Temp files are typically stored as: datasets/{dataset_id}/temp/*
                temp_prefix = f"datasets/{dataset.id}/temp/"
                
                if hasattr(storage, 'list_files'):
                    temp_files = storage.list_files(prefix=temp_prefix)
                    
                    deleted_count = 0
                    for temp_file in temp_files:
                        try:
                            storage.delete(temp_file)
                            deleted_count += 1
                        except Exception as e:
                            self.log_operation(
                                "cleanup_temp_file_failed",
                                dataset_id=dataset.id,
                                file=temp_file,
                                error=str(e)
                            )
                    
                    details["action"] = "cleaned_temp_files"
                    details["files_deleted"] = deleted_count
                    
                    self.log_operation(
                        "cleanup_temp_files_completed",
                        dataset_id=dataset.id,
                        files_deleted=deleted_count
                    )
                else:
                    details["action"] = "temp_cleanup_not_supported"
                    details["storage_type"] = type(storage).__name__
                    
            except Exception as e:
                self.log_operation(
                    "cleanup_temp_files_failed",
                    dataset_id=dataset.id,
                    error=str(e)
                )
                details["action"] = "cleanup_failed"
                details["error"] = str(e)
            
        elif policy.cleanup_target == CleanupTarget.FAILED_JOBS:
            # Delete failed dataset
            await self.dataset_repo.delete(dataset.id)
            details["action"] = "deleted_failed_job"
            
        await self._log_execution(
            "cleanup", 
            policy.id, 
            dataset.id if policy.cleanup_target != CleanupTarget.FULL_DATASET else None, 
            "success", 
            details
        )

    async def _log_execution(
        self, 
        policy_type: str, 
        policy_id: int, 
        dataset_id: Optional[int], 
        status: str, 
        details: dict
    ) -> None:
        """Log policy execution."""
        await self.log_repo.create({
            "policy_type": policy_type,
            "policy_id": policy_id,
            "dataset_id": dataset_id,
            "status": status,
            "details": details,
            "executed_at": datetime.now()
        })
