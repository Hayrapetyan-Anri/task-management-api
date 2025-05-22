"""
Database base imports.

This module centralizes all database-related imports to ensure proper
model registration with Alembic for migrations.
"""

from app.core.database import Base
from app.models.task import Task, TaskLog

# Import all models here to ensure they are registered with Base
# This is important for Alembic to detect model changes for migrations

__all__ = ["Base", "Task", "TaskLog"]