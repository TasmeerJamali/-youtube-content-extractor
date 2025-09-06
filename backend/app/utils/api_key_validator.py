"""
YouTube API key validation utilities.
"""

import logging
from typing import Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class APIKeyValidator:
    """Validates YouTube API keys."""
    
    @staticmethod
    async def validate_api_key(api_key: str) -> Dict[str, Any]:
        """
        Validate a YouTube API key by making a simple test request.
        
        Returns:
            Dict with validation status and details
        """
        if not api_key or not api_key.strip():
            return {
                "valid": False,
                "error": "API key is empty",
                "error_code": "EMPTY_KEY"
            }
        
        try:
            # Create YouTube service with the provided key
            youtube = build("youtube", "v3", developerKey=api_key.strip())
            
            # Make a simple test request to validate the key
            request = youtube.search().list(
                part="id",
                q="test",
                type="video",
                maxResults=1
            )
            
            # Execute the request
            response = request.execute()
            
            return {
                "valid": True,
                "error": None,
                "error_code": None,
                "quota_used": 100  # Search operation costs 100 quota units
            }
            
        except HttpError as e:
            error_content = e.content.decode('utf-8') if e.content else "No error content"
            
            if e.resp.status == 400:
                if "API_KEY_INVALID" in error_content:
                    return {
                        "valid": False,
                        "error": "Invalid API key format",
                        "error_code": "INVALID_FORMAT"
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Bad request: {error_content}",
                        "error_code": "BAD_REQUEST"
                    }
            
            elif e.resp.status == 403:
                if "quotaExceeded" in error_content:
                    return {
                        "valid": True,  # Key is valid but quota exceeded
                        "error": "API key is valid but quota exceeded",
                        "error_code": "QUOTA_EXCEEDED"
                    }
                elif "keyInvalid" in error_content:
                    return {
                        "valid": False,
                        "error": "Invalid API key",
                        "error_code": "KEY_INVALID"
                    }
                elif "accessNotConfigured" in error_content:
                    return {
                        "valid": False,
                        "error": "YouTube API is not enabled for this key",
                        "error_code": "API_NOT_ENABLED"
                    }
                else:
                    return {
                        "valid": False,
                        "error": f"Access forbidden: {error_content}",
                        "error_code": "ACCESS_FORBIDDEN"
                    }
            
            else:
                return {
                    "valid": False,
                    "error": f"API error {e.resp.status}: {error_content}",
                    "error_code": f"HTTP_{e.resp.status}"
                }
                
        except Exception as e:
            logger.error(f"Unexpected error validating API key: {str(e)}")
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}",
                "error_code": "VALIDATION_ERROR"
            }
    
    @staticmethod
    def get_api_key_help_message() -> Dict[str, Any]:
        """Get helpful information about getting a YouTube API key."""
        return {
            "title": "How to get a YouTube API Key",
            "steps": [
                "1. Go to Google Cloud Console: https://console.cloud.google.com/",
                "2. Create a new project or select an existing one",
                "3. Enable the YouTube Data API v3",
                "4. Go to 'Credentials' and click 'Create Credentials'",
                "5. Select 'API Key' and copy the generated key",
                "6. (Optional) Restrict the API key to YouTube Data API"
            ],
            "links": {
                "console": "https://console.cloud.google.com/",
                "documentation": "https://developers.google.com/youtube/v3/getting-started",
                "pricing": "https://developers.google.com/youtube/v3/determine_quota_cost"
            },
            "quota_info": {
                "daily_limit": 10000,
                "search_cost": 100,
                "video_details_cost": 1,
                "free_tier": "Yes, completely free with daily quota"
            }
        }


# Global validator instance
api_key_validator = APIKeyValidator()


async def validate_youtube_api_key(api_key: str) -> Dict[str, Any]:
    """Validate YouTube API key."""
    return await api_key_validator.validate_api_key(api_key)


def get_api_key_help() -> Dict[str, Any]:
    """Get API key help information."""
    return api_key_validator.get_api_key_help_message()