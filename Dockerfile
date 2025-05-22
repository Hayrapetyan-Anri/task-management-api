# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create requirements.txt from pyproject.toml dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    fastapi==0.104.1 \
    "uvicorn[standard]==0.24.0" \
    sqlalchemy==2.0.23 \
    asyncpg==0.29.0 \
    alembic==1.12.1 \
    pydantic==2.5.0 \
    pydantic-settings==2.0.3 \
    python-multipart==0.0.6 \
    httpx==0.25.2 \
    redis==5.0.1 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1 \
    pytest-cov==4.1.0 \
    aiosqlite==0.19.0

# Copy application code
COPY ./app /app/app
COPY ./alembic.ini /app/
COPY ./alembic /app/alembic

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
