"""
Pydantic schemas for task-related API operations.

This module defines the request and response schemas for task operations,
including validation rules and data transformation logic.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """
    Base schema for task data.
    
    Contains common fields shared between different task schemas.
    """
    
    title: str = Field(..., min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    priority: int = Field(
        default=TaskPriority.MEDIUM.value,
        ge=TaskPriority.CRITICAL.value,
        le=TaskPriority.LOW.value,
        description="Task priority (0=Critical, 1=High, 2=Medium, 3=Low)"
    )


class TaskCreate(TaskBase):
    """
    Schema for creating a new task.
    
    Inherits from TaskBase and includes validation for task creation.
    """
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """
        Validate and clean the task title.
        
        Args:
            v: The title string to validate
            
        Returns:
            Cleaned title string
            
        Raises:
            ValueError: If title is empty or only whitespace
        """
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        return v.strip()
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean the task description.
        
        Args:
            v: The description string to validate
            
        Returns:
            Cleaned description string or None
        """
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task.
    
    All fields are optional to support partial updates.
    """
    
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(None, max_length=2000, description="Task description")
    status: Optional[str] = Field(None, description="Task status")
    priority: Optional[int] = Field(
        None,
        ge=TaskPriority.CRITICAL.value,
        le=TaskPriority.LOW.value,
        description="Task priority"
    )
    
    @field_validator("title")
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean the task title for updates.
        
        Args:
            v: The title string to validate
            
        Returns:
            Cleaned title string or None
            
        Raises:
            ValueError: If title is provided but empty or only whitespace
        """
        if v is not None:
            if not v.strip():
                raise ValueError("Title cannot be empty")
            return v.strip()
        return v
    
    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate task status.
        
        Args:
            v: The status string to validate
            
        Returns:
            Validated status string or None
            
        Raises:
            ValueError: If status is not a valid TaskStatus value
        """
        if v is not None:
            valid_statuses = [status.value for status in TaskStatus]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate and clean the task description for updates.
        
        Args:
            v: The description string to validate
            
        Returns:
            Cleaned description string or None
        """
        if v is not None:
            v = v.strip()
            return v if v else None
        return v


class TaskLogResponse(BaseModel):
    """
    Schema for task log response data.
    
    Represents a single task log entry in API responses.
    """
    
    id: int = Field(..., description="Log entry ID")
    task_id: int = Field(..., description="Associated task ID")
    status: str = Field(..., description="Status that was logged")
    message: Optional[str] = Field(None, description="Log message")
    created_at: datetime = Field(..., description="When the log entry was created")
    
    model_config = ConfigDict(from_attributes=True)


class TaskResponse(TaskBase):
    """
    Schema for task response data.
    
    Represents a complete task object in API responses, including
    computed fields and relationships.
    """
    
    id: int = Field(..., description="Task ID")
    status: str = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="When the task was created")
    updated_at: datetime = Field(..., description="When the task was last updated")
    logs: List[TaskLogResponse] = Field(default_factory=list, description="Task log entries")
    
    model_config = ConfigDict(from_attributes=True)


class TaskSummaryResponse(BaseModel):
    """
    Schema for task summary response (without logs).
    
    Used for listing tasks where full log history is not needed.
    """
    
    id: int = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    status: str = Field(..., description="Current task status")
    priority: int = Field(..., description="Task priority")
    created_at: datetime = Field(..., description="When the task was created")
    updated_at: datetime = Field(..., description="When the task was last updated")
    
    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    """
    Schema for paginated task list response.
    
    Contains pagination metadata along with the list of tasks.
    """
    
    items: List[TaskSummaryResponse] = Field(..., description="List of tasks")
    total: int = Field(..., description="Total number of tasks matching the query")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class TaskProcessResponse(BaseModel):
    """
    Schema for task processing response.
    
    Returned when a task is submitted for background processing.
    """
    
    task_id: int = Field(..., description="ID of the task being processed")
    message: str = Field(..., description="Processing status message")
    estimated_completion: Optional[datetime] = Field(
        None, 
        description="Estimated completion time"
    )


class TaskFilterParams(BaseModel):
    """
    Schema for task filtering parameters.
    
    Used to validate query parameters for task listing endpoints.
    """
    
    status: Optional[str] = Field(None, description="Filter by task status")
    priority: Optional[int] = Field(None, description="Filter by task priority")
    title: Optional[str] = Field(None, description="Filter by title (partial match)")
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @field_validator("status")
    @classmethod
    def validate_status_filter(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate status filter parameter.
        
        Args:
            v: The status string to validate
            
        Returns:
            Validated status string or None
            
        Raises:
            ValueError: If status is not a valid TaskStatus value
        """
        if v is not None:
            valid_statuses = [status.value for status in TaskStatus]
            if v not in valid_statuses:
                raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        return v
    
    @field_validator("priority")
    @classmethod
    def validate_priority_filter(cls, v: Optional[int]) -> Optional[int]:
        """
        Validate priority filter parameter.
        
        Args:
            v: The priority value to validate
            
        Returns:
            Validated priority value or None
            
        Raises:
            ValueError: If priority is not a valid TaskPriority value
        """
        if v is not None:
            valid_priorities = [priority.value for priority in TaskPriority]
            if v not in valid_priorities:
                raise ValueError(f"Priority must be one of: {', '.join(map(str, valid_priorities))}")
        return v
    