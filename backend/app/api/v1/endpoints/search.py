"""
Search endpoints for video content discovery.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.services.input_processor import get_input_processor, ProcessedQuery
from app.services.youtube_api import get_youtube_api
from app.utils.api_key_validator import validate_youtube_api_key, get_api_key_help

logger = logging.getLogger(__name__)
router = APIRouter()


class SearchRequest(BaseModel):
    """Request model for content search."""
    idea: str = Field(..., min_length=1, max_length=1000, description="Video idea or concept to search for")
    max_results: int = Field(default=50, ge=1, le=200, description="Maximum number of results to return")
    content_types: Optional[List[str]] = Field(default=None, description="Preferred content types")
    language: Optional[str] = Field(default="en", description="Content language")
    region: Optional[str] = Field(default="US", description="Region code for localized results")
    published_after: Optional[datetime] = Field(default=None, description="Only include videos published after this date")
    published_before: Optional[datetime] = Field(default=None, description="Only include videos published before this date")
    min_duration: Optional[int] = Field(default=None, description="Minimum video duration in seconds")
    max_duration: Optional[int] = Field(default=None, description="Maximum video duration in seconds")
    include_transcripts: bool = Field(default=False, description="Whether to include video transcripts")
    include_comments: bool = Field(default=False, description="Whether to include top comments")
    api_key: Optional[str] = Field(default=None, description="User's YouTube API key (optional)")


class VideoResult(BaseModel):
    """Video result model."""
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
    relevance_score: float
    quality_score: float
    engagement_rate: Optional[float]
    tags: List[str]
    category: Optional[str]
    transcript: Optional[str] = None
    top_comments: Optional[List[str]] = None


class SearchResponse(BaseModel):
    """Response model for search results."""
    query_info: Dict[str, Any]
    total_results: int
    videos: List[VideoResult]
    search_time_ms: int
    quota_used: int
    suggestions: List[str]


@router.post("/", response_model=SearchResponse)
async def search_content(
    request: SearchRequest,
    background_tasks: BackgroundTasks,
    input_processor = Depends(get_input_processor)
):
    """
    Search for YouTube content based on video ideas and concepts.
    Supports user-provided API keys for unlimited quota.
    """
    start_time = datetime.now()
    
    try:
        # Get YouTube API instance with user's API key if provided
        youtube_api = await get_youtube_api(request.api_key)
        
        # Log API key usage (without exposing the key)
        if request.api_key and request.api_key.strip():
            logger.info(f"Using user-provided API key for search: {request.idea[:50]}...")
        else:
            logger.info(f"Using default API key for search: {request.idea[:50]}...")
        # Process the input idea
        user_preferences = {
            "language": request.language,
            "region": request.region
        }
        
        processed_query = await input_processor.process_idea(
            request.idea, 
            user_preferences
        )
        
        # Build enhanced search query with content types
        search_query = processed_query.search_terms[0] if processed_query.search_terms else request.idea
        
        # Enhance search query with content type keywords
        if request.content_types and len(request.content_types) > 0:
            content_keywords = {
                'tutorial': 'how to guide tutorial',
                'review': 'review unboxing test',
                'animation': 'animation animated cartoon',
                'music': 'music song artist',
                'gaming': 'gaming gameplay game',
                'vlog': 'vlog daily lifestyle',
                'news': 'news breaking report',
                'comedy': 'funny comedy humor',
                'documentary': 'documentary investigation',
                'educational': 'educational learn science'
            }
            
            # Add content type keywords to search query
            for content_type in request.content_types:
                if content_type.lower() in content_keywords:
                    search_query += f" {content_keywords[content_type.lower()]}"
        
        # Perform YouTube search
        search_results = await youtube_api.search_videos(
            query=search_query,
            max_results=request.max_results,
            published_after=request.published_after,
            published_before=request.published_before,
            region_code=request.region,
            language=request.language
        )
        
        # Extract video IDs with error handling
        video_ids = []
        for item in search_results.get("items", []):
            try:
                if "id" in item and "videoId" in item["id"]:
                    video_ids.append(item["id"]["videoId"])
                elif "id" in item and isinstance(item["id"], str):
                    # Sometimes the id is a string directly
                    video_ids.append(item["id"])
            except (KeyError, TypeError) as e:
                logger.warning(f"Skipping item with invalid structure: {e}")
                continue
        
        # Get detailed video information
        video_details = await youtube_api.get_video_details(video_ids)
        
        # Process and score results
        videos = []
        for video in video_details.get("items", []):
            video_result = await _process_video_result(
                video, 
                processed_query,
                youtube_api,
                request.include_transcripts,
                request.include_comments
            )
            
            # Apply filters
            if _apply_filters(video_result, request):
                videos.append(video_result)
        
        # Sort by relevance score
        videos.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Generate suggestions
        suggestions = await input_processor.expand_query(processed_query)
        
        # Calculate search time
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Get quota usage
        quota_info = await youtube_api.get_quota_usage()
        
        return SearchResponse(
            query_info={
                "original_idea": request.idea,
                "processed_keywords": processed_query.keywords,
                "detected_content_types": [ct.value for ct in processed_query.content_types],
                "intent": processed_query.intent,
                "confidence": processed_query.confidence,
                "search_terms_used": processed_query.search_terms[:5]
            },
            total_results=len(videos),
            videos=videos,
            search_time_ms=int(search_time),
            quota_used=quota_info["quota_used"],
            suggestions=suggestions[:10]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


async def _process_video_result(
    video: Dict[str, Any],
    processed_query: ProcessedQuery,
    youtube_api,
    include_transcripts: bool,
    include_comments: bool
) -> VideoResult:
    """Process a single video result."""
    
    snippet = video.get("snippet", {})
    statistics = video.get("statistics", {})
    content_details = video.get("contentDetails", {})
    
    # Calculate relevance score
    relevance_score = _calculate_relevance_score(video, processed_query)
    
    # Calculate quality score
    quality_score = _calculate_quality_score(video)
    
    # Calculate engagement rate
    engagement_rate = _calculate_engagement_rate(statistics)
    
    # Parse duration
    duration = _parse_duration(content_details.get("duration", ""))
    
    # Get transcript if requested
    transcript = None
    if include_transcripts:
        try:
            transcript = await youtube_api.get_video_transcript(video["id"])
            if not transcript:
                transcript = "No transcript available"
        except Exception as e:
            logger.warning(f"Failed to get transcript for video {video['id']}: {e}")
            transcript = "Transcript unavailable"
    
    # Get comments if requested
    top_comments = None
    if include_comments:
        try:
            comments_response = await youtube_api.get_video_comments(video["id"], max_results=5)
            comments = comments_response.get("items", [])
            if comments:
                top_comments = [
                    comment["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    for comment in comments
                    if "snippet" in comment and "topLevelComment" in comment["snippet"]
                ]
                # Limit comment length for display
                top_comments = [comment[:200] + "..." if len(comment) > 200 else comment for comment in top_comments]
            else:
                top_comments = ["No comments available"]
        except Exception as e:
            logger.warning(f"Failed to get comments for video {video['id']}: {e}")
            top_comments = ["Comments unavailable"]
    
    return VideoResult(
        video_id=video["id"],
        title=snippet.get("title", ""),
        description=snippet.get("description", ""),
        channel_title=snippet.get("channelTitle", ""),
        channel_id=snippet.get("channelId", ""),
        published_at=datetime.fromisoformat(snippet.get("publishedAt", "").replace("Z", "+00:00")),
        duration=duration,
        view_count=int(statistics.get("viewCount", 0)),
        like_count=int(statistics.get("likeCount", 0)) if statistics.get("likeCount") else None,
        comment_count=int(statistics.get("commentCount", 0)) if statistics.get("commentCount") else None,
        thumbnail_url=snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        relevance_score=relevance_score,
        quality_score=quality_score,
        engagement_rate=engagement_rate,
        tags=snippet.get("tags", []),
        category=snippet.get("categoryId"),
        transcript=transcript,
        top_comments=top_comments
    )


def _calculate_relevance_score(video: Dict[str, Any], processed_query: ProcessedQuery) -> float:
    """Calculate relevance score for a video."""
    score = 0.0
    
    title = video.get("snippet", {}).get("title", "").lower()
    description = video.get("snippet", {}).get("description", "").lower()
    
    # Keyword matching
    for keyword in processed_query.keywords[:10]:
        if keyword in title:
            score += 0.1
        if keyword in description:
            score += 0.05
    
    # Title similarity to original idea
    original_words = set(processed_query.original_text.lower().split())
    title_words = set(title.split())
    title_overlap = len(original_words.intersection(title_words)) / max(len(original_words), 1)
    score += title_overlap * 0.3
    
    # Content type matching
    for content_type in processed_query.content_types:
        if content_type.value in title or content_type.value in description:
            score += 0.2
    
    return min(score, 1.0)


def _calculate_quality_score(video: Dict[str, Any]) -> float:
    """Calculate quality score based on metrics."""
    statistics = video.get("statistics", {})
    snippet = video.get("snippet", {})
    
    view_count = int(statistics.get("viewCount", 0))
    like_count = int(statistics.get("likeCount", 0))
    comment_count = int(statistics.get("commentCount", 0))
    
    score = 0.0
    
    # View count factor
    if view_count > 1000000:
        score += 0.3
    elif view_count > 100000:
        score += 0.2
    elif view_count > 10000:
        score += 0.1
    
    # Engagement factor
    if view_count > 0:
        like_ratio = like_count / view_count
        comment_ratio = comment_count / view_count
        
        score += min(like_ratio * 100, 0.3)
        score += min(comment_ratio * 500, 0.2)
    
    # Channel quality indicators
    channel_title = snippet.get("channelTitle", "")
    if any(indicator in channel_title.lower() for indicator in ["official", "verified"]):
        score += 0.2
    
    return min(score, 1.0)


def _calculate_engagement_rate(statistics: Dict[str, Any]) -> Optional[float]:
    """Calculate engagement rate."""
    view_count = int(statistics.get("viewCount", 0))
    like_count = int(statistics.get("likeCount", 0))
    comment_count = int(statistics.get("commentCount", 0))
    
    if view_count == 0:
        return None
    
    engagement = (like_count + comment_count * 2) / view_count
    return min(engagement, 1.0)


def _parse_duration(duration_str: str) -> Optional[int]:
    """Parse ISO 8601 duration to seconds."""
    if not duration_str:
        return None
    
    # Simple parsing for PT#M#S format
    import re
    
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    match = re.match(pattern, duration_str)
    
    if match:
        hours, minutes, seconds = match.groups()
        total_seconds = 0
        
        if hours:
            total_seconds += int(hours) * 3600
        if minutes:
            total_seconds += int(minutes) * 60
        if seconds:
            total_seconds += int(seconds)
        
        return total_seconds
    
    return None


def _apply_filters(video: VideoResult, request: SearchRequest) -> bool:
    """Apply filters to video results."""
    
    # Duration filters
    if request.min_duration and video.duration and video.duration < request.min_duration:
        return False
    
    if request.max_duration and video.duration and video.duration > request.max_duration:
        return False
    
    # Content type filters
    if request.content_types and len(request.content_types) > 0:
        content_match = False
        title_lower = video.title.lower()
        description_lower = video.description.lower()
        tags_lower = [tag.lower() for tag in video.tags] if video.tags else []
        
        for content_type in request.content_types:
            content_type_lower = content_type.lower()
            
            # Check if content type appears in title, description, or tags
            if (content_type_lower in title_lower or 
                content_type_lower in description_lower or 
                any(content_type_lower in tag for tag in tags_lower) or
                any(content_type_lower in keyword for keyword in [title_lower, description_lower])):
                content_match = True
                break
                
            # Additional keyword matching for content types
            content_keywords = {
                'tutorial': ['how to', 'guide', 'learn', 'step by step', 'beginners', 'course'],
                'review': ['review', 'unboxing', 'test', 'comparison', 'vs', 'pros and cons'],
                'animation': ['animated', 'cartoon', 'anime', '2d', '3d', 'motion graphics'],
                'music': ['song', 'album', 'artist', 'band', 'concert', 'cover', 'remix'],
                'gaming': ['gameplay', 'lets play', 'playthrough', 'game', 'speedrun', 'stream'],
                'vlog': ['vlog', 'daily', 'routine', 'lifestyle', 'day in my life'],
                'news': ['news', 'breaking', 'report', 'update', 'current events'],
                'comedy': ['funny', 'humor', 'jokes', 'comedy', 'hilarious', 'laugh'],
                'documentary': ['documentary', 'investigation', 'true story', 'facts'],
                'educational': ['educational', 'science', 'math', 'history', 'learn']
            }
            
            if content_type_lower in content_keywords:
                keywords = content_keywords[content_type_lower]
                if any(keyword in title_lower or keyword in description_lower for keyword in keywords):
                    content_match = True
                    break
        
        if not content_match:
            return False
    
    # Date filters are already applied in the YouTube API call
    
    return True


@router.get("/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=1, description="Partial search query"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of suggestions to return"),
    input_processor = Depends(get_input_processor)
):
    """Get search suggestions based on partial input."""
    
    try:
        # Process partial query
        processed_query = await input_processor.process_idea(query)
        
        # Generate suggestions
        suggestions = await input_processor.expand_query(processed_query)
        
        return {
            "query": query,
            "suggestions": suggestions[:limit]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate suggestions: {str(e)}")


@router.get("/trending")
async def get_trending_content(
    region: str = Query(default="US", description="Region code"),
    category: Optional[str] = Query(default=None, description="Video category ID"),
    max_results: int = Query(default=25, ge=1, le=50, description="Number of results"),
    api_key: Optional[str] = Query(default=None, description="User's YouTube API key (optional)")
):
    """Get trending content for analysis."""
    
    try:
        # Get YouTube API instance with user's API key if provided
        youtube_api = await get_youtube_api(api_key)
        trending_videos = await youtube_api.get_trending_videos(
            region_code=region,
            category_id=category,
            max_results=max_results
        )
        
        return {
            "region": region,
            "category": category,
            "videos": trending_videos.get("items", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trending content: {str(e)}")


@router.post("/validate-api-key")
async def validate_api_key(
    api_key: str = Query(..., description="YouTube API key to validate")
):
    """Validate a YouTube API key."""
    
    try:
        validation_result = await validate_youtube_api_key(api_key)
        return validation_result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")


@router.get("/api-key-help")
async def get_api_key_help_info():
    """Get information about obtaining a YouTube API key."""
    
    return get_api_key_help()