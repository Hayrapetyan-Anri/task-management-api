"""
Task service module for business logic operations.

This module contains the core business logic for task operations,
including CRUD operations, validation, and task state management.
"""

from typing import List, Optional, Tuple
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskLog, TaskStatus
from app.schemas.task import TaskCreate, TaskFilterParams, TaskUpdate


class TaskService:
    """
    Service class for task-related business operations.
    
    This class encapsulates all business logic related to task management,
    providing a clean interface between the API layer and data layer.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize the task service.
        
        Args:
            db: Database session for performing operations
        """
        self.db = db
    
    async def create_task(self, task_data: TaskCreate) -> Task:
        """
        Create a new task.
        
        Args:
            task_data: Task creation data
            
        Returns:
            Created task instance
            
        Raises:
            ValueError: If task data is invalid
        """
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            status=TaskStatus.PENDING.value
        )
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        # Create initial log entry
        await self._create_task_log(
            task.id, 
            TaskStatus.PENDING.value, 
            "Task created"
        )
        
        return task
    
    async def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        Retrieve a task by its ID.
        
        Args:
            task_id: The ID of the task to retrieve
            
        Returns:
            Task instance if found, None otherwise
        """
        query = (
            select(Task)
            .options(selectinload(Task.logs))
            .where(Task.id == task_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_tasks(
        self, 
        filters: TaskFilterParams
    ) -> Tuple[List[Task], int]:
        """
        Retrieve tasks with filtering and pagination.
        
        Args:
            filters: Filter and pagination parameters
            
        Returns:
            Tuple of (tasks list, total count)
        """
        # Build base query
        query = select(Task)
        count_query = select(func.count(Task.id))
        
        # Apply filters
        conditions = []
        
        if filters.status:
            conditions.append(Task.status == filters.status)
        
        if filters.priority is not None:
            conditions.append(Task.priority == filters.priority)
        
        if filters.title:
            conditions.append(
                Task.title.ilike(f"%{filters.title}%")
            )
        
        if conditions:
            filter_condition = and_(*conditions)
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        # Get total count
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar_one()
        
        # Apply pagination and ordering
        query = (
            query
            .order_by(Task.priority.asc(), Task.created_at.desc())
            .offset((filters.page - 1) * filters.per_page)
            .limit(filters.per_page)
        )
        
        # Execute query
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        return list(tasks), total_count
    
    async def update_task(
        self, 
        task_id: int, 
        task_data: TaskUpdate
    ) -> Optional[Task]:
        """
        Update an existing task.
        
        Args:
            task_id: ID of the task to update
            task_data: Updated task data
            
        Returns:
            Updated task instance if found, None otherwise
            
        Raises:
            ValueError: If trying to update a completed task's non-status fields
        """
        try:
            task = await self.get_task_by_id(task_id)
            if not task:
                return None
            
            # Track what changed for logging
            changes = []
            old_status = task.status
            
            # Update fields
            update_data = task_data.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if hasattr(task, field) and getattr(task, field) != value:
                    old_value = getattr(task, field)
                    setattr(task, field, value)
                    changes.append(f"{field}: {old_value} -> {value}")
            
            if not changes:
                return task
            
            await self.db.commit()
            await self.db.refresh(task)
            
            # Log status change if status was updated
            if task.status != old_status:
                await self._create_task_log(
                    task.id,
                    task.status,
                    f"Status changed from {old_status} to {task.status}"
                )
            
            # Log other changes
            if len(changes) > 1 or (len(changes) == 1 and "status" not in changes[0]):
                await self._create_task_log(
                    task.id,
                    task.status,
                    f"Task updated: {', '.join(changes)}"
                )
            
            return task
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def delete_task(self, task_id: int) -> bool:
        """
        Delete a task by ID.
        
        Args:
            task_id: ID of the task to delete
            
        Returns:
            True if task was deleted, False if not found
            
        Raises:
            ValueError: If trying to delete a task that is currently processing
        """
        try:
            task = await self.get_task_by_id(task_id)
            if not task:
                return False
            
            if task.is_processing():
                raise ValueError("Cannot delete a task that is currently being processed")
            
            await self.db.delete(task)
            await self.db.commit()
            return True
        except ValueError:
            # Re-raise ValueError for business logic errors
            raise
        except Exception as e:
            await self.db.rollback()
            return False
    
    async def start_task_processing(self, task_id: int) -> Optional[Task]:
        """
        Mark a task as starting processing.
        
        Args:
            task_id: ID of the task to start processing
            
        Returns:
            Updated task instance if found, None otherwise
            
        Raises:
            ValueError: If task cannot be processed
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            return None
        
        if not task.can_be_processed():
            raise ValueError(
                f"Task with status '{task.status}' cannot be processed. "
                f"Only tasks with status 'pending' or 'failed' can be processed."
            )
        
        task.status = TaskStatus.IN_PROGRESS.value
        await self.db.commit()
        await self.db.refresh(task)
        
        await self._create_task_log(
            task.id,
            TaskStatus.IN_PROGRESS.value,
            "Task processing started"
        )
        
        return task
    
    async def complete_task_processing(
        self, 
        task_id: int, 
        success: bool = True,
        message: Optional[str] = None
    ) -> Optional[Task]:
        """
        Mark a task as completed or failed after processing.
        
        Args:
            task_id: ID of the task to complete
            success: Whether the processing was successful
            message: Optional completion message
            
        Returns:
            Updated task instance if found, None otherwise
        """
        task = await self.get_task_by_id(task_id)
        if not task:
            return None
        
        new_status = TaskStatus.COMPLETED.value if success else TaskStatus.FAILED.value
        task.status = new_status
        
        await self.db.commit()
        await self.db.refresh(task)
        
        log_message = message or (
            "Task completed successfully" if success else "Task processing failed"
        )
        
        await self._create_task_log(task.id, new_status, log_message)
        
        return task
    
    async def get_task_statistics(self) -> dict:
        """
        Get task statistics summary.
        
        Returns:
            Dictionary containing task counts by status and priority
        """
        # Count by status
        status_query = (
            select(Task.status, func.count(Task.id))
            .group_by(Task.status)
        )
        status_result = await self.db.execute(status_query)
        status_counts = dict(status_result.all())
        
        # Count by priority
        priority_query = (
            select(Task.priority, func.count(Task.id))
            .group_by(Task.priority)
        )
        priority_result = await self.db.execute(priority_query)
        priority_counts = dict(priority_result.all())
        
        # Total count
        total_query = select(func.count(Task.id))
        total_result = await self.db.execute(total_query)
        total_count = total_result.scalar_one()
        
        return {
            "total_tasks": total_count,
            "by_status": status_counts,
            "by_priority": priority_counts
        }
    
    async def get_tasks_for_processing(self, limit: int = 10) -> List[Task]:
        """
        Get tasks that are ready for processing.
        
        Args:
            limit: Maximum number of tasks to return
            
        Returns:
            List of tasks ready for processing
        """
        query = (
            select(Task)
            .where(
                or_(
                    Task.status == TaskStatus.PENDING.value,
                    Task.status == TaskStatus.FAILED.value
                )
            )
            .order_by(Task.priority.asc(), Task.created_at.asc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def _create_task_log(
        self, 
        task_id: int, 
        status: str, 
        message: str
    ) -> TaskLog:
        """
        Create a task log entry.
        
        Args:
            task_id: ID of the associated task
            status: Status to log
            message: Log message
            
        Returns:
            Created task log instance
        """
        log = TaskLog(
            task_id=task_id,
            status=status,
            message=message
        )
        
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)
        
        return log
    