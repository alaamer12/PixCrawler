"""
Policy service for dataset lifecycle management.

This module provides business logic for archival and cleanup policies
that control dataset lifecycle transitions.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from backend.core.exceptions import NotFoundError, ValidationError
from backend.repositories.policy_repository import (
    ArchivalPolicyRepository,
    CleanupPolicyRepository,
    PolicyExecutionLogRepository
)
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyUpdate
)
from backend.models.policy import ArchivalPolicy, CleanupPolicy, PolicyExecutionLog
from .base import BaseService

__all__ = ['PolicyService']


class PolicyService(BaseService):
    """
    Service for policy business logic.
    
    Handles policy creation, updates, retrieval, and execution
    for dataset lifecycle management.
    """

    def __init__(
        self,
        archival_repo: ArchivalPolicyRepository,
        cleanup_repo: CleanupPolicyRepository,
        execution_log_repo: PolicyExecutionLogRepository
    ) -> None:
        """
        Initialize policy service with repositories.
        
        Args:
            archival_repo: Archival policy repository
            cleanup_repo: Cleanup policy repository
            execution_log_repo: Execution log repository
        """
        super().__init__()
        self.archival_repo = archival_repo
        self.cleanup_repo = cleanup_repo
        self.execution_log_repo = execution_log_repo

    async def create_archival_policy(
        self,
        policy_in: ArchivalPolicyCreate
    ) -> ArchivalPolicy:
        """
        Create a new archival policy.
        
        Args:
            policy_in: Policy creation data
            
        Returns:
            Created archival policy
            
        Raises:
            ValidationError: If policy data is invalid or name already exists
        """
        self.log_operation("create_archival_policy", name=policy_in.name)
        
        # Check for duplicate name
        existing = await self.archival_repo.get_by_name(policy_in.name)
        if existing:
            raise ValidationError(f"Policy with name '{policy_in.name}' already exists")
        
        # Create policy
        policy_data = policy_in.model_dump()
        return await self.archival_repo.create(**policy_data)

    async def get_archival_policy(self, policy_id: int) -> ArchivalPolicy:
        """
        Get archival policy by ID.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            Archival policy
            
        Raises:
            NotFoundError: If policy not found
        """
        policy = await self.archival_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Archival policy {policy_id} not found")
        return policy

    async def list_archival_policies(
        self,
        active_only: bool = False
    ) -> List[ArchivalPolicy]:
        """
        List archival policies.
        
        Args:
            active_only: If True, only return active policies
            
        Returns:
            List of archival policies
        """
        if active_only:
            return list(await self.archival_repo.get_active_policies())
        
        # Get all policies - would need to implement in repository
        # For now, just return active policies
        return list(await self.archival_repo.get_active_policies())

    async def update_archival_policy(
        self,
        policy_id: int,
        policy_update: ArchivalPolicyUpdate
    ) -> ArchivalPolicy:
        """
        Update archival policy.
        
        Args:
            policy_id: Policy ID
            policy_update: Update data
            
        Returns:
            Updated archival policy
            
        Raises:
            NotFoundError: If policy not found
            ValidationError: If name already exists
        """
        self.log_operation("update_archival_policy", policy_id=policy_id)
        
        # Get existing policy
        policy = await self.archival_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Archival policy {policy_id} not found")
        
        # Check for duplicate name if name is being updated
        update_data = policy_update.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != policy.name:
            existing = await self.archival_repo.get_by_name(update_data["name"])
            if existing:
                raise ValidationError(f"Policy with name '{update_data['name']}' already exists")
        
        # Update policy
        return await self.archival_repo.update(policy, **update_data)

    async def delete_archival_policy(self, policy_id: int) -> None:
        """
        Delete archival policy.
        
        Args:
            policy_id: Policy ID
            
        Raises:
            NotFoundError: If policy not found
        """
        self.log_operation("delete_archival_policy", policy_id=policy_id)
        
        policy = await self.archival_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Archival policy {policy_id} not found")
        
        await self.archival_repo.delete(policy)

    async def create_cleanup_policy(
        self,
        policy_in: CleanupPolicyCreate
    ) -> CleanupPolicy:
        """
        Create a new cleanup policy.
        
        Args:
            policy_in: Policy creation data
            
        Returns:
            Created cleanup policy
            
        Raises:
            ValidationError: If policy data is invalid or name already exists
        """
        self.log_operation("create_cleanup_policy", name=policy_in.name)
        
        # Check for duplicate name
        existing = await self.cleanup_repo.get_by_name(policy_in.name)
        if existing:
            raise ValidationError(f"Policy with name '{policy_in.name}' already exists")
        
        # Create policy
        policy_data = policy_in.model_dump()
        return await self.cleanup_repo.create(**policy_data)

    async def get_cleanup_policy(self, policy_id: int) -> CleanupPolicy:
        """
        Get cleanup policy by ID.
        
        Args:
            policy_id: Policy ID
            
        Returns:
            Cleanup policy
            
        Raises:
            NotFoundError: If policy not found
        """
        policy = await self.cleanup_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Cleanup policy {policy_id} not found")
        return policy

    async def list_cleanup_policies(
        self,
        active_only: bool = False
    ) -> List[CleanupPolicy]:
        """
        List cleanup policies.
        
        Args:
            active_only: If True, only return active policies
            
        Returns:
            List of cleanup policies
        """
        if active_only:
            return list(await self.cleanup_repo.get_active_policies())
        
        # Get all policies - would need to implement in repository
        # For now, just return active policies
        return list(await self.cleanup_repo.get_active_policies())

    async def update_cleanup_policy(
        self,
        policy_id: int,
        policy_update: CleanupPolicyUpdate
    ) -> CleanupPolicy:
        """
        Update cleanup policy.
        
        Args:
            policy_id: Policy ID
            policy_update: Update data
            
        Returns:
            Updated cleanup policy
            
        Raises:
            NotFoundError: If policy not found
            ValidationError: If name already exists
        """
        self.log_operation("update_cleanup_policy", policy_id=policy_id)
        
        # Get existing policy
        policy = await self.cleanup_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Cleanup policy {policy_id} not found")
        
        # Check for duplicate name if name is being updated
        update_data = policy_update.model_dump(exclude_unset=True)
        if "name" in update_data and update_data["name"] != policy.name:
            existing = await self.cleanup_repo.get_by_name(update_data["name"])
            if existing:
                raise ValidationError(f"Policy with name '{update_data['name']}' already exists")
        
        # Update policy
        return await self.cleanup_repo.update(policy, **update_data)

    async def delete_cleanup_policy(self, policy_id: int) -> None:
        """
        Delete cleanup policy.
        
        Args:
            policy_id: Policy ID
            
        Raises:
            NotFoundError: If policy not found
        """
        self.log_operation("delete_cleanup_policy", policy_id=policy_id)
        
        policy = await self.cleanup_repo.get_by_id(policy_id)
        if not policy:
            raise NotFoundError(f"Cleanup policy {policy_id} not found")
        
        await self.cleanup_repo.delete(policy)

    async def execute_archival_policies(self) -> Dict[str, Any]:
        """
        Execute all active archival policies.
        
        This method identifies datasets that match archival policy criteria
        and triggers archival operations.
        
        Returns:
            Execution summary with counts and details
        """
        self.log_operation("execute_archival_policies")
        
        # Get active policies
        policies = await self.archival_repo.get_active_policies()
        
        summary = {
            "policies_executed": 0,
            "datasets_archived": 0,
            "errors": [],
            "executed_at": datetime.utcnow().isoformat()
        }
        
        for policy in policies:
            try:
                # Log policy execution start
                self.logger.info(f"Executing archival policy: {policy.name}")
                
                # TODO: Implement actual archival logic
                # This would involve:
                # 1. Query datasets matching policy criteria
                # 2. Check if datasets meet age/access requirements
                # 3. Trigger archival to target tier
                # 4. Log execution results
                
                # For now, just log the execution
                await self.execution_log_repo.create(
                    policy_type="archival",
                    policy_id=policy.id,
                    dataset_id=None,
                    status="success",
                    details={"message": "Policy execution placeholder"}
                )
                
                summary["policies_executed"] += 1
                
            except Exception as e:
                self.logger.error(f"Error executing policy {policy.name}: {e}")
                summary["errors"].append({
                    "policy_id": policy.id,
                    "policy_name": policy.name,
                    "error": str(e)
                })
        
        return summary

    async def execute_cleanup_policies(self) -> Dict[str, Any]:
        """
        Execute all active cleanup policies.
        
        This method identifies datasets/artifacts that match cleanup policy
        criteria and triggers cleanup operations.
        
        Returns:
            Execution summary with counts and details
        """
        self.log_operation("execute_cleanup_policies")
        
        # Get active policies
        policies = await self.cleanup_repo.get_active_policies()
        
        summary = {
            "policies_executed": 0,
            "items_cleaned": 0,
            "errors": [],
            "executed_at": datetime.utcnow().isoformat()
        }
        
        for policy in policies:
            try:
                # Log policy execution start
                self.logger.info(f"Executing cleanup policy: {policy.name}")
                
                # TODO: Implement actual cleanup logic
                # This would involve:
                # 1. Query datasets/artifacts matching policy criteria
                # 2. Check if items meet age/status requirements
                # 3. Trigger cleanup operations
                # 4. Log execution results
                
                # For now, just log the execution
                await self.execution_log_repo.create(
                    policy_type="cleanup",
                    policy_id=policy.id,
                    dataset_id=None,
                    status="success",
                    details={"message": "Policy execution placeholder"}
                )
                
                summary["policies_executed"] += 1
                
            except Exception as e:
                self.logger.error(f"Error executing policy {policy.name}: {e}")
                summary["errors"].append({
                    "policy_id": policy.id,
                    "policy_name": policy.name,
                    "error": str(e)
                })
        
        return summary

    async def get_execution_logs(
        self,
        dataset_id: Optional[int] = None,
        policy_type: Optional[str] = None,
        limit: int = 50
    ) -> List[PolicyExecutionLog]:
        """
        Get policy execution logs.
        
        Args:
            dataset_id: Filter by dataset ID
            policy_type: Filter by policy type (archival/cleanup)
            limit: Maximum number of logs to return
            
        Returns:
            List of execution logs
        """
        if dataset_id:
            return list(await self.execution_log_repo.get_by_dataset(dataset_id))
        
        # TODO: Implement filtering by policy_type and limit
        # For now, return empty list if no dataset_id
        return []
