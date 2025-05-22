"""
Main FastAPI application module.

This module initializes and configures the FastAPI application,
including middleware, exception handlers, and route registration.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.tasks import router as tasks_router
from app.core.config import settings
from app.services.background_tasks import shutdown_processor

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the FastAPI application,
    including background task processor cleanup.
    
    Args:
        app: FastAPI application instance
    """
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENV}")
    logger.info(f"Database URL: {str(settings.DATABASE_URL).split('@')[1] if '@' in str(settings.DATABASE_URL) else 'Not configured'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    await shutdown_processor()
    logger.info("Application shutdown complete")


def setup_middleware(app: FastAPI) -> None:
    """
    Configure application middleware.
    
    Args:
        app: FastAPI application instance
    """
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware for production
    if settings.ENV == "production":
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]  # Configure this properly for production
        )


def add_exception_handlers(app: FastAPI) -> None:
    """
    Configure global exception handlers.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
        """
        Handle SQLAlchemy database errors.
        
        Args:
            request: FastAPI request object
            exc: SQLAlchemy exception
            
        Returns:
            JSON error response
        """
        logger.error(f"Database error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Database error occurred",
                "type": "database_error"
            }
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """
        Handle ValueError exceptions.
        
        Args:
            request: FastAPI request object
            exc: ValueError exception
            
        Returns:
            JSON error response
        """
        logger.warning(f"Value error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "type": "validation_error"
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """
        Handle general exceptions.
        
        Args:
            request: FastAPI request object
            exc: General exception
            
        Returns:
            JSON error response
        """
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Internal server error",
                "type": "internal_error"
            }
        )


def setup_routers(app: FastAPI) -> None:
    """
    Configure application routers.
    
    Args:
        app: FastAPI application instance
    """
    # Include API v1 routes
    app.include_router(
        tasks_router,
        prefix=settings.API_V1_STR,
    )


def setup_health_check(app: FastAPI) -> None:
    """
    Setup health check endpoint.
    
    Args:
        app: FastAPI application instance
    """
    
    @app.get(
        "/health",
        summary="Health check",
        description="Simple health check endpoint to verify the application is running",
        tags=["health"]
    )
    async def health_check():
        """
        Health check endpoint.
        
        Returns:
            Health status information
        """
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": "1.0.0",
            "environment": settings.ENV
        }
    
    @app.get(
        "/",
        summary="Root endpoint",
        description="Root endpoint with basic API information",
        tags=["health"]
    )
    async def root():
        """
        Root endpoint.
        
        Returns:
            Basic API information
        """
        return {
            "message": f"Welcome to {settings.PROJECT_NAME}",
            "version": "1.0.0",
            "docs_url": f"{settings.API_V1_STR}/docs",
            "openapi_url": f"{settings.API_V1_STR}/openapi.json"
        }


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with metadata
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="A FastAPI application for managing tasks with background processing capabilities",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan
    )
    
    # Add middleware
    setup_middleware(app)
    
    # Add exception handlers
    add_exception_handlers(app)
    
    # Include routers
    setup_routers(app)
    
    # Add health check endpoint
    setup_health_check(app)
    
    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENV == "development",
        log_level=settings.LOG_LEVEL.lower()
    )
    