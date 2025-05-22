# Task Management API

A FastAPI application for managing tasks with background processing capabilities.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Async Database Operations**: SQLAlchemy with async support and PostgreSQL
- **Background Task Processing**: Async task queue with concurrent processing
- **Comprehensive API**: Full CRUD operations with filtering and pagination
- **Database Migrations**: Alembic for schema version control
- **Testing Suite**: Unit and integration tests with pytest
- **Docker Support**: Containerized application with docker-compose

## Quick Start

### Prerequisites

- Docker and Docker Compose

### Running the Application

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Hayrapetyan-Anri/task-management-api
   cd task-management-api
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and change SECRET_KEY and passwords
   ```

3. **Start the services:**
   ```bash
   docker-compose up --build
   ```

4. **Run database migrations:**
   ```bash
   docker-compose exec api alembic revision --autogenerate -m "Initial migration"
   docker-compose exec api alembic upgrade head
   ```

5. **Access the application:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/api/v1/docs

### Testing

```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app
```

## API Endpoints

- `POST /api/v1/tasks/` - Create a new task
- `GET /api/v1/tasks/` - List tasks (with filtering and pagination)
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PUT /api/v1/tasks/{task_id}` - Update task
- `DELETE /api/v1/tasks/{task_id}` - Delete task
- `POST /api/v1/tasks/{task_id}/process` - Start background processing
- `GET /api/v1/tasks/processing/status` - Get processing status
- `GET /health` - Health check endpoint

## Example Usage

**Create a task:**
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
     -H "Content-Type: application/json" \
     -d '{"title": "My Task", "description": "Task description", "priority": 1}'
```

**Start background processing:**
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/1/process"
```

## Tech Stack

- **FastAPI** - Web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM with async support
- **Alembic** - Database migrations
- **Redis** - Background task queue
- **Pydantic** - Data validation
- **pytest** - Testing framework
- **Docker** - Containerization
