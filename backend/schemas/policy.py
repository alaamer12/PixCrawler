"""
Policy Pydantic models and schemas.

This module provides schemas for archival and cleanup policies,
including validation and request/response models.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime

from pydantic import Field, model_validator

from .base import BaseSchema, TimestampMixin

__all__ = [
    'StorageTier',
    'PolicyType',
    'CleanupTarget',
    'ArchivalPolicyCreate',
    'ArchivalPolicyUpdate',
    'ArchivalPolicyResponse',
    'CleanupPolicyCreate',
    'CleanupPolicyUpdate',
    'CleanupPolicyResponse',
    'PolicyExecutionLogResponse',
]


class StorageTier(str, Enum):
    """Storage tier enumeration."""
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


class PolicyType(str, Enum):
    """Policy type enumeration."""
    ARCHIVAL = "archival"
    CLEANUP = "cleanup"


class CleanupTarget(str, Enum):
    """Cleanup target enumeration."""
    FULL_DATASET = "full_dataset"
    TEMP_FILES = "temp_files"
    FAILED_JOBS = "failed_jobs"


# --- Archival Policy Schemas ---

class ArchivalPolicyBase(BaseSchema):
    """Base schema for archival policies."""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Policy name"
    )
    description: Optional[str] = Field(None, description="Policy description")
    is_active: bool = Field(True, description="Whether policy is active")
    days_until_archive: int = Field(
        ..., 
        ge=1, 
        description="Days since creation/access before archiving"
    )
    target_tier: StorageTier = Field(
        StorageTier.COLD,
        description="Target storage tier"
    )
    filter_criteria: Optional[Dict[str, Any]] = Field(
        None,
        description="Criteria to filter datasets"
    )


class ArchivalPolicyCreate(ArchivalPolicyBase):
    """Schema for creating an archival policy."""
    pass


class ArchivalPolicyUpdate(BaseSchema):
    """Schema for updating an archival policy."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    days_until_archive: Optional[int] = Field(None, ge=1)
    target_tier: Optional[StorageTier] = None
    filter_criteria: Optional[Dict[str, Any]] = None


class ArchivalPolicyResponse(ArchivalPolicyBase, TimestampMixin):
    """Response schema for archival policy."""
    
    id: int = Field(..., description="Policy ID")


# --- Cleanup Policy Schemas ---

class CleanupPolicyBase(BaseSchema):
    """Base schema for cleanup policies."""
    
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Policy name"
    )
    description: Optional[str] = Field(None, description="Policy description")
    is_active: bool = Field(True, description="Whether policy is active")
    days_until_cleanup: int = Field(
        ..., 
        ge=1, 
        description="Days since creation/completion before cleanup"
    )
    cleanup_target: CleanupTarget = Field(
        CleanupTarget.TEMP_FILES,
        description="What to cleanup"
    )
    filter_criteria: Optional[Dict[str, Any]] = Field(
        None,
        description="Criteria to filter datasets"
    )


class CleanupPolicyCreate(CleanupPolicyBase):
    """Schema for creating a cleanup policy."""
    pass


class CleanupPolicyUpdate(BaseSchema):
    """Schema for updating a cleanup policy."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    days_until_cleanup: Optional[int] = Field(None, ge=1)
    cleanup_target: Optional[CleanupTarget] = None
    filter_criteria: Optional[Dict[str, Any]] = None


class CleanupPolicyResponse(CleanupPolicyBase, TimestampMixin):
    """Response schema for cleanup policy."""
    
    id: int = Field(..., description="Policy ID")


# --- Execution Log Schemas ---

class PolicyExecutionLogResponse(BaseSchema):
    """Response schema for policy execution logs."""
    
    id: int = Field(..., description="Log ID")
    policy_type: PolicyType = Field(..., description="Type of policy executed")
    policy_id: int = Field(..., description="ID of the policy executed")
    dataset_id: Optional[int] = Field(None, description="ID of the affected dataset")
    status: str = Field(..., description="Execution status")
    details: Optional[Dict[str, Any]] = Field(None, description="Execution details")
    executed_at: datetime = Field(..., description="Execution timestamp")
