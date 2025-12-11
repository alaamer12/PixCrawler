"""
Simple flow service for streamlined crawl operations.

This service provides a clean, simple alternative to the complex crawl_job system.
It focuses on just crawling images and validating them without all the overhead.
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from backend.models.flow import Flow
from backend.repositories.flow_repository import FlowRepository
from backend.services.base import BaseService
from utility.logging_config import get_logger

logger = get_logger(__name__)


class FlowService(BaseService):
    """Simple service for crawl flows."""
    
    def __init__(self, flow_repo: FlowRepository):
        super().__init__()
        self.flow_repo = flow_repo
    
    async def create_flow(
        self,
        keywords: List[str],
        max_images: int = 50,
        engines: List[str] = None,
        output_name: str = None
    ) -> Flow:
        """Create a new flow."""
        
        if not engines:
            engines = ["duckduckgo"]
        
        # Generate unique flow ID
        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        
        # Create output directory name
        if not output_name:
            keywords_str = "_".join(keywords[:3])  # First 3 keywords
            output_name = f"{keywords_str}_{flow_id}"
        
        # Create output path (permanent directory for debugging)
        output_path = f"datasets/{output_name}"
        Path(output_path).mkdir(parents=True, exist_ok=True)
        
        # Calculate total tasks (keywords × engines)
        total_tasks = len(keywords) * len(engines)
        
        # Create flow record
        flow = await self.flow_repo.create(
            flow_id=flow_id,
            keywords=keywords,
            max_images=max_images,
            engines=engines,
            output_path=output_path,
            output_name=output_name,
            total_tasks=total_tasks,
            status="pending"
        )
        
        logger.info(
            f"Created flow {flow_id} with {len(keywords)} keywords and {len(engines)} engines",
            flow_id=flow_id,
            keywords=keywords,
            engines=engines,
            total_tasks=total_tasks
        )
        
        return flow
    
    async def start_flow(self, flow_id: str) -> Dict[str, Any]:
        """Start a flow by dispatching Celery tasks."""
        
        # Import tasks
        from builder.tasks import (
            task_download_duckduckgo,
            task_download_google,
            task_download_bing
        )
        
        # Get flow
        flow = await self.flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Flow not found: {flow_id}")
        
        if flow.status != "pending":
            raise ValueError(f"Flow {flow_id} is not pending (status: {flow.status})")
        
        # Map engines to tasks
        engine_tasks = {
            "duckduckgo": task_download_duckduckgo,
            "google": task_download_google,
            "bing": task_download_bing
        }
        
        # Dispatch tasks
        task_ids = []
        images_per_keyword = max(1, flow.max_images // len(flow.keywords))
        
        logger.info(
            f"Starting flow {flow_id}: {len(flow.keywords)} keywords × {len(flow.engines)} engines",
            flow_id=flow_id,
            images_per_keyword=images_per_keyword
        )
        
        for keyword in flow.keywords:
            for engine in flow.engines:
                task_func = engine_tasks.get(engine.lower())
                if not task_func:
                    logger.warning(f"Unknown engine '{engine}', skipping")
                    continue
                
                # Create keyword-specific output directory
                keyword_output = f"{flow.output_path}/{keyword}"
                Path(keyword_output).mkdir(parents=True, exist_ok=True)
                
                # Dispatch task
                task = task_func.delay(
                    keyword=keyword,
                    output_dir=keyword_output,
                    max_images=images_per_keyword,
                    job_id=flow_id,
                    user_id="flow_user"
                )
                
                task_ids.append(task.id)
                
                logger.debug(
                    f"Dispatched {engine} task for '{keyword}': {task.id}",
                    flow_id=flow_id,
                    keyword=keyword,
                    engine=engine,
                    task_id=task.id
                )
        
        # Update flow with task IDs and running status
        flow.task_ids = task_ids
        flow.status = "running"
        flow.started_at = datetime.utcnow()
        await self.flow_repo.session.commit()
        await self.flow_repo.session.refresh(flow)
        
        logger.info(
            f"Flow {flow_id} started with {len(task_ids)} tasks",
            flow_id=flow_id,
            task_count=len(task_ids)
        )
        
        return {
            "flow_id": flow_id,
            "status": "running",
            "task_ids": task_ids,
            "total_tasks": len(task_ids),
            "message": f"Flow started with {len(task_ids)} tasks"
        }
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow status and progress."""
        
        flow = await self.flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Flow not found: {flow_id}")
        
        # Count actual files in output directory
        output_path = Path(flow.output_path)
        if output_path.exists():
            image_files = []
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                image_files.extend(output_path.rglob(ext))
            actual_downloaded = len(image_files)
        else:
            actual_downloaded = 0
        
        return {
            "flow_id": flow_id,
            "status": flow.status,
            "progress": flow.progress,
            "downloaded_images": actual_downloaded,  # Use actual file count
            "validated_images": flow.validated_images,
            "total_tasks": flow.total_tasks,
            "completed_tasks": flow.completed_tasks,
            "failed_tasks": flow.failed_tasks,
            "output_path": flow.output_path,
            "started_at": flow.started_at.isoformat() if flow.started_at else None,
            "completed_at": flow.completed_at.isoformat() if flow.completed_at else None
        }
    
    async def get_flow_result(self, flow_id: str) -> Dict[str, Any]:
        """Get final flow result with file list."""
        
        flow = await self.flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Flow not found: {flow_id}")
        
        # Get actual files
        output_path = Path(flow.output_path)
        file_list = []
        total_size = 0
        
        if output_path.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                for file_path in output_path.rglob(ext):
                    file_size = file_path.stat().st_size
                    total_size += file_size
                    file_list.append({
                        "filename": file_path.name,
                        "path": str(file_path.relative_to(output_path)),
                        "size_bytes": file_size,
                        "size_mb": round(file_size / (1024 * 1024), 2)
                    })
        
        # Calculate processing time
        processing_time = 0
        if flow.started_at and flow.completed_at:
            processing_time = (flow.completed_at - flow.started_at).total_seconds()
        
        return {
            "flow_id": flow_id,
            "status": flow.status,
            "total_downloaded": len(file_list),
            "total_validated": flow.validated_images,
            "total_failed": flow.failed_tasks,
            "output_path": flow.output_path,
            "file_list": file_list,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "processing_time": processing_time,
            "engines_used": flow.engines,
            "keywords_processed": flow.keywords
        }
    
    async def validate_flow_images(self, flow_id: str) -> Dict[str, Any]:
        """Validate all images in a flow."""
        
        from validator.tasks import validate_image_fast_task
        
        flow = await self.flow_repo.get_by_flow_id(flow_id)
        if not flow:
            raise ValueError(f"Flow not found: {flow_id}")
        
        # Get all image files
        output_path = Path(flow.output_path)
        image_files = []
        
        if output_path.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.webp']:
                image_files.extend(output_path.rglob(ext))
        
        if not image_files:
            return {
                "flow_id": flow_id,
                "message": "No images to validate",
                "validated": 0,
                "task_ids": []
            }
        
        # Dispatch validation tasks
        validation_task_ids = []
        
        for image_file in image_files:
            task = validate_image_fast_task.delay(
                image_path=str(image_file),
                job_id=flow_id,
                image_id=image_file.stem
            )
            validation_task_ids.append(task.id)
        
        logger.info(
            f"Started validation for flow {flow_id}: {len(validation_task_ids)} tasks",
            flow_id=flow_id,
            image_count=len(image_files)
        )
        
        return {
            "flow_id": flow_id,
            "message": f"Validation started for {len(image_files)} images",
            "validated": len(image_files),
            "task_ids": validation_task_ids
        }