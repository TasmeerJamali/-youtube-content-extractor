"""
Trending content endpoints for discovering popular videos.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.services.youtube_api import get_youtube_api

logger = logging.getLogger(__name__)
router = APIRouter()


class TrendingRequest(BaseModel):
    """Request model for trending content."""
    region: Optional[str] = Field(default="US", description="Region code for trending videos")
    category_id: Optional[str] = Field(default=None, description="Video category ID")
    max_results: int = Field(default=50, ge=1, le=200, description="Maximum number of results")


class TrendingVideoResult(BaseModel):
    """Trending video result model."""
    video_id: str
    title: str
    description: str
    channel_title: str
    channel_id: str
    published_at: datetime
    duration: Optional[int]
    view_count: int
    like_count: Optional[int]
    comment_count: Optional[int]
    thumbnail_url: str
    category: Optional[str]
    tags: List[str]
    trending_score: float


class TrendingResponse(BaseModel):
    """Response model for trending results."""
    region: str
    category: Optional[str]
    total_results: int
    videos: List[TrendingVideoResult]
    generated_at: datetime


@router.get("/", response_model=TrendingResponse)
async def get_trending_videos(
    region: str = Query(default="US", description="Region code"),
    category_id: Optional[str] = Query(default=None, description="Category ID"), 
    max_results: int = Query(default=50, ge=1, le=200, description="Max results"),
    youtube_api = Depends(get_youtube_api)
):
    """
    Get trending videos for a specific region and category.
    """
    
    try:
        # Get trending videos from YouTube API
        trending_results = await youtube_api.get_trending_videos(
            region_code=region,
            category_id=category_id,
            max_results=max_results
        )
        
        # Process and format results
        videos = []
        for video in trending_results.get("items", []):
            video_result = _process_trending_video(video)
            videos.append(video_result)
        
        return TrendingResponse(
            region=region,
            category=category_id,
            total_results=len(videos),
            videos=videos,
            generated_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error fetching trending videos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending videos: {str(e)}")


@router.get("/categories", response_model=List[Dict[str, Any]])
async def get_video_categories(
    region: str = Query(default="US", description="Region code"),
    youtube_api = Depends(get_youtube_api)
):
    """
    Get available video categories for a region.
    """
    
    try:
        # Get video categories from YouTube API
        categories_results = await youtube_api.get_video_categories(region_code=region)
        
        categories = []
        for category in categories_results.get("items", []):
            categories.append({
                "id": category["id"],
                "title": category["snippet"]["title"],
                "assignable": category["snippet"]["assignable"]
            })
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch categories: {str(e)}")


def _process_trending_video(video: Dict[str, Any]) -> TrendingVideoResult:
    """Process a single trending video result."""
    
    snippet = video.get("snippet", {})
    statistics = video.get("statistics", {})
    
    # Calculate trending score based on engagement
    view_count = int(statistics.get("viewCount", 0))
    like_count = int(statistics.get("likeCount", 0)) if statistics.get("likeCount") else 0
    comment_count = int(statistics.get("commentCount", 0)) if statistics.get("commentCount") else 0
    
    # Simple trending score calculation
    trending_score = (like_count * 2 + comment_count * 3) / max(view_count, 1) * 100000
    
    # Parse duration (if available)
    duration = None
    if "contentDetails" in video:
        duration_str = video["contentDetails"].get("duration", "")
        duration = _parse_duration(duration_str)
    
    return TrendingVideoResult(
        video_id=video["id"],
        title=snippet.get("title", ""),
        description=snippet.get("description", "")[:300] + "..." if len(snippet.get("description", "")) > 300 else snippet.get("description", ""),
        channel_title=snippet.get("channelTitle", ""),
        channel_id=snippet.get("channelId", ""),
        published_at=datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00")),
        duration=duration,
        view_count=view_count,
        like_count=like_count,
        comment_count=comment_count,
        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        category=snippet.get("categoryId"),
        tags=snippet.get("tags", [])[:10],  # Limit tags
        trending_score=trending_score
    )


def _parse_duration(duration_str: str) -> Optional[int]:
    """Parse ISO 8601 duration string to seconds."""
    import re
    
    if not duration_str:
        return None
    
    # Parse ISO 8601 duration (e.g., PT4M13S)
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return None
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds