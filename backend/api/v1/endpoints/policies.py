"""
API endpoints for dataset lifecycle policies.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

from backend.api.dependencies import get_current_user as get_current_active_user
from backend.schemas.policy import (
    ArchivalPolicyCreate,
    ArchivalPolicyResponse,
    ArchivalPolicyUpdate,
    CleanupPolicyCreate,
    CleanupPolicyResponse,
    CleanupPolicyUpdate,
)
from backend.services.policy import PolicyService
from backend.tasks.policy import execute_archival_policies, execute_cleanup_policies
from api.dependencies import get_policy_service

router = APIRouter(tags=["Policies"])


@router.post(
    "/archival",
    response_model=ArchivalPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create archival policy"
)
async def create_archival_policy(
    policy_in: ArchivalPolicyCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Create a new archival policy (Admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.create_archival_policy(policy_in)


@router.get(
    "/archival",
    response_model=List[ArchivalPolicyResponse],
    summary="List archival policies"
)
async def list_archival_policies(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """List all archival policies."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.list_archival_policies()


@router.get(
    "/archival/{policy_id}",
    response_model=ArchivalPolicyResponse,
    summary="Get archival policy"
)
async def get_archival_policy(
    policy_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Get archival policy by ID."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.get_archival_policy(policy_id)


@router.patch(
    "/archival/{policy_id}",
    response_model=ArchivalPolicyResponse,
    summary="Update archival policy"
)
async def update_archival_policy(
    policy_id: int,
    policy_in: ArchivalPolicyUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Update archival policy."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.update_archival_policy(policy_id, policy_in)


@router.delete(
    "/archival/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete archival policy"
)
async def delete_archival_policy(
    policy_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Delete archival policy."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await service.delete_archival_policy(policy_id)


# --- Cleanup Policies ---

@router.post(
    "/cleanup",
    response_model=CleanupPolicyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create cleanup policy"
)
async def create_cleanup_policy(
    policy_in: CleanupPolicyCreate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Create a new cleanup policy (Admin only)."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.create_cleanup_policy(policy_in)


@router.get(
    "/cleanup",
    response_model=List[CleanupPolicyResponse],
    summary="List cleanup policies"
)
async def list_cleanup_policies(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """List all cleanup policies."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.list_cleanup_policies()


@router.get(
    "/cleanup/{policy_id}",
    response_model=CleanupPolicyResponse,
    summary="Get cleanup policy"
)
async def get_cleanup_policy(
    policy_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Get cleanup policy by ID."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.get_cleanup_policy(policy_id)


@router.patch(
    "/cleanup/{policy_id}",
    response_model=CleanupPolicyResponse,
    summary="Update cleanup policy"
)
async def update_cleanup_policy(
    policy_id: int,
    policy_in: CleanupPolicyUpdate,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Update cleanup policy."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.update_cleanup_policy(policy_id, policy_in)


@router.delete(
    "/cleanup/{policy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete cleanup policy"
)
async def delete_cleanup_policy(
    policy_id: int,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    service: PolicyService = Depends(get_policy_service),
):
    """Delete cleanup policy."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    await service.delete_cleanup_policy(policy_id)


# --- Execution ---

@router.post(
    "/execute/archival",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger archival policy execution"
)
async def trigger_archival_execution(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    """Trigger archival policy execution manually."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Use Celery task
    execute_archival_policies.delay()
    return {"message": "Archival policy execution triggered"}


@router.post(
    "/execute/cleanup",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger cleanup policy execution"
)
async def trigger_cleanup_execution(
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
):
    """Trigger cleanup policy execution manually."""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    # Use Celery task
    execute_cleanup_policies.delay()
    return {"message": "Cleanup policy execution triggered"}
