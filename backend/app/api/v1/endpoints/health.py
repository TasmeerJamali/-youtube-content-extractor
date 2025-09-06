"""
Health and monitoring endpoints.
"""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.services.youtube_api import get_youtube_api
from app.utils.cache_manager import get_cache_manager

router = APIRouter()


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    timestamp: datetime
    services: Dict[str, Any]
    performance: Dict[str, Any]


@router.get("/", response_model=HealthStatus)
async def health_check(
    youtube_api = Depends(get_youtube_api),
    cache_manager = Depends(get_cache_manager)
):
    """Comprehensive health check."""
    
    timestamp = datetime.now()
    services = {}
    performance = {}
    
    # Check YouTube API service
    try:
        quota_info = await youtube_api.get_quota_usage()
        services["youtube_api"] = {
            "status": "healthy",
            "quota_used": quota_info["quota_used"],
            "quota_remaining": quota_info["quota_remaining"],
            "quota_percentage": quota_info["usage_percentage"]
        }
    except Exception as e:
        services["youtube_api"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Check cache service
    try:
        cache_stats = await cache_manager.get_stats()
        services["cache"] = {
            "status": "healthy" if cache_stats["redis_connected"] else "degraded",
            "redis_connected": cache_stats["redis_connected"],
            "memory_cache_size": cache_stats["memory_cache_size"],
            "caching_enabled": cache_stats["caching_enabled"]
        }
    except Exception as e:
        services["cache"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # Overall status
    overall_status = "healthy"
    if any(service.get("status") == "unhealthy" for service in services.values()):
        overall_status = "unhealthy"
    elif any(service.get("status") == "degraded" for service in services.values()):
        overall_status = "degraded"
    
    # Performance metrics (placeholder)
    performance = {
        "response_time_ms": 0,  # Would be calculated from actual metrics
        "memory_usage_mb": 0,   # Would be from system monitoring
        "cpu_usage_percent": 0  # Would be from system monitoring
    }
    
    return HealthStatus(
        status=overall_status,
        timestamp=timestamp,
        services=services,
        performance=performance
    )


@router.get("/services")
async def service_status():
    """Get detailed service status information."""
    
    return {
        "services": [
            {
                "name": "YouTube API",
                "description": "YouTube Data API v3 integration",
                "dependencies": ["Google APIs"],
                "endpoints": ["/search", "/videos", "/channels"]
            },
            {
                "name": "Cache Manager",
                "description": "Redis and in-memory caching",
                "dependencies": ["Redis"],
                "endpoints": ["all cached operations"]
            },
            {
                "name": "Input Processor",
                "description": "NLP-based query processing",
                "dependencies": ["spaCy", "NLTK"],
                "endpoints": ["/search"]
            }
        ]
    }


@router.get("/metrics")
async def get_metrics(
    youtube_api = Depends(get_youtube_api),
    cache_manager = Depends(get_cache_manager)
):
    """Get system metrics and statistics."""
    
    try:
        # YouTube API metrics
        quota_info = await youtube_api.get_quota_usage()
        
        # Cache metrics
        cache_stats = await cache_manager.get_stats()
        
        return {
            "timestamp": datetime.now(),
            "youtube_api": {
                "quota_usage": quota_info,
                "requests_today": "Not implemented",  # Would track actual requests
                "error_rate": "Not implemented"       # Would track error rates
            },
            "cache": cache_stats,
            "system": {
                "uptime": "Not implemented",          # Would track actual uptime
                "memory_usage": "Not implemented",    # Would track memory usage
                "cpu_usage": "Not implemented"        # Would track CPU usage
            }
        }
        
    except Exception as e:
        return {
            "error": f"Failed to collect metrics: {str(e)}",
            "timestamp": datetime.now()
        }