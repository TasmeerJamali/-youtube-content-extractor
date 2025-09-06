"""
Test configuration and fixtures for the YouTube Content Extractor.
"""

import pytest
import asyncio
from typing import AsyncGenerator
import os
from unittest.mock import MagicMock

# Set test environment
os.environ["ENVIRONMENT"] = "test"

from app.core.config import get_settings
from app.services.youtube_api import YouTubeAPIWrapper
from app.services.input_processor import InputProcessor
from app.services.content_analyzer import ContentAnalyzer


@pytest.fixture
def mock_youtube_api():
    """Mock YouTube API for testing."""
    mock_api = MagicMock(spec=YouTubeAPIWrapper)
    
    # Mock search response
    mock_api.search_videos.return_value = {
        "items": [
            {
                "id": {"videoId": "test_video_1"},
                "snippet": {
                    "title": "How to Build a Web App with Python",
                    "description": "Learn to build modern web applications",
                    "channelTitle": "Tech Tutorial Channel",
                    "channelId": "test_channel_1",
                    "publishedAt": "2024-01-01T12:00:00Z",
                    "tags": ["python", "web development", "tutorial"]
                }
            }
        ]
    }
    
    # Mock video details response
    mock_api.get_video_details.return_value = {
        "items": [
            {
                "id": "test_video_1",
                "snippet": {
                    "title": "How to Build a Web App with Python",
                    "description": "Learn to build modern web applications with Python and FastAPI",
                    "channelTitle": "Tech Tutorial Channel",
                    "channelId": "test_channel_1",
                    "publishedAt": "2024-01-01T12:00:00Z",
                    "tags": ["python", "web development", "tutorial", "fastapi"],
                    "categoryId": "27"
                },
                "statistics": {
                    "viewCount": "50000",
                    "likeCount": "2500",
                    "commentCount": "150"
                },
                "contentDetails": {
                    "duration": "PT15M30S"
                }
            }
        ]
    }
    
    # Mock quota usage
    mock_api.get_quota_usage.return_value = {
        "quota_used": 100,
        "quota_limit": 10000,
        "quota_remaining": 9900,
        "usage_percentage": 1.0
    }
    
    return mock_api


@pytest.fixture
def sample_search_request():
    """Sample search request for testing."""
    return {
        "idea": "How to learn Python programming for beginners",
        "max_results": 25,
        "content_types": ["tutorial"],
        "language": "en",
        "region": "US",
        "include_transcripts": False,
        "include_comments": False
    }


@pytest.fixture
def sample_video_data():
    """Sample video data for testing."""
    return {
        "id": "test_video_1",
        "snippet": {
            "title": "Python Programming Tutorial for Beginners",
            "description": "Complete Python tutorial covering all basics you need to know",
            "channelTitle": "CodeAcademy",
            "channelId": "test_channel_1",
            "publishedAt": "2024-01-01T12:00:00Z",
            "tags": ["python", "programming", "tutorial", "beginners"],
            "categoryId": "27"
        },
        "statistics": {
            "viewCount": "100000",
            "likeCount": "5000",
            "commentCount": "500"
        },
        "contentDetails": {
            "duration": "PT25M45S"
        }
    }


@pytest.fixture
def sample_channel_data():
    """Sample channel data for testing."""
    return {
        "id": "test_channel_1",
        "snippet": {
            "title": "CodeAcademy",
            "description": "Professional programming tutorials and courses",
            "country": "US"
        },
        "statistics": {
            "subscriberCount": "500000",
            "videoCount": "200",
            "viewCount": "10000000"
        }
    }


@pytest.fixture
def test_settings():
    """Test settings configuration."""
    settings = get_settings()
    settings.youtube_api_key = "test_api_key"
    settings.enable_caching = False  # Disable caching for tests
    settings.enable_rate_limiting = False  # Disable rate limiting for tests
    return settings


@pytest.fixture
async def input_processor():
    """Input processor instance for testing."""
    processor = InputProcessor()
    await processor.initialize()
    return processor


@pytest.fixture
async def content_analyzer():
    """Content analyzer instance for testing."""
    analyzer = ContentAnalyzer()
    await analyzer.initialize()
    return analyzer


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Test data constants
TEST_VIDEO_IDEAS = [
    "How to learn Python programming",
    "Best smartphone review 2024",
    "Daily morning routine vlog",
    "Machine learning tutorial for beginners",
    "Cooking pasta recipe video",
    "Gaming walkthrough for new players",
    "Travel vlog from Japan",
    "Product unboxing and first impressions"
]

TEST_KEYWORDS = [
    ["python", "programming", "tutorial", "coding"],
    ["smartphone", "review", "technology", "mobile"],
    ["morning", "routine", "lifestyle", "daily"],
    ["machine learning", "ai", "data science", "tutorial"],
    ["cooking", "pasta", "recipe", "food"],
    ["gaming", "walkthrough", "gameplay", "guide"],
    ["travel", "japan", "vlog", "culture"],
    ["unboxing", "product", "review", "first impressions"]
]

TEST_SEARCH_RESPONSES = {
    "success": {
        "query_info": {
            "original_idea": "How to learn Python programming",
            "processed_keywords": ["python", "programming", "learn", "tutorial"],
            "detected_content_types": ["tutorial"],
            "intent": "learn",
            "confidence": 0.85,
            "search_terms_used": ["python programming tutorial", "learn python"]
        },
        "total_results": 1,
        "videos": [],
        "search_time_ms": 250,
        "quota_used": 100,
        "suggestions": ["python basics", "python course", "programming fundamentals"]
    },
    "no_results": {
        "query_info": {
            "original_idea": "xyz123nonexistent",
            "processed_keywords": ["xyz123nonexistent"],
            "detected_content_types": ["other"],
            "intent": "discover",
            "confidence": 0.2,
            "search_terms_used": ["xyz123nonexistent"]
        },
        "total_results": 0,
        "videos": [],
        "search_time_ms": 180,
        "quota_used": 100,
        "suggestions": []
    }
}