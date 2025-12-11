"""
Simple flow endpoints for streamlined crawl operations.

This module provides clean, simple endpoints for crawling images
without the complexity of the full crawl_job system.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status

from backend.api.v1.response_models import get_common_responses
from backend.schemas.flow import (
    FlowRequest,
    FlowResponse,
    FlowStatus,
    FlowResult
)
from backend.services.flow import FlowService
from backend.repositories.flow_repository import FlowRepository
from backend.database.connection import get_session
from utility.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/flow",
    tags=["Flow"],
    responses=get_common_responses(500),
)


async def get_flow_service(session = Depends(get_session)) -> FlowService:
    """Get flow service with dependencies."""
    flow_repo = FlowRepository(session)
    return FlowService(flow_repo)


@router.post(
    "/start",
    response_model=FlowResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Start Simple Flow",
    description="Start a simple crawl flow that downloads and validates images.",
    operation_id="startFlow",
)
async def start_flow(
    request: FlowRequest,
    service: FlowService = Depends(get_flow_service)
) -> FlowResponse:
    """
    Start a simple crawl flow.
    
    This endpoint creates and starts a flow that:
    1. Downloads images for the specified keywords
    2. Saves them to a permanent directory (datasets/)
    3. Optionally validates the images
    
    No complex job management - just simple, direct crawling.
    """
    try:
        # Create flow
        flow = await service.create_flow(
            keywords=request.keywords,
            max_images=request.max_images,
            engines=request.engines,
            output_name=request.output_name
        )
        
        # Start flow
        result = await service.start_flow(flow.flow_id)
        
        return FlowResponse(
            flow_id=flow.flow_id,
            status=result["status"],
            keywords=flow.keywords,
            max_images=flow.max_images,
            engines=flow.engines,
            output_path=flow.output_path,
            task_ids=result["task_ids"],
            message=result["message"]
        )
        
    except Exception as e:
        logger.error(f"Failed to start flow: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start flow: {str(e)}"
        )


@router.get(
    "/{flow_id}/status",
    response_model=FlowStatus,
    summary="Get Flow Status",
    description="Get current status and progress of a flow.",
    operation_id="getFlowStatus",
)
async def get_flow_status(
    flow_id: str,
    service: FlowService = Depends(get_flow_service)
) -> FlowStatus:
    """Get flow status and progress."""
    try:
        status_data = await service.get_flow_status(flow_id)
        return FlowStatus(**status_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get flow status: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow status: {str(e)}"
        )


@router.get(
    "/{flow_id}/result",
    response_model=FlowResult,
    summary="Get Flow Result",
    description="Get final result of a completed flow with file list.",
    operation_id="getFlowResult",
)
async def get_flow_result(
    flow_id: str,
    service: FlowService = Depends(get_flow_service)
) -> FlowResult:
    """Get flow result with downloaded files."""
    try:
        result_data = await service.get_flow_result(flow_id)
        return FlowResult(**result_data)
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to get flow result: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get flow result: {str(e)}"
        )


@router.post(
    "/{flow_id}/validate",
    summary="Validate Flow Images",
    description="Validate all images in a completed flow.",
    operation_id="validateFlowImages",
)
async def validate_flow_images(
    flow_id: str,
    service: FlowService = Depends(get_flow_service)
) -> Dict[str, Any]:
    """Validate all images in a flow."""
    try:
        result = await service.validate_flow_images(flow_id)
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to validate flow images: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate flow images: {str(e)}"
        )


@router.get(
    "/",
    response_model=List[FlowStatus],
    summary="List All Flows",
    description="List all flows with their current status.",
    operation_id="listFlows",
)
async def list_flows(
    service: FlowService = Depends(get_flow_service)
) -> List[FlowStatus]:
    """List all flows."""
    try:
        flows = await service.flow_repo.get_active_flows()
        
        status_list = []
        for flow in flows:
            status_data = await service.get_flow_status(flow.flow_id)
            status_list.append(FlowStatus(**status_data))
        
        return status_list
        
    except Exception as e:
        logger.error(f"Failed to list flows: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list flows: {str(e)}"
        )