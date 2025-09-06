"""
YouTube API wrapper with rate limiting, caching, and error handling.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

import httpx
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# import aioredis

from app.core.config import get_settings
from app.utils.rate_limiter import RateLimiter
from app.utils.cache_manager import CacheManager

logger = logging.getLogger(__name__)
settings = get_settings()


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""
    pass


class QuotaExceededException(YouTubeAPIError):
    """Exception raised when API quota is exceeded."""
    pass


class YouTubeAPIWrapper:
    """
    Enhanced YouTube API wrapper with comprehensive error handling,
    rate limiting, caching, and quota management.
    Supports both default API key and user-provided API keys.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or fall back to default
        self.api_key = api_key or settings.youtube_api_key
        self.service_name = settings.youtube_api_service_name
        self.version = settings.youtube_api_version
        self.quota_limit = settings.youtube_api_quota_limit
        
        # Initialize YouTube service
        self.youtube = build(
            self.service_name,
            self.version,
            developerKey=self.api_key
        )
        
        # Initialize rate limiter and cache
        self.rate_limiter = RateLimiter()
        self.cache_manager = CacheManager()
        
        # Quota tracking (per API key)
        self.quota_used = 0
        self.quota_reset_time = datetime.now() + timedelta(days=1)
        
        # API costs for different operations
        self.operation_costs = {
            'search': 100,
            'videos': 1,
            'channels': 1,
            'comments': 1,
            'captions': 200
        }
    
    async def _check_quota(self, operation: str) -> bool:
        """Check if we have enough quota for the operation."""
        cost = self.operation_costs.get(operation, 1)
        
        if datetime.now() > self.quota_reset_time:
            self.quota_used = 0
            self.quota_reset_time = datetime.now() + timedelta(days=1)
        
        if self.quota_used + cost > self.quota_limit:
            logger.error(f"Quota exceeded. Used: {self.quota_used}, Limit: {self.quota_limit}")
            raise QuotaExceededException("Daily quota limit exceeded")
        
        return True
    
    async def _update_quota(self, operation: str):
        """Update quota usage after an operation."""
        cost = self.operation_costs.get(operation, 1)
        self.quota_used += cost
        logger.info(f"Quota used: {self.quota_used}/{self.quota_limit} (Operation: {operation}, Cost: {cost})")
    
    async def _make_request(self, request_func, operation: str, cache_key: Optional[str] = None):
        """
        Make a rate-limited and cached API request with error handling.
        """
        # Check cache first
        if cache_key and settings.enable_caching:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for key: {cache_key}")
                return cached_result
        
        # Check quota
        await self._check_quota(operation)
        
        # Apply rate limiting
        await self.rate_limiter.acquire()
        
        try:
            # Execute the request
            result = request_func.execute()
            
            # Update quota
            await self._update_quota(operation)
            
            # Cache the result
            if cache_key and settings.enable_caching:
                await self.cache_manager.set(
                    cache_key, 
                    result, 
                    ttl=settings.cache_ttl_seconds
                )
            
            return result
            
        except HttpError as e:
            error_content = e.content.decode('utf-8') if e.content else "No error content"
            logger.error(f"YouTube API error: {e.resp.status} - {error_content}")
            
            if e.resp.status == 403:
                if "quota" in error_content.lower():
                    raise QuotaExceededException("API quota exceeded")
                else:
                    raise YouTubeAPIError(f"API access forbidden: {error_content}")
            elif e.resp.status == 400:
                raise YouTubeAPIError(f"Bad request: {error_content}")
            elif e.resp.status == 404:
                raise YouTubeAPIError(f"Resource not found: {error_content}")
            else:
                raise YouTubeAPIError(f"API error {e.resp.status}: {error_content}")
        
        except Exception as e:
            logger.error(f"Unexpected error in YouTube API request: {str(e)}")
            raise YouTubeAPIError(f"Unexpected error: {str(e)}")
    
    async def search_videos(
        self,
        query: str,
        max_results: int = 50,
        order: str = "relevance",
        published_after: Optional[datetime] = None,
        published_before: Optional[datetime] = None,
        region_code: Optional[str] = None,
        language: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for videos on YouTube with advanced filtering options.
        """
        # Create cache key
        cache_key = f"search:{hash(f'{query}:{max_results}:{order}:{published_after}:{published_before}:{region_code}:{language}:{content_type}')}"
        
        # Build search parameters
        search_params = {
            'part': 'id,snippet',
            'q': query,
            'type': 'video',
            'maxResults': min(max_results, 50),  # API limit is 50
            'order': order,
            'safeSearch': 'moderate'
        }
        
        if published_after:
            search_params['publishedAfter'] = published_after.isoformat() + 'Z'
        
        if published_before:
            search_params['publishedBefore'] = published_before.isoformat() + 'Z'
        
        if region_code:
            search_params['regionCode'] = region_code
        
        if language:
            search_params['relevanceLanguage'] = language
        
        if content_type == 'live':
            search_params['eventType'] = 'live'
        elif content_type == 'upcoming':
            search_params['eventType'] = 'upcoming'
        
        request = self.youtube.search().list(**search_params)
        
        result = await self._make_request(request, 'search', cache_key)
        
        # If we need more results and haven't hit the max, make additional requests
        if max_results > 50 and 'nextPageToken' in result:
            all_items = result['items']
            next_page_token = result['nextPageToken']
            remaining_results = max_results - 50
            
            while next_page_token and remaining_results > 0:
                search_params['pageToken'] = next_page_token
                search_params['maxResults'] = min(remaining_results, 50)
                
                request = self.youtube.search().list(**search_params)
                page_result = await self._make_request(request, 'search')
                
                all_items.extend(page_result['items'])
                next_page_token = page_result.get('nextPageToken')
                remaining_results -= len(page_result['items'])
            
            result['items'] = all_items
        
        return result
    
    async def get_video_details(self, video_ids: List[str]) -> Dict[str, Any]:
        """
        Get detailed information about specific videos.
        """
        if not video_ids:
            return {'items': []}
        
        # YouTube API allows up to 50 IDs per request
        video_ids_str = ','.join(video_ids[:50])
        cache_key = f"video_details:{hash(video_ids_str)}"
        
        request = self.youtube.videos().list(
            part='id,snippet,statistics,contentDetails,status',
            id=video_ids_str
        )
        
        return await self._make_request(request, 'videos', cache_key)
    
    async def get_channel_details(self, channel_ids: List[str]) -> Dict[str, Any]:
        """
        Get detailed information about specific channels.
        """
        if not channel_ids:
            return {'items': []}
        
        channel_ids_str = ','.join(channel_ids[:50])
        cache_key = f"channel_details:{hash(channel_ids_str)}"
        
        request = self.youtube.channels().list(
            part='id,snippet,statistics,contentDetails,brandingSettings,status',
            id=channel_ids_str
        )
        
        return await self._make_request(request, 'channels', cache_key)
    
    async def get_video_comments(
        self,
        video_id: str,
        max_results: int = 100,
        order: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Get comments for a specific video.
        """
        cache_key = f"comments:{video_id}:{max_results}:{order}"
        
        try:
            request = self.youtube.commentThreads().list(
                part='id,snippet,replies',
                videoId=video_id,
                maxResults=min(max_results, 100),
                order=order,
                textFormat='plainText'
            )
            
            return await self._make_request(request, 'comments', cache_key)
            
        except YouTubeAPIError as e:
            if "disabled" in str(e).lower() or "not found" in str(e).lower():
                logger.warning(f"Comments disabled or not available for video {video_id}")
                return {'items': []}
            raise
    
    async def get_video_captions(self, video_id: str) -> Dict[str, Any]:
        """
        Get available captions/transcripts for a video.
        """
        cache_key = f"captions:{video_id}"
        
        try:
            request = self.youtube.captions().list(
                part='id,snippet',
                videoId=video_id
            )
            
            return await self._make_request(request, 'captions', cache_key)
            
        except YouTubeAPIError as e:
            logger.warning(f"Captions not available for video {video_id}: {e}")
            return {'items': []}
    
    async def download_caption(self, caption_id: str) -> str:
        """
        Download caption content by caption ID.
        """
        try:
            request = self.youtube.captions().download(
                id=caption_id,
                tfmt='srt'  # Get subtitle format
            )
            
            # Execute the request to get the raw caption data
            caption_data = request.execute()
            
            # If caption_data is bytes, decode it
            if isinstance(caption_data, bytes):
                return caption_data.decode('utf-8')
            
            return str(caption_data)
            
        except Exception as e:
            logger.warning(f"Could not download caption {caption_id}: {e}")
            return ""
    
    async def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get video transcript by finding and downloading the best available caption.
        """
        try:
            # Get available captions
            captions_response = await self.get_video_captions(video_id)
            captions = captions_response.get('items', [])
            
            if not captions:
                return None
            
            # Find the best caption (prefer English, then auto-generated)
            best_caption = None
            for caption in captions:
                snippet = caption.get('snippet', {})
                language = snippet.get('language', '')
                
                # Prefer English captions
                if language.startswith('en'):
                    best_caption = caption
                    break
                    
                # Fallback to any available caption
                if not best_caption:
                    best_caption = caption
            
            if best_caption:
                caption_id = best_caption['id']
                transcript_text = await self.download_caption(caption_id)
                
                # Clean up the transcript (remove timestamps, formatting)
                cleaned_transcript = self._clean_transcript(transcript_text)
                return cleaned_transcript
                
            return None
            
        except Exception as e:
            logger.warning(f"Error getting transcript for video {video_id}: {e}")
            return None
    
    def _clean_transcript(self, raw_transcript: str) -> str:
        """
        Clean up raw transcript data by removing timestamps and formatting.
        """
        import re
        
        if not raw_transcript:
            return ""
        
        # Remove SRT timestamps (00:00:00,000 --> 00:00:00,000)
        cleaned = re.sub(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', '', raw_transcript)
        
        # Remove sequence numbers
        cleaned = re.sub(r'^\d+$', '', cleaned, flags=re.MULTILINE)
        
        # Remove extra whitespace and newlines
        cleaned = re.sub(r'\n\s*\n', '\n', cleaned)
        cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)
        
        # Join lines and clean up
        lines = [line.strip() for line in cleaned.split('\n') if line.strip()]
        final_transcript = ' '.join(lines)
        
        # Truncate if too long (keep first 1000 characters)
        if len(final_transcript) > 1000:
            final_transcript = final_transcript[:1000] + "..."
            
        return final_transcript
    
    async def get_trending_videos(
        self,
        region_code: str = "US",
        category_id: Optional[str] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Get trending videos for a specific region and category.
        """
        cache_key = f"trending:{region_code}:{category_id}:{max_results}"
        
        search_params = {
            'part': 'id,snippet,statistics,contentDetails',
            'chart': 'mostPopular',
            'regionCode': region_code,
            'maxResults': min(max_results, 50)
        }
        
        if category_id:
            search_params['videoCategoryId'] = category_id
        
        request = self.youtube.videos().list(**search_params)
        
        return await self._make_request(request, 'videos', cache_key)
    
    async def get_video_categories(
        self,
        region_code: str = "US"
    ) -> Dict[str, Any]:
        """
        Get available video categories for a region.
        """
        cache_key = f"categories:{region_code}"
        
        request = self.youtube.videoCategories().list(
            part='id,snippet',
            regionCode=region_code
        )
        
        return await self._make_request(request, 'videos', cache_key)
    
    async def search_channels(
        self,
        query: str,
        max_results: int = 25,
        order: str = "relevance"
    ) -> Dict[str, Any]:
        """
        Search for channels on YouTube.
        """
        cache_key = f"channel_search:{hash(f'{query}:{max_results}:{order}')}"
        
        request = self.youtube.search().list(
            part='id,snippet',
            q=query,
            type='channel',
            maxResults=min(max_results, 25),
            order=order
        )
        
        return await self._make_request(request, 'search', cache_key)
    
    async def get_quota_usage(self) -> Dict[str, Any]:
        """
        Get current quota usage information.
        """
        return {
            'quota_used': self.quota_used,
            'quota_limit': self.quota_limit,
            'quota_remaining': self.quota_limit - self.quota_used,
            'quota_reset_time': self.quota_reset_time.isoformat(),
            'usage_percentage': (self.quota_used / self.quota_limit) * 100
        }
    
    async def batch_get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get details for multiple videos, handling batching automatically.
        """
        all_videos = []
        batch_size = 50
        
        for i in range(0, len(video_ids), batch_size):
            batch_ids = video_ids[i:i + batch_size]
            result = await self.get_video_details(batch_ids)
            all_videos.extend(result.get('items', []))
            
            # Add small delay between batches to be respectful
            if i + batch_size < len(video_ids):
                await asyncio.sleep(0.1)
        
        return all_videos
    
    async def close(self):
        """Clean up resources."""
        await self.cache_manager.close()
        await self.rate_limiter.close()


# Global YouTube API instance (using default API key)
youtube_api = YouTubeAPIWrapper()


async def get_youtube_api(api_key: Optional[str] = None) -> YouTubeAPIWrapper:
    """Get YouTube API instance with optional user-provided API key."""
    if api_key and api_key.strip():
        # Create new instance with user's API key
        return YouTubeAPIWrapper(api_key=api_key.strip())
    else:
        # Use default instance with system API key
        return youtube_api


def create_youtube_api_instance(api_key: Optional[str] = None) -> YouTubeAPIWrapper:
    """Create a new YouTube API instance (synchronous version)."""
    return YouTubeAPIWrapper(api_key=api_key)