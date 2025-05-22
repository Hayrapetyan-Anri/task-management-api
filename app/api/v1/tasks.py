"""
Task API endpoints.

This module defines all REST API endpoints for task management operations,
including CRUD operations, filtering, pagination, and background processing.
"""

import math
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.task import (
    TaskCreate,
    TaskFilterParams,
    TaskListResponse,
    TaskProcessResponse,
    TaskResponse,
    TaskSummaryResponse,
    TaskUpdate,
)
from app.services.background_tasks import process_task, get_processing_status
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


async def get_task_service(db: AsyncSession = Depends(get_db)) -> TaskService:
    """
    Dependency function to get task service instance.
    
    Args:
        db: Database session
        
    Returns:
        TaskService instance
    """
    return TaskService(db)


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Create a new task with the provided title, description, and priority."
)
async def create_task(
    task_data: TaskCreate,
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Create a new task.
    
    Args:
        task_data: Task creation data
        task_service: Task service instance
        
    Returns:
        Created task data
        
    Raises:
        HTTPException: If task creation fails
    """
    try:
        task = await task_service.create_task(task_data)
        return TaskResponse.model_validate(task)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create task"
        )


@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List tasks with filtering and pagination",
    description="Retrieve a paginated list of tasks with optional filtering by status, priority, and title."
)
async def list_tasks(
    task_status: str = Query(None, description="Filter by task status", alias="status"),
    priority: int = Query(None, description="Filter by task priority"),
    title: str = Query(None, description="Filter by title (partial match)"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    task_service: TaskService = Depends(get_task_service)
) -> TaskListResponse:
    """
    List tasks with filtering and pagination.
    
    Args:
        task_status: Optional status filter
        priority: Optional priority filter
        title: Optional title filter (partial match)
        page: Page number (1-based)
        per_page: Number of items per page
        task_service: Task service instance
        
    Returns:
        Paginated list of tasks
        
    Raises:
        HTTPException: If filtering parameters are invalid
    """
    try:
        # Validate and create filter parameters
        filters = TaskFilterParams(
            status=task_status,
            priority=priority,
            title=title,
            page=page,
            per_page=per_page
        )
        
        tasks, total_count = await task_service.get_tasks(filters)
        
        # Calculate pagination metadata
        total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
        has_next = page < total_pages
        has_prev = page > 1
        
        # Convert to response format
        task_summaries = [TaskSummaryResponse.model_validate(task) for task in tasks]
        
        return TaskListResponse(
            items=task_summaries,
            total=total_count,
            page=page,
            per_page=per_page,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks"
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
    description="Retrieve detailed information about a specific task, including its log history."
)
async def get_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Get detailed task information by ID.
    
    Args:
        task_id: ID of the task to retrieve
        task_service: Task service instance
        
    Returns:
        Detailed task data including logs
        
    Raises:
        HTTPException: If task is not found
    """
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    return TaskResponse.model_validate(task)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task",
    description="Update an existing task's properties such as title, description, status, or priority."
)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    task_service: TaskService = Depends(get_task_service)
) -> TaskResponse:
    """
    Update an existing task.
    
    Args:
        task_id: ID of the task to update
        task_data: Updated task data
        task_service: Task service instance
        
    Returns:
        Updated task data
        
    Raises:
        HTTPException: If task is not found or update fails
    """
    try:
        task = await task_service.update_task(task_id, task_data)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
        
        return TaskResponse.model_validate(task)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error updating task {task_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update task: {str(e)}"
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Delete a task by its ID. Tasks that are currently being processed cannot be deleted."
)
async def delete_task(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
) -> None:
    """
    Delete a task by ID.
    
    Args:
        task_id: ID of the task to delete
        task_service: Task service instance
        
    Raises:
        HTTPException: If task is not found or cannot be deleted
    """
    try:
        deleted = await task_service.delete_task(task_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with ID {task_id} not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Unexpected error deleting task {task_id}: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete task: {str(e)}"
        )


@router.post(
    "/{task_id}/process",
    response_model=TaskProcessResponse,
    summary="Start background processing",
    description="Submit a task for background processing. The task must be in 'pending' or 'failed' status."
)
async def process_task_endpoint(
    task_id: int,
    task_service: TaskService = Depends(get_task_service)
) -> TaskProcessResponse:
    """
    Start background processing for a task.
    
    Args:
        task_id: ID of the task to process
        task_service: Task service instance
        
    Returns:
        Processing response with status information
        
    Raises:
        HTTPException: If task cannot be processed
    """
    # First verify the task exists and can be processed
    task = await task_service.get_task_by_id(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found"
        )
    
    if not task.can_be_processed():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task with status '{task.status}' cannot be processed. "
                   f"Only tasks with status 'pending' or 'failed' can be processed."
        )
    
    # Attempt to start background processing
    try:
        processing_started = await process_task(task_id)
        
        if not processing_started:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Background processing is currently at capacity. Please try again later."
            )
        
        return TaskProcessResponse(
            task_id=task_id,
            message="Task has been queued for background processing",
            estimated_completion=None  # Could be calculated based on queue length and priority
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start task processing: {str(e)}"
        )


@router.get(
    "/stats/summary",
    response_model=Dict,
    summary="Get task statistics",
    description="Retrieve summary statistics about tasks including counts by status and priority."
)
async def get_task_statistics(
    task_service: TaskService = Depends(get_task_service)
) -> Dict:
    """
    Get task statistics summary.
    
    Args:
        task_service: Task service instance
        
    Returns:
        Dictionary containing task statistics
        
    Raises:
        HTTPException: If statistics retrieval fails
    """
    try:
        stats = await task_service.get_task_statistics()
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve task statistics"
        )


@router.get(
    "/processing/status",
    response_model=Dict,
    summary="Get background processing status",
    description="Retrieve information about currently running background tasks and processing capacity."
)
async def get_background_processing_status() -> Dict:
    """
    Get background processing status.
    
    Returns:
        Dictionary containing processing status information
        
    Raises:
        HTTPException: If status retrieval fails
    """
    try:
        status_info = await get_processing_status()
        return status_info
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve processing status"
        )
    