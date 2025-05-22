"""
Background task processing service.

This module handles the execution of background tasks using asyncio,
providing task queue management and processing capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.services.task_service import TaskService

logger = logging.getLogger(__name__)


class BackgroundTaskProcessor:
    """
    Background task processor for handling long-running tasks.
    
    This class manages a queue of tasks and processes them asynchronously,
    with support for concurrency limits and error handling.
    """
    
    def __init__(self):
        """Initialize the background task processor."""
        self._processing_tasks: Set[int] = set()
        self._task_futures: Dict[int, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
        self._max_concurrent_tasks = settings.MAX_CONCURRENT_TASKS
    
    async def process_task(self, task_id: int) -> bool:
        """
        Process a single task by ID.
        
        Args:
            task_id: ID of the task to process
            
        Returns:
            True if task was successfully queued for processing, False otherwise
        """
        if task_id in self._processing_tasks:
            logger.warning(f"Task {task_id} is already being processed")
            return False
        
        if len(self._processing_tasks) >= self._max_concurrent_tasks:
            logger.warning(f"Maximum concurrent tasks reached ({self._max_concurrent_tasks})")
            return False
        
        # Start processing the task
        future = asyncio.create_task(self._execute_task(task_id))
        self._task_futures[task_id] = future
        self._processing_tasks.add(task_id)
        
        logger.info(f"Started processing task {task_id}")
        return True
    
    async def _execute_task(self, task_id: int) -> None:
        """
        Execute a single task with error handling.
        
        Args:
            task_id: ID of the task to execute
        """
        async with self._get_db_session() as db:
            task_service = TaskService(db)
            
            try:
                # Start the task
                task = await task_service.start_task_processing(task_id)
                if not task:
                    logger.error(f"Task {task_id} not found")
                    return
                
                logger.info(f"Processing task {task_id}: {task.title}")
                
                # Simulate task processing based on priority
                processing_time = self._calculate_processing_time(task.priority)
                
                # Perform the actual task work
                success = await self._perform_task_work(task_id, processing_time)
                
                # Complete the task
                completion_message = (
                    f"Task completed successfully in {processing_time} seconds"
                    if success else
                    f"Task failed after {processing_time} seconds"
                )
                
                await task_service.complete_task_processing(
                    task_id, 
                    success=success,
                    message=completion_message
                )
                
                logger.info(f"Task {task_id} {'completed' if success else 'failed'}")
                
            except Exception as e:
                logger.error(f"Error processing task {task_id}: {str(e)}")
                try:
                    await task_service.complete_task_processing(
                        task_id,
                        success=False,
                        message=f"Task failed with error: {str(e)}"
                    )
                except Exception as completion_error:
                    logger.error(f"Error completing failed task {task_id}: {str(completion_error)}")
            
            finally:
                # Clean up
                self._processing_tasks.discard(task_id)
                self._task_futures.pop(task_id, None)
    
    async def _perform_task_work(self, task_id: int, processing_time: int) -> bool:
        """
        Perform the actual work for a task.
        
        This is a simulation of task processing. In a real application,
        this would contain the actual business logic for the task.
        
        Args:
            task_id: ID of the task being processed
            processing_time: Time to simulate processing
            
        Returns:
            True if task succeeds, False if it fails
        """
        try:
            # Simulate processing with periodic status updates
            chunk_size = max(1, processing_time // 5)  # Update status every 20% of processing time
            
            for i in range(0, processing_time, chunk_size):
                if self._shutdown_event.is_set():
                    logger.info(f"Task {task_id} interrupted due to shutdown")
                    return False
                
                await asyncio.sleep(min(chunk_size, processing_time - i))
                progress = min(100, ((i + chunk_size) / processing_time) * 100)
                logger.debug(f"Task {task_id} progress: {progress:.1f}%")
            
            # Simulate occasional failures (10% failure rate)
            import random
            return random.random() > 0.1
            
        except asyncio.CancelledError:
            logger.info(f"Task {task_id} was cancelled")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in task {task_id}: {str(e)}")
            return False
    
    def _calculate_processing_time(self, priority: int) -> int:
        """
        Calculate processing time based on task priority.
        
        Args:
            priority: Task priority (0=Critical, 1=High, 2=Medium, 3=Low)
            
        Returns:
            Processing time in seconds
        """
        # Higher priority tasks get processed faster
        base_time = 5
        priority_multiplier = {
            0: 0.5,  # Critical: 2.5 seconds
            1: 0.8,  # High: 4 seconds
            2: 1.0,  # Medium: 5 seconds
            3: 1.5,  # Low: 7.5 seconds
        }
        
        return int(base_time * priority_multiplier.get(priority, 1.0))
    
    async def get_processing_status(self) -> Dict[str, any]:
        """
        Get current processing status.
        
        Returns:
            Dictionary containing processing statistics
        """
        return {
            "processing_tasks": list(self._processing_tasks),
            "active_count": len(self._processing_tasks),
            "max_concurrent": self._max_concurrent_tasks,
            "available_slots": self._max_concurrent_tasks - len(self._processing_tasks)
        }
    
    async def stop_task(self, task_id: int) -> bool:
        """
        Stop processing a specific task.
        
        Args:
            task_id: ID of the task to stop
            
        Returns:
            True if task was stopped, False if not found or already completed
        """
        if task_id not in self._task_futures:
            return False
        
        future = self._task_futures[task_id]
        future.cancel()
        
        try:
            await future
        except asyncio.CancelledError:
            pass
        
        logger.info(f"Stopped processing task {task_id}")
        return True
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the task processor.
        
        Waits for all currently processing tasks to complete or timeout.
        """
        logger.info("Shutting down background task processor...")
        self._shutdown_event.set()
        
        if self._task_futures:
            logger.info(f"Waiting for {len(self._task_futures)} tasks to complete...")
            
            # Wait for tasks to complete with a timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*self._task_futures.values(), return_exceptions=True),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                logger.warning("Timeout waiting for tasks to complete, cancelling remaining tasks")
                for future in self._task_futures.values():
                    future.cancel()
        
        self._processing_tasks.clear()
        self._task_futures.clear()
        logger.info("Background task processor shutdown complete")
    
    @asynccontextmanager
    async def _get_db_session(self):
        """
        Get a database session for task processing.
        
        Yields:
            AsyncSession: Database session
        """
        async with AsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global background task processor instance
background_processor = BackgroundTaskProcessor()


async def process_task(task_id: int) -> bool:
    """
    Convenience function to process a task using the global processor.
    
    Args:
        task_id: ID of the task to process
        
    Returns:
        True if task was successfully queued for processing, False otherwise
    """
    return await background_processor.process_task(task_id)


async def get_processing_status() -> Dict[str, any]:
    """
    Get current processing status from the global processor.
    
    Returns:
        Dictionary containing processing statistics
    """
    return await background_processor.get_processing_status()


async def stop_task_processing(task_id: int) -> bool:
    """
    Stop processing a specific task using the global processor.
    
    Args:
        task_id: ID of the task to stop
        
    Returns:
        True if task was stopped, False if not found
    """
    return await background_processor.stop_task(task_id)


async def shutdown_processor() -> None:
    """
    Shutdown the global background task processor.
    """
    await background_processor.shutdown()
    