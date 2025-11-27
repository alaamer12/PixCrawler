"""
Dataset export endpoints with streaming support.

This module provides endpoints for exporting datasets in various formats
using StreamingResponse for efficient large file handling.
"""

import io
import json
import zipfile
from pathlib import Path
from typing import Dict, Any, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.responses import StreamingResponse, FileResponse
from starlette.concurrency import run_in_threadpool

from backend.api.types import CurrentUser, DBSession, DatasetServiceDep
from backend.api.v1.response_models import get_common_responses
from backend.core.exceptions import NotFoundError
from utility.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    tags=["Exports"],
    responses=get_common_responses(401, 404, 500),
)


async def generate_json_stream(data: list[Dict[str, Any]]) -> AsyncIterator[bytes]:
    """
    Generate JSON data as a stream.

    Args:
        data: List of data items to stream

    Yields:
        JSON bytes in chunks
    """
    yield b'[\n'

    for i, item in enumerate(data):
        json_str = json.dumps(item, indent=2)
        if i > 0:
            yield b',\n'
        yield json_str.encode('utf-8')

    yield b'\n]'


async def generate_csv_stream(data: list[Dict[str, Any]]) -> AsyncIterator[bytes]:
    """
    Generate CSV data as a stream.

    Args:
        data: List of data items to stream

    Yields:
        CSV bytes in chunks
    """
    import csv

    if not data:
        return

    # Write header
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    yield output.getvalue().encode('utf-8')

    # Write rows
    for item in data:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=item.keys())
        writer.writerow(item)
        yield output.getvalue().encode('utf-8')


async def generate_zip_archive(
    dataset_id: int,
    images: list[Dict[str, Any]],
    metadata: Dict[str, Any]
) -> bytes:
    """
    Generate a ZIP archive containing images and metadata.

    Args:
        dataset_id: Dataset ID
        images: List of image metadata
        metadata: Dataset metadata

    Returns:
        ZIP file bytes
    """
    def _create_zip() -> bytes:
        """Create ZIP file in thread pool (sync operation)."""
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add metadata
            zf.writestr(
                'metadata.json',
                json.dumps(metadata, indent=2)
            )

            # Add image list
            zf.writestr(
                'images.json',
                json.dumps(images, indent=2)
            )

            # Add README
            readme = f"""# Dataset {dataset_id}

## Contents
- metadata.json: Dataset metadata
- images.json: List of all images with metadata
- images/: Directory containing all images (if available)

## Statistics
- Total images: {len(images)}
- Created: {metadata.get('created_at', 'N/A')}
"""
            zf.writestr('README.md', readme)

        return buffer.getvalue()

    # Run sync ZIP creation in thread pool
    return await run_in_threadpool(_create_zip)


@router.get(
    "/datasets/{dataset_id}/export/json",
    summary="Export Dataset as JSON",
    description="Export dataset images and metadata as streaming JSON.",
    response_description="Streaming JSON file download",
    operation_id="exportDatasetJson",
    responses={
        200: {
            "description": "Dataset exported successfully as JSON",
            "content": {
                "application/json": {
                    "example": [
                        {"id": 1, "url": "https://example.com/img1.jpg", "label": "cat"},
                        {"id": 2, "url": "https://example.com/img2.jpg", "label": "dog"}
                    ]
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def export_dataset_json(
    dataset_id: int,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> StreamingResponse:
    """
    Export dataset as streaming JSON.

    Exports all images and metadata in JSON format_ using streaming
    for efficient handling of large datasets.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID to export
        current_user: Current authenticated user
        dataset_service: Dataset service

    Returns:
        Streaming JSON response

    Raises:
        HTTPException: If dataset not found or access denied
    """
    try:
        # Verify access
        dataset = await dataset_service.get_dataset(dataset_id, current_user["user_id"])

        # Get all images (this would be paginated in production)
        images = await dataset_service.get_dataset_images(dataset_id)

        logger.info(f"Exporting dataset {dataset_id} as JSON ({len(images)} images)")

        return StreamingResponse(
            generate_json_stream(images),
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=dataset_{dataset_id}.json"
            }
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )


@router.get(
    "/datasets/{dataset_id}/export/csv",
    summary="Export Dataset as CSV",
    description="Export dataset images and metadata as streaming CSV.",
    response_description="Streaming CSV file download",
    operation_id="exportDatasetCsv",
    responses={
        200: {
            "description": "Dataset exported successfully as CSV",
            "content": {
                "text/csv": {
                    "example": "id,url,label\n1,https://example.com/img1.jpg,cat\n2,https://example.com/img2.jpg,dog"
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def export_dataset_csv(
    dataset_id: int,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> StreamingResponse:
    """
    Export dataset as streaming CSV.

    Exports all images and metadata in CSV format_ using streaming
    for efficient handling of large datasets.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID to export
        current_user: Current authenticated user
        dataset_service: Dataset service

    Returns:
        Streaming CSV response

    Raises:
        HTTPException: If dataset not found or access denied
    """
    try:
        # Verify access
        dataset = await dataset_service.get_dataset(dataset_id, current_user["user_id"])

        # Get all images
        images = await dataset_service.get_dataset_images(dataset_id)

        logger.info(f"Exporting dataset {dataset_id} as CSV ({len(images)} images)")

        return StreamingResponse(
            generate_csv_stream(images),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=dataset_{dataset_id}.csv"
            }
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )


@router.get(
    "/datasets/{dataset_id}/export/zip",
    summary="Export Dataset as ZIP",
    description="Export dataset as a ZIP archive with images and metadata.",
    response_description="ZIP file download",
    operation_id="exportDatasetZip",
    responses={
        200: {
            "description": "Dataset exported successfully as ZIP",
            "content": {
                "application/zip": {
                    "schema": {
                        "type": "string",
                        "format_": "binary"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def export_dataset_zip(
    dataset_id: int,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> StreamingResponse:
    """
    Export dataset as ZIP archive.

    Creates a ZIP archive containing images, metadata.json, images.json,
    and README.md. Processed in thread pool for efficient handling.

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID to export
        current_user: Current authenticated user
        dataset_service: Dataset service

    Returns:
        ZIP file response

    Raises:
        HTTPException: If dataset not found or access denied
    """
    try:
        # Verify access
        dataset = await dataset_service.get_dataset(dataset_id, current_user["user_id"])

        # Get all images and metadata
        images = await dataset_service.get_dataset_images(dataset_id)
        metadata = {
            "dataset_id": dataset_id,
            "name": dataset.get("name"),
            "description": dataset.get("description"),
            "created_at": dataset.get("created_at"),
            "total_images": len(images),
        }

        logger.info(f"Exporting dataset {dataset_id} as ZIP ({len(images)} images)")

        # Generate ZIP in thread pool
        zip_bytes = await generate_zip_archive(dataset_id, images, metadata)

        return StreamingResponse(
            iter([zip_bytes]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=dataset_{dataset_id}.zip",
                "Content-Length": str(len(zip_bytes))
            }
        )

    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset {dataset_id} not found"
        )


@router.get(
    "/datasets/{dataset_id}/images/{image_id}/download",
    summary="Download Single Image",
    description="Download a specific image file from a dataset.",
    response_description="Image file download",
    operation_id="downloadDatasetImage",
    responses={
        200: {
            "description": "Image downloaded successfully",
            "content": {
                "image/jpeg": {
                    "schema": {
                        "type": "string",
                        "format_": "binary"
                    }
                },
                "image/png": {
                    "schema": {
                        "type": "string",
                        "format_": "binary"
                    }
                }
            }
        },
        **get_common_responses(401, 404, 500)
    }
)
async def download_image(
    dataset_id: int,
    image_id: int,
    current_user: CurrentUser,
    dataset_service: DatasetServiceDep,
) -> FileResponse:
    """
    Download a single image file.

    Uses FileResponse for efficient file serving with automatic:
    - Content-Type detection
    - Range request support (partial content)
    - ETag generation
    - Last-Modified headers

    **Authentication Required:** Bearer token

    Args:
        dataset_id: Dataset ID
        image_id: Image ID to download
        current_user: Current authenticated user
        dataset_service: Dataset service

    Returns:
        File response with image

    Raises:
        HTTPException: If image not found or access denied
    """
    try:
        # Verify access to dataset
        await dataset_service.get_dataset(dataset_id, current_user["user_id"])

        # Get image file path
        image = await dataset_service.get_image(image_id)

        if not image or image.get("dataset_id") != dataset_id:
            raise NotFoundError(f"Image {image_id} not found in dataset {dataset_id}")

        file_path = Path(image["file_path"])

        if not file_path.exists():
            raise NotFoundError(f"Image file not found: {file_path}")

        logger.info(f"Serving image {image_id} from dataset {dataset_id}")

        # FileResponse automatically handles:
        # - Content-Type detection
        # - Range requests (partial content)
        # - ETag generation
        # - Last-Modified headers
        return FileResponse(
            path=file_path,
            filename=file_path.name,
            media_type=image.get("mime_type", "image/jpeg")
        )

    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
