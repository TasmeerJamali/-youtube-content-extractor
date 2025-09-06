"""
Main FastAPI application for YouTube Content Extractor.
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.core.config import get_settings
from app.utils.cache_manager import get_cache_manager
from app.services.input_processor import get_input_processor
from app.api.v1.router import api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    logger.info("Starting YouTube Content Extractor...")
    
    # Initialize services
    try:
        # Initialize cache manager
        cache_manager = await get_cache_manager()
        logger.info("Cache manager initialized")
        
        # Initialize input processor
        input_processor = await get_input_processor()
        logger.info("Input processor initialized")
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Cleanup
    logger.info("Shutting down application...")
    try:
        await cache_manager.close()
        logger.info("Cache manager closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Create FastAPI application
app = FastAPI(
    title="YouTube Content Extractor",
    description="AI-powered YouTube content discovery and analysis system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add API router
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "message": "YouTube Content Extractor API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check cache manager
        cache_manager = await get_cache_manager()
        cache_stats = await cache_manager.get_stats()
        
        return {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z",  # Will be replaced with actual timestamp
            "services": {
                "cache": {
                    "status": "connected" if cache_stats["redis_connected"] else "fallback",
                    "memory_cache_size": cache_stats["memory_cache_size"]
                },
                "nlp": {
                    "status": "ready"
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.max_workers
    )