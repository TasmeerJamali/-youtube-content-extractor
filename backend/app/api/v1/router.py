"""
API router for v1 endpoints.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import search, health, analytics, trends

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    search.router,
    prefix="/search",
    tags=["search"]
)

api_router.include_router(
    trends.router,
    prefix="/trends",
    tags=["trends"]
)

api_router.include_router(
    health.router,
    prefix="/health",
    tags=["health"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)