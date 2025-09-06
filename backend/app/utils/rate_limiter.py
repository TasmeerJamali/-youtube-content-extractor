"""
Rate limiting utilities for API calls.
"""

import asyncio
import time
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    calls_per_minute: int = 100
    calls_per_hour: int = 1000
    burst_limit: int = 10


class RateLimiter:
    """
    Token bucket rate limiter with support for multiple time windows.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        
        # Token bucket for minute-level limiting
        self.minute_tokens = self.config.calls_per_minute
        self.minute_last_refill = time.time()
        
        # Token bucket for hour-level limiting
        self.hour_tokens = self.config.calls_per_hour
        self.hour_last_refill = time.time()
        
        # Burst protection
        self.burst_tokens = self.config.burst_limit
        self.burst_last_refill = time.time()
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
        
        # Request timestamps for monitoring
        self.request_timestamps = []
    
    async def _refill_tokens(self):
        """Refill tokens based on elapsed time."""
        current_time = time.time()
        
        # Refill minute tokens
        minute_elapsed = current_time - self.minute_last_refill
        if minute_elapsed >= 60.0:
            self.minute_tokens = self.config.calls_per_minute
            self.minute_last_refill = current_time
        else:
            tokens_to_add = int((minute_elapsed / 60.0) * self.config.calls_per_minute)
            self.minute_tokens = min(
                self.config.calls_per_minute, 
                self.minute_tokens + tokens_to_add
            )
            if tokens_to_add > 0:
                self.minute_last_refill = current_time
        
        # Refill hour tokens
        hour_elapsed = current_time - self.hour_last_refill
        if hour_elapsed >= 3600.0:
            self.hour_tokens = self.config.calls_per_hour
            self.hour_last_refill = current_time
        else:
            tokens_to_add = int((hour_elapsed / 3600.0) * self.config.calls_per_hour)
            self.hour_tokens = min(
                self.config.calls_per_hour,
                self.hour_tokens + tokens_to_add
            )
            if tokens_to_add > 0:
                self.hour_last_refill = current_time
        
        # Refill burst tokens
        burst_elapsed = current_time - self.burst_last_refill
        if burst_elapsed >= 1.0:  # Refill every second
            self.burst_tokens = self.config.burst_limit
            self.burst_last_refill = current_time
    
    async def acquire(self, tokens: int = 1) -> bool:
        """
        Acquire tokens from the rate limiter.
        Blocks until tokens are available.
        """
        async with self._lock:
            while True:
                await self._refill_tokens()
                
                # Check if we have enough tokens in all buckets
                if (self.minute_tokens >= tokens and 
                    self.hour_tokens >= tokens and 
                    self.burst_tokens >= tokens):
                    
                    # Consume tokens
                    self.minute_tokens -= tokens
                    self.hour_tokens -= tokens
                    self.burst_tokens -= tokens
                    
                    # Record request timestamp
                    self.request_timestamps.append(time.time())
                    
                    # Keep only recent timestamps for monitoring
                    cutoff_time = time.time() - 3600  # Last hour
                    self.request_timestamps = [
                        ts for ts in self.request_timestamps if ts > cutoff_time
                    ]
                    
                    logger.debug(f"Rate limit tokens acquired. Remaining: minute={self.minute_tokens}, hour={self.hour_tokens}, burst={self.burst_tokens}")
                    return True
                
                # Calculate wait time
                wait_time = min(
                    (60.0 - (time.time() - self.minute_last_refill)) if self.minute_tokens < tokens else float('inf'),
                    (3600.0 - (time.time() - self.hour_last_refill)) if self.hour_tokens < tokens else float('inf'),
                    (1.0 - (time.time() - self.burst_last_refill)) if self.burst_tokens < tokens else float('inf')
                )
                
                if wait_time == float('inf'):
                    wait_time = 0.1  # Small default wait
                
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                await asyncio.sleep(max(0.1, wait_time))
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens without blocking.
        Returns True if tokens were acquired, False otherwise.
        """
        async with self._lock:
            await self._refill_tokens()
            
            if (self.minute_tokens >= tokens and 
                self.hour_tokens >= tokens and 
                self.burst_tokens >= tokens):
                
                self.minute_tokens -= tokens
                self.hour_tokens -= tokens
                self.burst_tokens -= tokens
                
                self.request_timestamps.append(time.time())
                
                return True
            
            return False
    
    def get_status(self) -> Dict[str, any]:
        """Get current rate limiter status."""
        current_time = time.time()
        
        # Count recent requests
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        requests_last_minute = len([ts for ts in self.request_timestamps if ts > minute_ago])
        requests_last_hour = len([ts for ts in self.request_timestamps if ts > hour_ago])
        
        return {
            'minute_tokens_available': self.minute_tokens,
            'hour_tokens_available': self.hour_tokens,
            'burst_tokens_available': self.burst_tokens,
            'requests_last_minute': requests_last_minute,
            'requests_last_hour': requests_last_hour,
            'minute_limit': self.config.calls_per_minute,
            'hour_limit': self.config.calls_per_hour,
            'burst_limit': self.config.burst_limit
        }
    
    async def reset(self):
        """Reset all token buckets to full capacity."""
        async with self._lock:
            current_time = time.time()
            self.minute_tokens = self.config.calls_per_minute
            self.hour_tokens = self.config.calls_per_hour
            self.burst_tokens = self.config.burst_limit
            self.minute_last_refill = current_time
            self.hour_last_refill = current_time
            self.burst_last_refill = current_time
            self.request_timestamps.clear()
    
    async def close(self):
        """Clean up resources."""
        pass  # No resources to clean up for now


class AdaptiveRateLimiter(RateLimiter):
    """
    Rate limiter that adapts based on API response patterns.
    """
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        super().__init__(config)
        self.error_count = 0
        self.success_count = 0
        self.adaptive_delay = 0.0
        self.last_error_time = 0.0
    
    async def record_success(self):
        """Record a successful API call."""
        self.success_count += 1
        
        # Gradually reduce adaptive delay on success
        if self.adaptive_delay > 0:
            self.adaptive_delay = max(0, self.adaptive_delay - 0.1)
    
    async def record_error(self, error_type: str = "generic"):
        """Record an API error and adjust rate limiting."""
        self.error_count += 1
        self.last_error_time = time.time()
        
        # Increase adaptive delay based on error type
        if "quota" in error_type.lower():
            self.adaptive_delay = min(60.0, self.adaptive_delay + 10.0)
        elif "rate" in error_type.lower():
            self.adaptive_delay = min(30.0, self.adaptive_delay + 5.0)
        else:
            self.adaptive_delay = min(10.0, self.adaptive_delay + 1.0)
        
        logger.warning(f"Error recorded. Adaptive delay increased to {self.adaptive_delay}s")
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens with adaptive delay."""
        # Apply adaptive delay
        if self.adaptive_delay > 0:
            await asyncio.sleep(self.adaptive_delay)
        
        return await super().acquire(tokens)
    
    def get_status(self) -> Dict[str, any]:
        """Get status including adaptive information."""
        status = super().get_status()
        status.update({
            'error_count': self.error_count,
            'success_count': self.success_count,
            'adaptive_delay': self.adaptive_delay,
            'success_rate': self.success_count / max(1, self.success_count + self.error_count)
        })
        return status