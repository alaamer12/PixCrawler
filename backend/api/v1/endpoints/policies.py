"""
API endpoints for dataset lifecycle policies.

This module provides REST API endpoints for managing dataset lifecycle policies
including archival and cleanup policies. All endpoints require admin privileges.

Endpoints:
    POST /archival - Create archival policy
    GET /archival - List archival policies
    GET /archival/{policy_id} - Get archival policy
    PATCH /archival/{policy_id} - Update archival policy
    DELETE /archival/{policy_id} - Delete archival policy
    POST /cleanup - Create cleanup policy
    GET /cleanup - List cleanup policies
    GET /cleanup/{policy_id} - Get cleanup policy
    PATCH /cleanup/{policy_id} - Update cleanup policy
    DELETE /cleanup/{policy_id} - Delete cleanup policy
    POST /execute/archival - Trigger archival execution
    POST /execute/cleanup - Trigger cleanup execution

Authentication:
    All endpoints require admin authentication via Supabase JWT token.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status as http_status, BackgroundTasks

from backend.api.types import AdminUser, PolicyServiceDep
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyResponse,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyResponse,
    CleanupPolicyUpdate,
)
from backend.tasks.policy import execute_archival_policies, execute_cleanup_policies

router = APIRouter(tags=["Policies"])


@router.post(
    "/archival",
    response_model=ArchivalPolicyResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create archival policy",
    operation_id="createArchivalPolicy"
)
async def create_archival_policy(
    policy_in: ArchivalPolicyCreate,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Create a new archival policy (Admin only)."""
    return await service.create_archival_policy(policy_in)


@router.get(
    "/archival",
    response_model=List[ArchivalPolicyResponse],
    summary="List archival policies",
    operation_id="listArchivalPolicies"
)
async def list_archival_policies(
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """List all archival policies."""
    return await service.list_archival_policies()


@router.get(
    "/archival/{policy_id}",
    response_model=ArchivalPolicyResponse,
    summary="Get archival policy",
    operation_id="getArchivalPolicy"
)
async def get_archival_policy(
    policy_id: int,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Get archival policy by ID."""
    return await service.get_archival_policy(policy_id)


@router.patch(
    "/archival/{policy_id}",
    response_model=ArchivalPolicyResponse,
    summary="Update archival policy",
    operation_id="updateArchivalPolicy"
)
async def update_archival_policy(
    policy_id: int,
    policy_in: ArchivalPolicyUpdate,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Update archival policy."""
    return await service.update_archival_policy(policy_id, policy_in)


@router.delete(
    "/archival/{policy_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete archival policy",
    operation_id="deleteArchivalPolicy"
)
async def delete_archival_policy(
    policy_id: int,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Delete archival policy."""
    await service.delete_archival_policy(policy_id)


# --- Cleanup Policies ---

@router.post(
    "/cleanup",
    response_model=CleanupPolicyResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create cleanup policy",
    operation_id="createCleanupPolicy"
)
async def create_cleanup_policy(
    policy_in: CleanupPolicyCreate,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Create a new cleanup policy (Admin only)."""
    return await service.create_cleanup_policy(policy_in)


@router.get(
    "/cleanup",
    response_model=List[CleanupPolicyResponse],
    summary="List cleanup policies",
    operation_id="listCleanupPolicies"
)
async def list_cleanup_policies(
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """List all cleanup policies."""
    return await service.list_cleanup_policies()


@router.get(
    "/cleanup/{policy_id}",
    response_model=CleanupPolicyResponse,
    summary="Get cleanup policy",
    operation_id="getCleanupPolicy"
)
async def get_cleanup_policy(
    policy_id: int,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Get cleanup policy by ID."""
    return await service.get_cleanup_policy(policy_id)


@router.patch(
    "/cleanup/{policy_id}",
    response_model=CleanupPolicyResponse,
    summary="Update cleanup policy",
    operation_id="updateCleanupPolicy"
)
async def update_cleanup_policy(
    policy_id: int,
    policy_in: CleanupPolicyUpdate,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Update cleanup policy."""
    return await service.update_cleanup_policy(policy_id, policy_in)


@router.delete(
    "/cleanup/{policy_id}",
    status_code=http_status.HTTP_204_NO_CONTENT,
    summary="Delete cleanup policy",
    operation_id="deleteCleanupPolicy"
)
async def delete_cleanup_policy(
    policy_id: int,
    admin_user: AdminUser,
    service: PolicyServiceDep,
):
    """Delete cleanup policy."""
    await service.delete_cleanup_policy(policy_id)


# --- Execution ---

@router.post(
    "/execute/archival",
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Trigger archival policy execution",
    operation_id="triggerArchivalExecution"
)
async def trigger_archival_execution(
    background_tasks: BackgroundTasks,
    admin_user: AdminUser,
):
    """Trigger archival policy execution manually."""
    # Use Celery task
    execute_archival_policies.delay()
    return {"message": "Archival policy execution triggered"}


@router.post(
    "/execute/cleanup",
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Trigger cleanup policy execution",
    operation_id="triggerCleanupExecution"
)
async def trigger_cleanup_execution(
    background_tasks: BackgroundTasks,
    admin_user: AdminUser,
):
    """Trigger cleanup policy execution manually."""
    # Use Celery task
    execute_cleanup_policies.delay()
    return {"message": "Cleanup policy execution triggered"}
