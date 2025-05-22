"""
Unit tests for task service functionality.

This module contains unit tests for the TaskService class,
testing business logic and data operations.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskFilterParams, TaskUpdate
from app.services.task_service import TaskService


class TestTaskService:
    """Test cases for TaskService class."""
    
    @pytest.mark.asyncio
    async def test_create_task(self, db_session: AsyncSession):
        """
        Test task creation.
        
        Args:
            db_session: Test database session
        """
        task_service = TaskService(db_session)
        task_data = TaskCreate(
            title="Test Task",
            description="Test Description",
            priority=2
        )
        
        task = await task_service.create_task(task_data)
        
        assert task.id is not None
        assert task.title == "Test Task"
        assert task.description == "Test Description"
        assert task.priority == 2
        assert task.status == TaskStatus.PENDING.value
        assert task.created_at is not None
        assert task.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_get_task_by_id(self, db_session: AsyncSession, sample_task: Task):
        """
        Test retrieving a task by ID.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        
        retrieved_task = await task_service.get_task_by_id(sample_task.id)
        
        assert retrieved_task is not None
        assert retrieved_task.id == sample_task.id
        assert retrieved_task.title == sample_task.title
    
    @pytest.mark.asyncio
    async def test_get_task_by_id_not_found(self, db_session: AsyncSession):
        """
        Test retrieving a non-existent task.
        
        Args:
            db_session: Test database session
        """
        task_service = TaskService(db_session)
        
        task = await task_service.get_task_by_id(99999)
        
        assert task is None
    
    @pytest.mark.asyncio
    async def test_get_tasks_no_filters(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test retrieving all tasks without filters.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        filters = TaskFilterParams(page=1, per_page=10)
        
        tasks, total_count = await task_service.get_tasks(filters)
        
        assert len(tasks) == 4
        assert total_count == 4
        # Tasks should be ordered by priority (asc) then created_at (desc)
        assert tasks[0].priority == 1  # High priority first
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_status_filter(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test retrieving tasks with status filter.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        filters = TaskFilterParams(status="pending", page=1, per_page=10)
        
        tasks, total_count = await task_service.get_tasks(filters)
        
        assert len(tasks) == 1
        assert total_count == 1
        assert all(task.status == "pending" for task in tasks)
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_priority_filter(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test retrieving tasks with priority filter.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        filters = TaskFilterParams(priority=2, page=1, per_page=10)
        
        tasks, total_count = await task_service.get_tasks(filters)
        
        assert len(tasks) == 2
        assert total_count == 2
        assert all(task.priority == 2 for task in tasks)
    
    @pytest.mark.asyncio
    async def test_get_tasks_with_title_filter(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test retrieving tasks with title filter.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        filters = TaskFilterParams(title="High", page=1, per_page=10)
        
        tasks, total_count = await task_service.get_tasks(filters)
        
        assert len(tasks) == 1
        assert total_count == 1
        assert "High" in tasks[0].title
    
    @pytest.mark.asyncio
    async def test_get_tasks_pagination(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test task pagination.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        filters = TaskFilterParams(page=1, per_page=2)
        
        tasks, total_count = await task_service.get_tasks(filters)
        
        assert len(tasks) == 2
        assert total_count == 4
        
        # Test second page
        filters = TaskFilterParams(page=2, per_page=2)
        tasks, total_count = await task_service.get_tasks(filters)
        
        assert len(tasks) == 2
        assert total_count == 4
    
    @pytest.mark.asyncio
    async def test_update_task(self, db_session: AsyncSession, sample_task: Task):
        """
        Test task update.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        update_data = TaskUpdate(
            title="Updated Title",
            description="Updated Description",
            status="in_progress",
            priority=1
        )
        
        updated_task = await task_service.update_task(sample_task.id, update_data)
        
        assert updated_task is not None
        assert updated_task.title == "Updated Title"
        assert updated_task.description == "Updated Description"
        assert updated_task.status == "in_progress"
        assert updated_task.priority == 1
    
    @pytest.mark.asyncio
    async def test_update_task_partial(self, db_session: AsyncSession, sample_task: Task):
        """
        Test partial task update.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        original_description = sample_task.description
        update_data = TaskUpdate(title="New Title Only")
        
        updated_task = await task_service.update_task(sample_task.id, update_data)
        
        assert updated_task is not None
        assert updated_task.title == "New Title Only"
        assert updated_task.description == original_description  # Unchanged
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, db_session: AsyncSession):
        """
        Test updating a non-existent task.
        
        Args:
            db_session: Test database session
        """
        task_service = TaskService(db_session)
        update_data = TaskUpdate(title="New Title")
        
        updated_task = await task_service.update_task(99999, update_data)
        
        assert updated_task is None
    
    @pytest.mark.asyncio
    async def test_delete_task(self, db_session: AsyncSession, sample_task: Task):
        """
        Test task deletion.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        task_id = sample_task.id
        
        deleted = await task_service.delete_task(task_id)
        
        assert deleted is True
        
        # Verify task is deleted
        retrieved_task = await task_service.get_task_by_id(task_id)
        assert retrieved_task is None
    
    @pytest.mark.asyncio
    async def test_delete_task_not_found(self, db_session: AsyncSession):
        """
        Test deleting a non-existent task.
        
        Args:
            db_session: Test database session
        """
        task_service = TaskService(db_session)
        
        deleted = await task_service.delete_task(99999)
        
        assert deleted is False
    
    @pytest.mark.asyncio
    async def test_delete_processing_task(self, db_session: AsyncSession, sample_task: Task):
        """
        Test deleting a task that is being processed.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        
        # Set task to processing
        sample_task.status = TaskStatus.IN_PROGRESS.value
        await db_session.commit()
        
        with pytest.raises(ValueError, match="Cannot delete a task that is currently being processed"):
            await task_service.delete_task(sample_task.id)
    
    @pytest.mark.asyncio
    async def test_start_task_processing(self, db_session: AsyncSession, sample_task: Task):
        """
        Test starting task processing.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        
        task = await task_service.start_task_processing(sample_task.id)
        
        assert task is not None
        assert task.status == TaskStatus.IN_PROGRESS.value
    
    @pytest.mark.asyncio
    async def test_start_task_processing_invalid_status(self, db_session: AsyncSession, sample_task: Task):
        """
        Test starting processing for a task with invalid status.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        
        # Set task to completed
        sample_task.status = TaskStatus.COMPLETED.value
        await db_session.commit()
        
        with pytest.raises(ValueError, match="cannot be processed"):
            await task_service.start_task_processing(sample_task.id)
    
    @pytest.mark.asyncio
    async def test_complete_task_processing_success(self, db_session: AsyncSession, sample_task: Task):
        """
        Test completing task processing successfully.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        
        task = await task_service.complete_task_processing(
            sample_task.id, 
            success=True, 
            message="Task completed successfully"
        )
        
        assert task is not None
        assert task.status == TaskStatus.COMPLETED.value
    
    @pytest.mark.asyncio
    async def test_complete_task_processing_failure(self, db_session: AsyncSession, sample_task: Task):
        """
        Test completing task processing with failure.
        
        Args:
            db_session: Test database session
            sample_task: Sample task fixture
        """
        task_service = TaskService(db_session)
        
        task = await task_service.complete_task_processing(
            sample_task.id, 
            success=False, 
            message="Task failed"
        )
        
        assert task is not None
        assert task.status == TaskStatus.FAILED.value
    
    @pytest.mark.asyncio
    async def test_get_task_statistics(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test getting task statistics.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        
        stats = await task_service.get_task_statistics()
        
        assert stats["total_tasks"] == 4
        assert "by_status" in stats
        assert "by_priority" in stats
        assert stats["by_status"]["pending"] == 1
        assert stats["by_status"]["in_progress"] == 1
        assert stats["by_status"]["completed"] == 1
        assert stats["by_status"]["failed"] == 1
    
    @pytest.mark.asyncio
    async def test_get_tasks_for_processing(self, db_session: AsyncSession, sample_tasks: list[Task]):
        """
        Test getting tasks ready for processing.
        
        Args:
            db_session: Test database session
            sample_tasks: Sample tasks fixture
        """
        task_service = TaskService(db_session)
        
        tasks = await task_service.get_tasks_for_processing(limit=10)
        
        # Should return pending and failed tasks only
        assert len(tasks) == 2
        processable_statuses = [TaskStatus.PENDING.value, TaskStatus.FAILED.value]
        for task in tasks:
            assert task.status in processable_statuses
        
        # Should be ordered by priority (high priority first)
        assert tasks[0].priority <= tasks[1].priority
        