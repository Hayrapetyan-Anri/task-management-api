"""
Test configuration and fixtures.

This module provides shared test fixtures and configuration
for the test suite, including database setup and client fixtures.
"""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import TestSettings
from app.core.database import Base, get_db
from app.main import create_application
from app.models.task import Task, TaskLog

# Test database URL - using SQLite for faster tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test_db.sqlite"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """
    Create an event loop for the test session.
    
    Yields:
        Event loop for async tests
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session for testing.
    
    This fixture creates a fresh database for each test function,
    ensuring test isolation.
    
    Yields:
        Database session for testing
    """
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with TestSessionLocal() as session:
        yield session
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client(db_session: AsyncSession) -> TestClient:
    """
    Create a test client with database dependency override.
    
    Args:
        db_session: Test database session
        
    Returns:
        FastAPI test client
    """
    app = create_application()
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an async test client with database dependency override.
    
    Args:
        db_session: Test database session
        
    Yields:
        Async HTTP client for testing
    """
    app = create_application()
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as async_test_client:
        yield async_test_client


@pytest_asyncio.fixture
async def sample_task(db_session: AsyncSession) -> Task:
    """
    Create a sample task for testing.
    
    Args:
        db_session: Test database session
        
    Returns:
        Sample task instance
    """
    task = Task(
        title="Test Task",
        description="This is a test task",
        priority=2,
        status="pending"
    )
    
    db_session.add(task)
    await db_session.commit()
    await db_session.refresh(task)
    
    return task


@pytest_asyncio.fixture
async def sample_tasks(db_session: AsyncSession) -> list[Task]:
    """
    Create multiple sample tasks for testing.
    
    Args:
        db_session: Test database session
        
    Returns:
        List of sample task instances
    """
    tasks = [
        Task(
            title="High Priority Task",
            description="This is a high priority task",
            priority=1,
            status="pending"
        ),
        Task(
            title="Medium Priority Task",
            description="This is a medium priority task",
            priority=2,
            status="in_progress"
        ),
        Task(
            title="Low Priority Task",
            description="This is a low priority task",
            priority=3,
            status="completed"
        ),
        Task(
            title="Another Task",
            description="Another test task",
            priority=2,
            status="failed"
        )
    ]
    
    for task in tasks:
        db_session.add(task)
    
    await db_session.commit()
    
    for task in tasks:
        await db_session.refresh(task)
    
    return tasks


@pytest.fixture
def sample_task_data() -> dict:
    """
    Sample task data for API testing.
    
    Returns:
        Dictionary with sample task data
    """
    return {
        "title": "New Test Task",
        "description": "This is a new test task",
        "priority": 2
    }


@pytest.fixture
def sample_task_update_data() -> dict:
    """
    Sample task update data for API testing.
    
    Returns:
        Dictionary with sample task update data
    """
    return {
        "title": "Updated Test Task",
        "description": "This task has been updated",
        "status": "in_progress",
        "priority": 1
    }
