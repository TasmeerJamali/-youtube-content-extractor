"""
Analytics and insights endpoints.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.services.youtube_api import get_youtube_api

router = APIRouter()


class TrendAnalysis(BaseModel):
    """Trend analysis response model."""
    keyword: str
    trend_score: float
    search_volume: int
    competition_level: str
    related_topics: List[str]
    content_opportunities: List[str]


class ContentInsights(BaseModel):
    """Content insights response model."""
    topic: str
    total_videos: int
    avg_view_count: float
    avg_engagement_rate: float
    top_creators: List[Dict[str, Any]]
    content_gaps: List[str]
    recommended_formats: List[str]


@router.get("/trends", response_model=List[TrendAnalysis])
async def analyze_trends(
    keywords: List[str] = Query(..., description="Keywords to analyze"),
    region: str = Query(default="US", description="Region for trend analysis"),
    timeframe: str = Query(default="30d", description="Timeframe for analysis"),
    youtube_api = Depends(get_youtube_api)
):
    """Analyze content trends for given keywords."""
    
    try:
        trend_analyses = []
        
        for keyword in keywords:
            # Search for recent content
            search_results = await youtube_api.search_videos(
                query=keyword,
                max_results=50,
                published_after=datetime.now() - timedelta(days=30),
                region_code=region,
                order="relevance"
            )
            
            # Analyze results
            trend_analysis = await _analyze_keyword_trend(keyword, search_results, youtube_api)
            trend_analyses.append(trend_analysis)
        
        return trend_analyses
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trend analysis failed: {str(e)}")


@router.get("/content-insights", response_model=ContentInsights)
async def get_content_insights(
    topic: str = Query(..., description="Topic to analyze"),
    region: str = Query(default="US", description="Region code"),
    content_type: Optional[str] = Query(default=None, description="Content type filter"),
    youtube_api = Depends(get_youtube_api)
):
    """Get comprehensive insights for a content topic."""
    
    try:
        # Search for content in the topic
        search_results = await youtube_api.search_videos(
            query=topic,
            max_results=100,
            region_code=region,
            order="relevance"
        )
        
        # Get detailed video information
        video_ids = [item["id"]["videoId"] for item in search_results.get("items", [])]
        video_details = await youtube_api.get_video_details(video_ids)
        
        # Analyze content
        insights = await _analyze_content_insights(topic, video_details["items"], youtube_api)
        
        return insights
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content insights failed: {str(e)}")


@router.get("/competitor-analysis")
async def analyze_competitors(
    channels: List[str] = Query(..., description="Channel IDs to analyze"),
    metrics: List[str] = Query(default=["views", "engagement", "frequency"], description="Metrics to analyze"),
    youtube_api = Depends(get_youtube_api)
):
    """Analyze competitor channels and their content strategies."""
    
    try:
        analysis_results = []
        
        for channel_id in channels:
            # Get channel details
            channel_details = await youtube_api.get_channel_details([channel_id])
            
            if not channel_details.get("items"):
                continue
            
            channel_info = channel_details["items"][0]
            
            # Search for recent videos from this channel
            search_results = await youtube_api.search_videos(
                query=f'channel:{channel_id}',
                max_results=50,
                published_after=datetime.now() - timedelta(days=30),
                order="date"
            )
            
            # Analyze channel performance
            channel_analysis = await _analyze_channel_performance(
                channel_info, 
                search_results, 
                metrics,
                youtube_api
            )
            
            analysis_results.append(channel_analysis)
        
        return {
            "timestamp": datetime.now(),
            "channels_analyzed": len(analysis_results),
            "analysis": analysis_results,
            "insights": _generate_competitive_insights(analysis_results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitor analysis failed: {str(e)}")


@router.get("/content-gaps")
async def identify_content_gaps(
    niche: str = Query(..., description="Content niche to analyze"),
    competitor_channels: List[str] = Query(default=[], description="Competitor channel IDs"),
    region: str = Query(default="US", description="Region code"),
    youtube_api = Depends(get_youtube_api)
):
    """Identify content gaps and opportunities in a niche."""
    
    try:
        # Search for existing content in the niche
        existing_content = await youtube_api.search_videos(
            query=niche,
            max_results=200,
            region_code=region,
            order="relevance"
        )
        
        # Analyze content gaps
        gaps = await _identify_gaps(niche, existing_content, competitor_channels, youtube_api)
        
        return {
            "niche": niche,
            "analysis_date": datetime.now(),
            "total_existing_content": len(existing_content.get("items", [])),
            "identified_gaps": gaps,
            "recommendations": _generate_gap_recommendations(gaps)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis failed: {str(e)}")


async def _analyze_keyword_trend(
    keyword: str, 
    search_results: Dict[str, Any], 
    youtube_api
) -> TrendAnalysis:
    """Analyze trend data for a specific keyword."""
    
    videos = search_results.get("items", [])
    
    # Calculate trend score based on recent activity
    total_views = 0
    total_videos = len(videos)
    
    if videos:
        # Get detailed stats for sample videos
        video_ids = [item["id"]["videoId"] for item in videos[:20]]
        video_details = await youtube_api.get_video_details(video_ids)
        
        for video in video_details.get("items", []):
            stats = video.get("statistics", {})
            total_views += int(stats.get("viewCount", 0))
    
    # Calculate trend score (simplified)
    avg_views = total_views / max(total_videos, 1)
    trend_score = min(avg_views / 100000, 1.0)  # Normalize to 0-1
    
    # Determine competition level
    if total_videos > 1000:
        competition = "high"
    elif total_videos > 100:
        competition = "medium"
    else:
        competition = "low"
    
    # Generate related topics (simplified)
    related_topics = [f"{keyword} tutorial", f"{keyword} review", f"best {keyword}"]
    
    # Generate content opportunities
    opportunities = [
        f"Beginner's guide to {keyword}",
        f"{keyword} comparison videos",
        f"Advanced {keyword} techniques"
    ]
    
    return TrendAnalysis(
        keyword=keyword,
        trend_score=trend_score,
        search_volume=total_videos,
        competition_level=competition,
        related_topics=related_topics,
        content_opportunities=opportunities
    )


async def _analyze_content_insights(
    topic: str, 
    videos: List[Dict[str, Any]], 
    youtube_api
) -> ContentInsights:
    """Analyze content insights for a topic."""
    
    if not videos:
        return ContentInsights(
            topic=topic,
            total_videos=0,
            avg_view_count=0.0,
            avg_engagement_rate=0.0,
            top_creators=[],
            content_gaps=[],
            recommended_formats=[]
        )
    
    # Calculate metrics
    total_views = sum(int(video.get("statistics", {}).get("viewCount", 0)) for video in videos)
    avg_view_count = total_views / len(videos)
    
    # Calculate average engagement rate
    engagement_rates = []
    for video in videos:
        stats = video.get("statistics", {})
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0))
        comments = int(stats.get("commentCount", 0))
        
        if views > 0:
            engagement_rate = (likes + comments) / views
            engagement_rates.append(engagement_rate)
    
    avg_engagement_rate = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0.0
    
    # Identify top creators
    creator_stats = {}
    for video in videos:
        channel_id = video.get("snippet", {}).get("channelId")
        channel_title = video.get("snippet", {}).get("channelTitle")
        views = int(video.get("statistics", {}).get("viewCount", 0))
        
        if channel_id:
            if channel_id not in creator_stats:
                creator_stats[channel_id] = {
                    "channel_title": channel_title,
                    "total_views": 0,
                    "video_count": 0
                }
            
            creator_stats[channel_id]["total_views"] += views
            creator_stats[channel_id]["video_count"] += 1
    
    # Sort by total views
    top_creators = sorted(
        [{"channel_id": k, **v} for k, v in creator_stats.items()],
        key=lambda x: x["total_views"],
        reverse=True
    )[:5]
    
    # Identify content gaps (simplified)
    content_gaps = [
        f"Interactive {topic} content",
        f"{topic} for beginners",
        f"Advanced {topic} strategies"
    ]
    
    # Recommend formats
    recommended_formats = ["tutorial", "review", "comparison", "case study"]
    
    return ContentInsights(
        topic=topic,
        total_videos=len(videos),
        avg_view_count=avg_view_count,
        avg_engagement_rate=avg_engagement_rate,
        top_creators=top_creators,
        content_gaps=content_gaps,
        recommended_formats=recommended_formats
    )


async def _analyze_channel_performance(
    channel_info: Dict[str, Any],
    recent_videos: Dict[str, Any],
    metrics: List[str],
    youtube_api
) -> Dict[str, Any]:
    """Analyze performance metrics for a channel."""
    
    channel_stats = channel_info.get("statistics", {})
    videos = recent_videos.get("items", [])
    
    analysis = {
        "channel_id": channel_info["id"],
        "channel_title": channel_info.get("snippet", {}).get("title"),
        "subscriber_count": int(channel_stats.get("subscriberCount", 0)),
        "total_videos": int(channel_stats.get("videoCount", 0)),
        "recent_videos_count": len(videos),
        "metrics": {}
    }
    
    if "views" in metrics and videos:
        # Get detailed video stats
        video_ids = [item["id"]["videoId"] for item in videos]
        video_details = await youtube_api.get_video_details(video_ids)
        
        total_views = sum(
            int(video.get("statistics", {}).get("viewCount", 0))
            for video in video_details.get("items", [])
        )
        
        analysis["metrics"]["avg_views_per_video"] = total_views / len(videos) if videos else 0
        analysis["metrics"]["total_recent_views"] = total_views
    
    if "engagement" in metrics:
        # Calculate engagement metrics
        analysis["metrics"]["avg_engagement_rate"] = 0.05  # Placeholder
    
    if "frequency" in metrics:
        # Calculate posting frequency
        if videos:
            first_video_date = datetime.fromisoformat(videos[-1]["snippet"]["publishedAt"].replace("Z", "+00:00"))
            last_video_date = datetime.fromisoformat(videos[0]["snippet"]["publishedAt"].replace("Z", "+00:00"))
            
            days_span = (last_video_date - first_video_date).days
            frequency = len(videos) / max(days_span, 1) if days_span > 0 else len(videos)
            
            analysis["metrics"]["videos_per_day"] = frequency
    
    return analysis


def _generate_competitive_insights(analysis_results: List[Dict[str, Any]]) -> List[str]:
    """Generate insights from competitive analysis."""
    
    insights = []
    
    if not analysis_results:
        return insights
    
    # Compare subscriber counts
    subscribers = [result.get("subscriber_count", 0) for result in analysis_results]
    avg_subscribers = sum(subscribers) / len(subscribers)
    
    insights.append(f"Average competitor subscriber count: {int(avg_subscribers):,}")
    
    # Compare video frequencies
    frequencies = [
        result.get("metrics", {}).get("videos_per_day", 0) 
        for result in analysis_results
    ]
    
    if frequencies:
        avg_frequency = sum(frequencies) / len(frequencies)
        insights.append(f"Average posting frequency: {avg_frequency:.2f} videos per day")
    
    return insights


async def _identify_gaps(
    niche: str,
    existing_content: Dict[str, Any],
    competitor_channels: List[str],
    youtube_api
) -> List[Dict[str, Any]]:
    """Identify content gaps in a niche."""
    
    gaps = []
    
    # Analyze existing content topics
    videos = existing_content.get("items", [])
    
    # Common content types to check for
    content_types = [
        "tutorial", "review", "comparison", "beginner guide", 
        "advanced tips", "case study", "interview", "behind the scenes"
    ]
    
    # Check which content types are underrepresented
    for content_type in content_types:
        matching_videos = [
            video for video in videos
            if content_type in video.get("snippet", {}).get("title", "").lower()
        ]
        
        if len(matching_videos) < 5:  # Threshold for gap identification
            gaps.append({
                "content_type": content_type,
                "current_count": len(matching_videos),
                "opportunity_score": 1.0 - (len(matching_videos) / 10),
                "suggested_approach": f"Create {content_type} content for {niche}"
            })
    
    return gaps


def _generate_gap_recommendations(gaps: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on identified gaps."""
    
    recommendations = []
    
    # Sort gaps by opportunity score
    sorted_gaps = sorted(gaps, key=lambda x: x["opportunity_score"], reverse=True)
    
    for gap in sorted_gaps[:5]:  # Top 5 recommendations
        recommendations.append(
            f"High opportunity: {gap['suggested_approach']} "
            f"(Current content: {gap['current_count']}, "
            f"Opportunity score: {gap['opportunity_score']:.2f})"
        )
    
    return recommendations