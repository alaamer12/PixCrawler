#!/usr/bin/env python3
"""
Standalone simple flow system that bypasses all model complexity.

This creates a minimal flow system that:
1. Takes keywords and crawls images directly
2. Saves to datasets/ directory 
3. Returns progress and results
4. No database dependencies - uses file system only
"""

import os
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

from celery_core.app import get_celery_app
from utility.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class SimpleFlow:
    """Simple flow data structure."""
    flow_id: str
    keywords: List[str]
    max_images: int
    engines: List[str]
    output_name: str
    output_path: str
    status: str = "pending"
    progress: int = 0
    downloaded_images: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    task_ids: List[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.task_ids is None:
            self.task_ids = []

class SimpleFlowManager:
    """Manager for simple flows using file system storage."""
    
    def __init__(self):
        self.flows_dir = Path("flows_data")
        self.flows_dir.mkdir(exist_ok=True)
        self.datasets_dir = Path("datasets")
        self.datasets_dir.mkdir(exist_ok=True)
        self.celery_app = get_celery_app()
    
    def _get_flow_file(self, flow_id: str) -> Path:
        """Get flow data file path."""
        return self.flows_dir / f"{flow_id}.json"
    
    def _save_flow(self, flow: SimpleFlow) -> None:
        """Save flow to file."""
        flow_file = self._get_flow_file(flow.flow_id)
        
        # Convert datetime objects to strings for JSON serialization
        flow_dict = asdict(flow)
        if flow_dict['started_at']:
            flow_dict['started_at'] = flow.started_at.isoformat()
        if flow_dict['completed_at']:
            flow_dict['completed_at'] = flow.completed_at.isoformat()
        
        with open(flow_file, 'w') as f:
            json.dump(flow_dict, f, indent=2)
    
    def _load_flow(self, flow_id: str) -> Optional[SimpleFlow]:
        """Load flow from file."""
        flow_file = self._get_flow_file(flow_id)
        
        if not flow_file.exists():
            return None
        
        try:
            with open(flow_file, 'r') as f:
                flow_dict = json.load(f)
            
            # Convert string dates back to datetime objects
            if flow_dict.get('started_at'):
                flow_dict['started_at'] = datetime.fromisoformat(flow_dict['started_at'])
            if flow_dict.get('completed_at'):
                flow_dict['completed_at'] = datetime.fromisoformat(flow_dict['completed_at'])
            
            return SimpleFlow(**flow_dict)
        except Exception as e:
            logger.error(f"Failed to load flow {flow_id}: {e}")
            return None
    
    def create_flow(
        self,
        keywords: List[str],
        max_images: int,
        engines: List[str],
        output_name: str
    ) -> SimpleFlow:
        """Create a new flow."""
        
        flow_id = f"flow_{uuid.uuid4().hex[:8]}"
        output_path = str(self.datasets_dir / output_name)
        
        # Create output directory
        os.makedirs(output_path, exist_ok=True)
        
        flow = SimpleFlow(
            flow_id=flow_id,
            keywords=keywords,
            max_images=max_images,
            engines=engines,
            output_name=output_name,
            output_path=output_path,
            total_tasks=len(keywords) * len(engines)
        )
        
        self._save_flow(flow)
        logger.info(f"Created flow {flow_id} with output: {output_path}")
        
        return flow
    
    def start_flow(self, flow_id: str) -> Dict[str, Any]:
        """Start flow execution."""
        
        flow = self._load_flow(flow_id)
        if not flow:
            raise ValueError(f"Flow {flow_id} not found")
        
        if flow.status != "pending":
            raise ValueError(f"Flow {flow_id} is not in pending state")
        
        try:
            # Update flow status
            flow.status = "running"
            flow.started_at = datetime.utcnow()
            
            # Dispatch Celery tasks
            task_ids = []
            
            for keyword in flow.keywords:
                for engine in flow.engines:
                    # Use the existing crawl task from builder
                    task = self.celery_app.send_task(
                        'builder.tasks.crawl_images',
                        args=[{
                            'keywords': [keyword],
                            'max_images': flow.max_images // len(flow.keywords),
                            'engines': [engine],
                            'output_dir': flow.output_path,
                            'validate_images': True
                        }],
                        queue='crawl'
                    )
                    task_ids.append(task.id)
            
            flow.task_ids = task_ids
            self._save_flow(flow)
            
            logger.info(f"Started flow {flow_id} with {len(task_ids)} tasks")
            
            return {
                "status": "running",
                "task_ids": task_ids,
                "message": f"Started {len(task_ids)} crawl tasks"
            }
            
        except Exception as e:
            flow.status = "failed"
            flow.error_message = str(e)
            self._save_flow(flow)
            logger.error(f"Failed to start flow {flow_id}: {e}")
            raise
    
    def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get flow status with real-time progress."""
        
        flow = self._load_flow(flow_id)
        if not flow:
            raise ValueError(f"Flow {flow_id} not found")
        
        # Count actual downloaded images
        downloaded_count = 0
        if os.path.exists(flow.output_path):
            for root, dirs, files in os.walk(flow.output_path):
                image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
                downloaded_count += len(image_files)
        
        # Check task status if running
        completed_tasks = 0
        if flow.task_ids:
            for task_id in flow.task_ids:
                try:
                    result = self.celery_app.AsyncResult(task_id)
                    if result.ready():
                        completed_tasks += 1
                except Exception:
                    pass
        
        # Update progress
        if flow.total_tasks > 0:
            progress = int((completed_tasks / flow.total_tasks) * 100)
        else:
            progress = 0
        
        # Update status based on completion
        if flow.status == "running":
            if completed_tasks >= flow.total_tasks:
                flow.status = "completed"
                flow.completed_at = datetime.utcnow()
                flow.progress = 100
                self._save_flow(flow)
        
        flow.downloaded_images = downloaded_count
        flow.completed_tasks = completed_tasks
        flow.progress = progress
        
        return {
            "flow_id": flow.flow_id,
            "status": flow.status,
            "progress": progress,
            "downloaded_images": downloaded_count,
            "total_tasks": flow.total_tasks,
            "completed_tasks": completed_tasks,
            "keywords": flow.keywords,
            "engines": flow.engines,
            "output_path": flow.output_path,
            "started_at": flow.started_at.isoformat() if flow.started_at else None,
            "completed_at": flow.completed_at.isoformat() if flow.completed_at else None,
            "error_message": flow.error_message
        }
    
    def get_flow_result(self, flow_id: str) -> Dict[str, Any]:
        """Get final flow result with file list."""
        
        flow = self._load_flow(flow_id)
        if not flow:
            raise ValueError(f"Flow {flow_id} not found")
        
        if flow.status not in ["completed", "failed"]:
            # Get current status first
            status = self.get_flow_status(flow_id)
            if status["status"] not in ["completed", "failed"]:
                raise ValueError(f"Flow {flow_id} is not completed yet")
        
        # Collect file information
        file_list = []
        total_size = 0
        
        if os.path.exists(flow.output_path):
            for root, dirs, files in os.walk(flow.output_path):
                for file in files:
                    if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            total_size += file_size
                            
                            file_list.append({
                                "filename": file,
                                "path": os.path.relpath(file_path, flow.output_path),
                                "size_bytes": file_size,
                                "size_mb": round(file_size / (1024 * 1024), 2)
                            })
                        except OSError:
                            continue
        
        # Calculate processing time
        processing_time = 0
        if flow.started_at and flow.completed_at:
            processing_time = (flow.completed_at - flow.started_at).total_seconds()
        
        return {
            "flow_id": flow.flow_id,
            "status": flow.status,
            "total_downloaded": len(file_list),
            "output_path": flow.output_path,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "processing_time": processing_time,
            "file_list": file_list[:20],  # Limit to first 20 files
            "keywords": flow.keywords,
            "engines": flow.engines,
            "error_message": flow.error_message
        }
    
    def list_flows(self) -> List[Dict[str, Any]]:
        """List all flows."""
        
        flows = []
        
        for flow_file in self.flows_dir.glob("*.json"):
            flow_id = flow_file.stem
            try:
                status = self.get_flow_status(flow_id)
                flows.append(status)
            except Exception as e:
                logger.error(f"Failed to get status for flow {flow_id}: {e}")
        
        return flows

# Global instance
flow_manager = SimpleFlowManager()