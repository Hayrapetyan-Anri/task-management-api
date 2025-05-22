"""
Application configuration settings.

This module defines the configuration classes for the Task Management API,
including database settings, Redis configuration, and other environment-specific variables.
"""

from typing import Optional
from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    This class defines all configuration parameters for the application,
    including database connections, Redis settings, and API configuration.
    """
    
    # API Configuration
    PROJECT_NAME: str = Field(default="Task Management API", description="Name of the API project")
    API_V1_STR: str = Field(default="/api/v1", description="API version prefix")
    SECRET_KEY: str = Field(description="Secret key for JWT encoding")
    
    # Environment
    ENV: str = Field(default="development", description="Environment (development, production, testing)")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # Database Configuration
    DATABASE_URL: str = Field(description="PostgreSQL database URL")
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQLAlchemy query logging")
    
    # Redis Configuration
    REDIS_URL: str = Field(description="Redis connection URL")
    
    # Task Processing Configuration
    TASK_RETRY_ATTEMPTS: int = Field(default=3, description="Number of retry attempts for failed tasks")
    TASK_RETRY_DELAY: int = Field(default=60, description="Delay between retry attempts in seconds")
    MAX_CONCURRENT_TASKS: int = Field(default=10, description="Maximum number of concurrent background tasks")
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = Field(default=20, description="Default number of items per page")
    MAX_PAGE_SIZE: int = Field(default=100, description="Maximum number of items per page")
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="List of allowed CORS origins"
    )
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """
        Validate and ensure the database URL uses asyncpg driver.
        
        Args:
            v: The database URL string
            
        Returns:
            Validated database URL with asyncpg driver
        """
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif not v.startswith("postgresql+asyncpg://"):
                raise ValueError("Database URL must use postgresql+asyncpg:// scheme")
        return v
    
    @field_validator("BACKEND_CORS_ORIGINS")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """
        Parse CORS origins from string or list.
        
        Args:
            v: CORS origins as string (comma-separated) or list
            
        Returns:
            List of CORS origin URLs
        """
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError("CORS origins must be a list or comma-separated string")
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)


class TestSettings(Settings):
    """
    Test-specific configuration settings.
    
    Inherits from Settings and overrides certain values for testing environment.
    """
    
    ENV: str = "testing"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/task_management_test"
    DATABASE_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"


def get_settings() -> Settings:
    """
    Get application settings instance.
    
    Returns the appropriate settings class based on the environment.
    This function can be easily mocked in tests.
    
    Returns:
        Settings instance for the current environment
    """
    import os
    env = os.getenv("ENV", "development")
    
    if env == "testing":
        return TestSettings()
    return Settings()


# Global settings instance
settings = get_settings()
