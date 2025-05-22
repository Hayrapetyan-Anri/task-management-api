"""
Integration tests for the API endpoints.

This module contains integration tests for all API endpoints,
testing the complete request/response cycle.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.models.task import Task


class TestTaskAPI:
    """Integration tests for task API endpoints."""
    
    def test_health_check(self, client: TestClient):
        """
        Test health check endpoint.
        
        Args:
            client: FastAPI test client
        """
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "version" in data
    
    def test_root_endpoint(self, client: TestClient):
        """
        Test root endpoint.
        
        Args:
            client: FastAPI test client
        """
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs_url" in data
    
    def test_create_task(self, client: TestClient, sample_task_data: dict):
        """
        Test task creation endpoint.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        response = client.post("/api/v1/tasks/", json=sample_task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["priority"] == sample_task_data["priority"]
        assert data["status"] == "pending"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_task_invalid_data(self, client: TestClient):
        """
        Test task creation with invalid data.
        
        Args:
            client: FastAPI test client
        """
        invalid_data = {
            "title": "",  # Empty title
            "priority": 5  # Invalid priority
        }
        
        response = client.post("/api/v1/tasks/", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_task(self, client: TestClient, sample_task_data: dict):
        """
        Test getting a specific task.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        # First create a task
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Then get it
        response = client.get(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == sample_task_data["title"]
        assert "logs" in data
    
    def test_get_task_not_found(self, client: TestClient):
        """
        Test getting a non-existent task.
        
        Args:
            client: FastAPI test client
        """
        response = client.get("/api/v1/tasks/99999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_list_tasks_empty(self, client: TestClient):
        """
        Test listing tasks when none exist.
        
        Args:
            client: FastAPI test client
        """
        response = client.get("/api/v1/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 20
    
    def test_list_tasks_with_data(self, client: TestClient):
        """
        Test listing tasks with existing data.
        
        Args:
            client: FastAPI test client
        """
        # Create some tasks first
        task_data = {
            "title": "Test Task 1",
            "description": "First test task",
            "priority": 1
        }
        client.post("/api/v1/tasks/", json=task_data)
        
        task_data["title"] = "Test Task 2"
        task_data["priority"] = 2
        client.post("/api/v1/tasks/", json=task_data)
        
        # List tasks
        response = client.get("/api/v1/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 2
        # Should be ordered by priority
        assert data["items"][0]["priority"] <= data["items"][1]["priority"]
    
    def test_list_tasks_with_filters(self, client: TestClient):
        """
        Test listing tasks with filters.
        
        Args:
            client: FastAPI test client
        """
        # Create tasks with different properties
        high_priority_task = {
            "title": "High Priority Task",
            "description": "Important task",
            "priority": 1
        }
        low_priority_task = {
            "title": "Low Priority Task",
            "description": "Less important task",
            "priority": 3
        }
        
        client.post("/api/v1/tasks/", json=high_priority_task)
        client.post("/api/v1/tasks/", json=low_priority_task)
        
        # Filter by priority
        response = client.get("/api/v1/tasks/?priority=1")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["priority"] == 1
        
        # Filter by title
        response = client.get("/api/v1/tasks/?title=High")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert "High" in data["items"][0]["title"]
    
    def test_list_tasks_pagination(self, client: TestClient):
        """
        Test task list pagination.
        
        Args:
            client: FastAPI test client
        """
        # Create multiple tasks
        for i in range(5):
            task_data = {
                "title": f"Task {i}",
                "description": f"Description {i}",
                "priority": 2
            }
            client.post("/api/v1/tasks/", json=task_data)
        
        # Get first page
        response = client.get("/api/v1/tasks/?page=1&per_page=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["per_page"] == 2
        assert data["pages"] == 3
        assert data["has_next"] is True
        assert data["has_prev"] is False
        
        # Get second page
        response = client.get("/api/v1/tasks/?page=2&per_page=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["page"] == 2
        assert data["has_next"] is True
        assert data["has_prev"] is True
    
    def test_update_task(self, client: TestClient, sample_task_data: dict, sample_task_update_data: dict):
        """
        Test task update endpoint.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
            sample_task_update_data: Sample update data fixture
        """
        # Create a task first
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Update it
        response = client.put(f"/api/v1/tasks/{task_id}", json=sample_task_update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == sample_task_update_data["title"]
        assert data["description"] == sample_task_update_data["description"]
        assert data["status"] == sample_task_update_data["status"]
        assert data["priority"] == sample_task_update_data["priority"]
    
    def test_update_task_partial(self, client: TestClient, sample_task_data: dict):
        """
        Test partial task update.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        # Create a task first
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        original_description = create_response.json()["description"]
        
        # Partial update (only title)
        update_data = {"title": "Updated Title Only"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title Only"
        assert data["description"] == original_description  # Unchanged
    
    def test_update_task_not_found(self, client: TestClient):
        """
        Test updating a non-existent task.
        
        Args:
            client: FastAPI test client
        """
        update_data = {"title": "New Title"}
        response = client.put("/api/v1/tasks/99999", json=update_data)
        
        assert response.status_code == 404
    
    def test_update_task_invalid_status(self, client: TestClient, sample_task_data: dict):
        """
        Test updating task with invalid status.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        # Create a task first
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Try to update with invalid status
        update_data = {"status": "invalid_status"}
        response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_delete_task(self, client: TestClient, sample_task_data: dict):
        """
        Test task deletion endpoint.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        # Create a task first
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/v1/tasks/{task_id}")
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404
    
    def test_delete_task_not_found(self, client: TestClient):
        """
        Test deleting a non-existent task.
        
        Args:
            client: FastAPI test client
        """
        response = client.delete("/api/v1/tasks/99999")
        
        assert response.status_code == 404
    
    def test_process_task(self, client: TestClient, sample_task_data: dict):
        """
        Test task processing endpoint.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        # Create a task first
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Start processing
        response = client.post(f"/api/v1/tasks/{task_id}/process")
        
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert "message" in data
    
    def test_process_task_not_found(self, client: TestClient):
        """
        Test processing a non-existent task.
        
        Args:
            client: FastAPI test client
        """
        response = client.post("/api/v1/tasks/99999/process")
        
        assert response.status_code == 404
    
    def test_process_task_invalid_status(self, client: TestClient, sample_task_data: dict):
        """
        Test processing a task with invalid status.
        
        Args:
            client: FastAPI test client
            sample_task_data: Sample task data fixture
        """
        # Create and complete a task
        create_response = client.post("/api/v1/tasks/", json=sample_task_data)
        task_id = create_response.json()["id"]
        
        # Set status to completed
        update_data = {"status": "completed"}
        client.put(f"/api/v1/tasks/{task_id}", json=update_data)
        
        # Try to process completed task
        response = client.post(f"/api/v1/tasks/{task_id}/process")
        
        assert response.status_code == 400
        assert "cannot be processed" in response.json()["detail"]
    
    def test_get_task_statistics(self, client: TestClient):
        """
        Test task statistics endpoint.
        
        Args:
            client: FastAPI test client
        """
        # Create some tasks with different statuses
        tasks_data = [
            {"title": "Task 1", "priority": 1},
            {"title": "Task 2", "priority": 2},
            {"title": "Task 3", "priority": 3},
        ]
        
        for task_data in tasks_data:
            client.post("/api/v1/tasks/", json=task_data)
        
        # Get statistics
        response = client.get("/api/v1/tasks/stats/summary")
        
        assert response.status_code == 200
        data = response.json()
        assert "total_tasks" in data
        assert "by_status" in data
        assert "by_priority" in data
        assert data["total_tasks"] == 3
    
    def test_get_processing_status(self, client: TestClient):
        """
        Test processing status endpoint.
        
        Args:
            client: FastAPI test client
        """
        response = client.get("/api/v1/tasks/processing/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "active_count" in data
        assert "max_concurrent" in data
        assert "available_slots" in data
        assert "processing_tasks" in data


@pytest.mark.asyncio
class TestAsyncTaskAPI:
    """Async integration tests for task API endpoints."""
    
    async def test_create_task_async(self, async_client: AsyncClient, sample_task_data: dict):
        """
        Test async task creation.
        
        Args:
            async_client: Async HTTP client
            sample_task_data: Sample task data fixture
        """
        response = await async_client.post("/api/v1/tasks/", json=sample_task_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
    
    async def test_list_tasks_async(self, async_client: AsyncClient):
        """
        Test async task listing.
        
        Args:
            async_client: Async HTTP client
        """
        response = await async_client.get("/api/v1/tasks/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        