"""
Simple flow endpoints using standalone flow system.

This bypasses all database complexity and uses file-based storage.
"""

from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException
from fastapi import status as http_status
from pydantic import BaseModel, Field

from backend.simple_flow import flow_manager
from utility.logging_config import get_logger

logger = get_logger(__name__)

# Simple request/response models
class SimpleFlowRequest(BaseModel):
    """Request to start a simple flow."""
    keywords: List[str] = Field(..., min_items=1, max_items=10)
    max_images: int = Field(10, ge=1, le=1000)
    engines: List[str] = Field(["duckduckgo"], min_items=1)
    output_name: str = Field(..., min_length=1, max_length=100)

class SimpleFlowResponse(BaseModel):
    """Response from starting a flow."""
    flow_id: str
    status: str
    message: str
    output_path: str
    task_count: int

router = APIRouter(
    prefix="/simple-flow",
    tags=["Simple Flow"],
)

@router.post(
    "/start",
    response_model=SimpleFlowResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Start Simple Flow",
    description="Start a simple crawl flow that downloads images directly to datasets/",
)
async def start_simple_flow(request: SimpleFlowRequest) -> SimpleFlowResponse:
    """Start a simple crawl flow."""
    try:
        # Create flow
        flow = flow_manager.create_flow(
            keywords=request.keywords,
            max_images=request.max_images,
            engines=request.engines,
            output_name=request.output_name
        )
        
        # Start flow
        result = flow_manager.start_flow(flow.flow_id)
        
        return SimpleFlowResponse(
            flow_id=flow.flow_id,
            status=result["status"],
            message=result["message"],
            output_path=flow.output_path,
            task_count=len(result["task_ids"])
        )
        
    except Exception as e:
        logger.error(f"Failed to start simple flow: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start flow: {str(e)}"
        )

@router.get(
    "/{flow_id}/status",
    summary="Get Flow Status",
    description="Get current status and progress of a simple flow.",
)
async def get_simple_flow_status(flow_id: str) -> Dict[str, Any]:
    """Get flow status and progress."""
    try:
        return flow_manager.get_flow_status(flow_id)
        
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
    summary="Get Flow Result",
    description="Get final result of a completed flow with file list.",
)
async def get_simple_flow_result(flow_id: str) -> Dict[str, Any]:
    """Get flow result with downloaded files."""
    try:
        return flow_manager.get_flow_result(flow_id)
        
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
    "/{flow_id}/upload-azure",
    summary="Upload to Azure",
    description="Upload completed flow dataset to Azure Blob Storage.",
)
async def upload_flow_to_azure(flow_id: str) -> Dict[str, Any]:
    """Upload flow dataset to Azure Blob Storage."""
    try:
        result = await flow_manager.upload_to_azure(flow_id)
        
        if result.get("success"):
            return result
        else:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Upload failed")
            )
        
    except ValueError as e:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to upload flow to Azure: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload to Azure: {str(e)}"
        )

@router.get(
    "/",
    summary="List All Flows",
    description="List all simple flows with their current status.",
)
async def list_simple_flows() -> List[Dict[str, Any]]:
    """List all flows."""
    try:
        return flow_manager.list_flows()
        
    except Exception as e:
        logger.error(f"Failed to list flows: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list flows: {str(e)}"
        )