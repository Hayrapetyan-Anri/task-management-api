"""
Database configuration and session management.

This module provides database connectivity, session management, and
base database utilities for the Task Management API.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool

from app.core.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DATABASE_ECHO,
    future=True,
    poolclass=NullPool if settings.ENV == "testing" else None,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create declarative base for SQLAlchemy models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    This function provides a database session for FastAPI dependency injection.
    It ensures proper session cleanup after each request.
    
    Yields:
        AsyncSession: Database session instance
        
    Example:
        ```python
        @app.get("/tasks")
        async def get_tasks(db: AsyncSession = Depends(get_db)):
            # Use db session here
            pass
        ```
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables() -> None:
    """
    Create database tables.
    
    This function creates all database tables defined by SQLAlchemy models.
    Used primarily for testing or initial setup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_and_tables() -> None:
    """
    Drop all database tables.
    
    This function drops all database tables. Used primarily for testing cleanup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        