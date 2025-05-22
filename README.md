# Task Management API

A FastAPI application for managing tasks with background processing capabilities. This application demonstrates modern Python web development practices including async programming, database operations, and comprehensive testing.

## Features

- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Async Database Operations**: SQLAlchemy with async support and PostgreSQL
- **Background Task Processing**: Async task queue with concurrent processing
- **Comprehensive API**: Full CRUD operations with filtering and pagination
- **Data Validation**: Pydantic schemas for request/response validation
- **Database Migrations**: Alembic for schema version control
- **Testing Suite**: Unit and integration tests with pytest
- **Docker Support**: Containerized application with docker-compose
- **Code Quality**: Type hints, docstrings, and formatting tools

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Poetry (for dependency management)

### Running with Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd task-management-api
   ```

2. **Start the services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - API: http://localhost:8000
   - Interactive docs: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

### Running for Development

1. **Start services with hot reload:**
   ```bash
   docker-compose --profile dev up --build
   ```

2. **The development server will be available at:**
   - API: http://localhost:8001
   - Code changes will automatically reload the server

## API Endpoints

### Core Task Operations

- `POST /api/v1/tasks/` - Create a new task
- `GET /api/v1/tasks/` - List tasks (with filtering and pagination)
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PUT /api/v1/tasks/{task_id}` - Update task
- `DELETE /api/v1/tasks/{task_id}` - Delete task

### Background Processing

- `POST /api/v1/tasks/{task_id}/process` - Start background processing
- `GET /api/v1/tasks/processing/status` - Get processing status

### Statistics and Monitoring

- `GET /api/v1/tasks/stats/summary` - Get task statistics
- `GET /health` - Health check endpoint

### Example Usage

**Create a task:**
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "Important Task",
       "description": "This task needs to be completed",
       "priority": 1
     }'
```

**List tasks with filtering:**
```bash
curl "http://localhost:8000/api/v1/tasks/?status=pending&priority=1&page=1&per_page=10"
```

**Start background processing:**
```bash
curl -X POST "http://localhost:8000/api/v1/tasks/1/process"
```

## Database Schema

### Tasks Table
```sql
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Task Logs Table
```sql
CREATE TABLE task_logs (
    id SERIAL PRIMARY KEY,
    task_id INTEGER REFERENCES tasks(id),
    status VARCHAR(50) NOT NULL,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Task Status Flow

- **pending** → **in_progress** → **completed**
- **pending** → **in_progress** → **failed**
- **failed** → **in_progress** → **completed**

## Priority Levels

- **0**: Critical
- **1**: High
- **2**: Medium (default)
- **3**: Low

## Development

### Local Setup

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start PostgreSQL and Redis:**
   ```bash
   docker-compose up db redis
   ```

4. **Run database migrations:**
   ```bash
   poetry run alembic upgrade head
   ```

5. **Start the development server:**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

### Database Migrations

**Create a new migration:**
```bash
docker-compose exec api alembic revision --autogenerate -m "description"
```

**Apply migrations:**
```bash
docker-compose exec api alembic upgrade head
```

**Rollback migrations:**
```bash
docker-compose exec api alembic downgrade -1
```

### Running Tests

**Run all tests:**
```bash
docker-compose exec api pytest
```

**Run with coverage:**
```bash
docker-compose exec api pytest --cov=app --cov-report=html
```

**Run specific test categories:**
```bash
# Unit tests only
docker-compose exec api pytest -m unit

# Integration tests only
docker-compose exec api pytest -m integration
```

### Code Quality

**Format code:**
```bash
docker-compose exec api black app/
docker-compose exec api isort app/
```

**Lint code:**
```bash
docker-compose exec api flake8 app/
docker-compose exec api mypy app/
```

## Architecture

### Project Structure
```
app/
├── api/v1/          # API endpoints
├── core/            # Configuration and database
├── db/              # Database utilities
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas
├── services/        # Business logic
└── tests/           # Test suite
```

### Key Components

- **FastAPI Application**: Main web framework handling HTTP requests
- **SQLAlchemy Models**: Database ORM for data persistence
- **Pydantic Schemas**: Data validation and serialization
- **Task Service**: Business logic for task operations
- **Background Processor**: Async task processing engine
- **Alembic**: Database migration management

### Background Processing

The application includes a custom background task processor that:

- Manages concurrent task execution
- Provides task status tracking
- Handles failures and retries
- Supports graceful shutdown
- Maintains processing statistics

## Monitoring and Observability

### Application Monitoring

For production deployment, consider implementing:

1. **Logging Strategy:**
   - Structured logging with JSON format
   - Log aggregation (ELK stack, Fluentd)
   - Application-specific metrics

2. **Metrics Collection:**
   - Prometheus for metrics
   - Grafana for visualization
   - Custom business metrics

3. **Health Checks:**
   - Database connectivity
   - Background processor status
   - External service dependencies

4. **Error Tracking:**
   - Sentry for error monitoring
   - Alert management
   - Performance monitoring

### Database Monitoring

- Connection pool monitoring
- Query performance analysis
- Index usage statistics
- Database size and growth tracking

### Infrastructure Monitoring

- Container resource usage
- Network performance
- Disk space and I/O
- Load balancer metrics

## Deployment

### Docker Production Build

```dockerfile
# Multi-stage build for production
FROM python:3.11-slim as production

# Install production dependencies only
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-root

# Copy application code
COPY ./app /app/app
COPY ./alembic.ini /app/
COPY ./alembic /app/alembic

# Production command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables

Key environment variables for production:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:port/dbname

# Redis
REDIS_URL=redis://host:port/0

# Application
SECRET_KEY=your-secret-key
ENV=production
LOG_LEVEL=INFO

# CORS
BACKEND_CORS_ORIGINS=https://somedomain.some

# Task Processing
MAX_CONCURRENT_TASKS=50
TASK_RETRY_ATTEMPTS=3
```

### Security Considerations

- Use secrets management for sensitive data
- Implement proper CORS configuration
- Add rate limiting
- Use HTTPS in production
- Regular security updates
- Database connection encryption