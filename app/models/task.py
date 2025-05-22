"""
Task and TaskLog database models.

This module defines the SQLAlchemy models for tasks and task logs,
including their relationships and database constraints.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TaskStatus(str, Enum):
    """
    Enumeration of possible task statuses.
    
    This enum defines all valid states a task can be in throughout its lifecycle.
    """
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(int, Enum):
    """
    Enumeration of task priority levels.
    
    Lower numbers indicate higher priority.
    """
    LOW = 3
    MEDIUM = 2
    HIGH = 1
    CRITICAL = 0


class Task(Base):
    """
    Task model representing a task in the system.
    
    This model stores all information about a task including its metadata,
    status, and relationships to task logs.
    
    Attributes:
        id: Primary key identifier
        title: Task title (required)
        description: Detailed task description (optional)
        status: Current task status
        priority: Task priority level
        created_at: Timestamp when task was created
        updated_at: Timestamp when task was last updated
        logs: Related task log entries
    """
    
    __tablename__ = "tasks"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default=TaskStatus.PENDING.value,
        index=True
    )
    priority: Mapped[int] = mapped_column(
        Integer, 
        nullable=False, 
        default=TaskPriority.MEDIUM.value,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    logs: Mapped[List["TaskLog"]] = relationship(
        "TaskLog",
        back_populates="task",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        """String representation of the Task model."""
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    def is_processing(self) -> bool:
        """
        Check if the task is currently being processed.
        
        Returns:
            True if task is in progress, False otherwise
        """
        return self.status == TaskStatus.IN_PROGRESS.value
    
    def is_completed(self) -> bool:
        """
        Check if the task has been completed successfully.
        
        Returns:
            True if task is completed, False otherwise
        """
        return self.status == TaskStatus.COMPLETED.value
    
    def is_failed(self) -> bool:
        """
        Check if the task has failed.
        
        Returns:
            True if task failed, False otherwise
        """
        return self.status == TaskStatus.FAILED.value
    
    def can_be_processed(self) -> bool:
        """
        Check if the task can be processed (started or retried).
        
        Returns:
            True if task can be processed, False otherwise
        """
        return self.status in [TaskStatus.PENDING.value, TaskStatus.FAILED.value]


class TaskLog(Base):
    """
    Task log model for tracking task status changes.
    
    This model maintains an audit trail of all status changes for each task,
    providing visibility into task processing history.
    
    Attributes:
        id: Primary key identifier
        task_id: Foreign key to the associated task
        status: Status that was set
        message: Optional message describing the status change
        created_at: Timestamp when the log entry was created
        task: Related task object
    """
    
    __tablename__ = "task_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(
        Integer, 
        ForeignKey("tasks.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="logs")
    
    def __repr__(self) -> str:
        """String representation of the TaskLog model."""
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, status='{self.status}')>"
    