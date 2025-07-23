"""
Rate Limiting Service
Implements comprehensive rate limiting with Redis backend
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json
import logging
from enum import Enum

from app.core.database import db_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

class RateLimitType(Enum):
    """Rate limit types"""
    API_CALLS = "api_calls"
    EMAIL_SENDS = "email_sends"
    LOGIN_ATTEMPTS = "login_attempts"
    PASSWORD_RESETS = "password_resets"
    TEMPLATE_CREATES = "template_creates"
    USER_REGISTRATION = "user_registration"

class RateLimitWindow(Enum):
    """Rate limit time windows"""
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"

class RateLimitResult:
    """Rate limit check result"""
    
    def __init__(self, allowed: bool, limit: int, remaining: int, reset_time: datetime, 
                 retry_after: Optional[int] = None):
        self.allowed = allowed
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "limit": self.limit,
            "remaining": self.remaining,
            "reset_time": self.reset_time.isoformat(),
            "retry_after": self.retry_after
        }

class RateLimitService:
    """Rate limiting service with Redis backend"""
    
    def __init__(self):
        self.redis_client = db_manager.get_redis_client()
        
        # Rate limit configurations
        self.rate_limits = {
            # API Rate Limits
            RateLimitType.API_CALLS: {
                RateLimitWindow.MINUTE: settings.API_RATE_LIMIT_PER_MINUTE,
                RateLimitWindow.HOUR: settings.API_RATE_LIMIT_PER_HOUR,
                RateLimitWindow.DAY: settings.API_RATE_LIMIT_PER_DAY,
            },
            
            # Email Rate Limits
            RateLimitType.EMAIL_SENDS: {
                RateLimitWindow.MINUTE: settings.EMAIL_BURST_LIMIT,
                RateLimitWindow.DAY: settings.UNVERIFIED_DAILY_LIMIT,  # Default, varies by user
            },
            
            # Security Rate Limits
            RateLimitType.LOGIN_ATTEMPTS: {
                RateLimitWindow.MINUTE: 5,
                RateLimitWindow.HOUR: 20,
                RateLimitWindow.DAY: 100,
            },
            
            RateLimitType.PASSWORD_RESETS: {
                RateLimitWindow.HOUR: 3,
                RateLimitWindow.DAY: 10,
            },
            
            # Feature Rate Limits
            RateLimitType.TEMPLATE_CREATES: {
                RateLimitWindow.HOUR: 10,
                RateLimitWindow.DAY: 50,
            },
            
            RateLimitType.USER_REGISTRATION: {
                RateLimitWindow.HOUR: 5,
                RateLimitWindow.DAY: 20,
            },
        }
    
    def _get_window_seconds(self, window: RateLimitWindow) -> int:
        """Get window duration in seconds"""
        window_map = {
            RateLimitWindow.MINUTE: 60,
            RateLimitWindow.HOUR: 3600,
            RateLimitWindow.DAY: 86400,
            RateLimitWindow.WEEK: 604800,
            RateLimitWindow.MONTH: 2592000,
        }
        return window_map[window]
    
    def _get_redis_key(self, rate_type: RateLimitType, identifier: str, 
                      window: RateLimitWindow) -> str:
        """Generate Redis key for rate limiting"""
        now = datetime.utcnow()
        
        if window == RateLimitWindow.MINUTE:
            time_bucket = f"{now.year}-{now.month:02d}-{now.day:02d}-{now.hour:02d}-{now.minute:02d}"
        elif window == RateLimitWindow.HOUR:
            time_bucket = f"{now.year}-{now.month:02d}-{now.day:02d}-{now.hour:02d}"
        elif window == RateLimitWindow.DAY:
            time_bucket = f"{now.year}-{now.month:02d}-{now.day:02d}"
        elif window == RateLimitWindow.WEEK:
            week = now.isocalendar()[1]
            time_bucket = f"{now.year}-W{week:02d}"
        else:  # MONTH
            time_bucket = f"{now.year}-{now.month:02d}"
        
        return f"rate_limit:{rate_type.value}:{identifier}:{window.value}:{time_bucket}"
    
    def _get_reset_time(self, window: RateLimitWindow) -> datetime:
        """Get reset time for the current window"""
        now = datetime.utcnow()
        
        if window == RateLimitWindow.MINUTE:
            return now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        elif window == RateLimitWindow.HOUR:
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif window == RateLimitWindow.DAY:
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        elif window == RateLimitWindow.WEEK:
            days_ahead = 6 - now.weekday()  # Monday is 0
            return (now + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)
        else:  # MONTH
            if now.month == 12:
                return now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                return now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    async def check_rate_limit(self, rate_type: RateLimitType, identifier: str, 
                              window: RateLimitWindow, custom_limit: Optional[int] = None,
                              increment: int = 1) -> RateLimitResult:
        """
        Check and update rate limit for given parameters
        
        Args:
            rate_type: Type of rate limit
            identifier: Unique identifier (user_id, ip_address, etc.)
            window: Time window for the limit
            custom_limit: Override default limit
            increment: Amount to increment counter by
        
        Returns:
            RateLimitResult with limit check details
        """
        try:
            # Get limit for this rate type and window
            limit = custom_limit or self.rate_limits.get(rate_type, {}).get(window, 1000)
            
            # Generate Redis key
            redis_key = self._get_redis_key(rate_type, identifier, window)
            
            # Get current count
            current_count = await self._get_current_count(redis_key)
            
            # Calculate remaining and reset time
            remaining = max(0, limit - current_count)
            reset_time = self._get_reset_time(window)
            retry_after = None
            
            # Check if limit exceeded
            if current_count + increment > limit:
                retry_after = int((reset_time - datetime.utcnow()).total_seconds())
                return RateLimitResult(
                    allowed=False,
                    limit=limit,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=retry_after
                )
            
            # Increment counter
            await self._increment_counter(redis_key, increment, self._get_window_seconds(window))
            
            # Update remaining count
            remaining = max(0, limit - (current_count + increment))
            
            return RateLimitResult(
                allowed=True,
                limit=limit,
                remaining=remaining,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # Fail open - allow request if rate limiting fails
            return RateLimitResult(
                allowed=True,
                limit=limit or 1000,
                remaining=999,
                reset_time=datetime.utcnow() + timedelta(hours=1)
            )
    
    async def _get_current_count(self, redis_key: str) -> int:
        """Get current count from Redis"""
        try:
            count = await asyncio.get_event_loop().run_in_executor(
                None, self.redis_client.get, redis_key
            )
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Failed to get rate limit count: {e}")
            return 0
    
    async def _increment_counter(self, redis_key: str, increment: int, ttl: int):
        """Increment counter in Redis with TTL"""
        try:
            pipe = self.redis_client.pipeline()
            pipe.incrby(redis_key, increment)
            pipe.expire(redis_key, ttl)
            await asyncio.get_event_loop().run_in_executor(None, pipe.execute)
        except Exception as e:
            logger.error(f"Failed to increment rate limit counter: {e}")
    
    async def check_email_rate_limit(self, user_id: int, is_verified: bool, 
                                   email_count: int = 1) -> RateLimitResult:
        """Check email sending rate limits based on user verification status"""
        try:
            # Determine daily limit based on verification status
            if is_verified:
                daily_limit = settings.VERIFIED_DAILY_LIMIT
                if daily_limit == -1:  # Unlimited
                    daily_limit = 999999999
            else:
                daily_limit = settings.UNVERIFIED_DAILY_LIMIT
            
            # Check burst limit (per minute)
            burst_result = await self.check_rate_limit(
                RateLimitType.EMAIL_SENDS,
                str(user_id),
                RateLimitWindow.MINUTE,
                custom_limit=settings.EMAIL_BURST_LIMIT,
                increment=email_count
            )
            
            if not burst_result.allowed:
                return burst_result
            
            # Check daily limit
            daily_result = await self.check_rate_limit(
                RateLimitType.EMAIL_SENDS,
                str(user_id),
                RateLimitWindow.DAY,
                custom_limit=daily_limit,
                increment=email_count
            )
            
            return daily_result
            
        except Exception as e:
            logger.error(f"Email rate limit check failed: {e}")
            # Fail open for email sending
            return RateLimitResult(
                allowed=True,
                limit=daily_limit or settings.UNVERIFIED_DAILY_LIMIT,
                remaining=999,
                reset_time=datetime.utcnow() + timedelta(days=1)
            )
    
    async def check_api_rate_limit(self, identifier: str, endpoint: str) -> RateLimitResult:
        """Check API rate limits with multiple windows"""
        try:
            # Combine identifier and endpoint for granular limiting
            rate_key = f"{identifier}:{endpoint}"
            
            # Check per-minute limit first (most restrictive)
            minute_result = await self.check_rate_limit(
                RateLimitType.API_CALLS,
                rate_key,
                RateLimitWindow.MINUTE
            )
            
            if not minute_result.allowed:
                return minute_result
            
            # Check hourly limit
            hour_result = await self.check_rate_limit(
                RateLimitType.API_CALLS,
                rate_key,
                RateLimitWindow.HOUR
            )
            
            if not hour_result.allowed:
                return hour_result
            
            # Check daily limit
            daily_result = await self.check_rate_limit(
                RateLimitType.API_CALLS,
                rate_key,
                RateLimitWindow.DAY
            )
            
            return daily_result
            
        except Exception as e:
            logger.error(f"API rate limit check failed: {e}")
            return RateLimitResult(
                allowed=True,
                limit=settings.API_RATE_LIMIT_PER_MINUTE,
                remaining=999,
                reset_time=datetime.utcnow() + timedelta(minutes=1)
            )
    
    async def get_rate_limit_status(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive rate limit status for a user"""
        try:
            status = {}
            
            # Email limits
            email_daily = await self.check_rate_limit(
                RateLimitType.EMAIL_SENDS,
                str(user_id),
                RateLimitWindow.DAY,
                increment=0  # Don't increment, just check
            )
            
            email_burst = await self.check_rate_limit(
                RateLimitType.EMAIL_SENDS,
                str(user_id),
                RateLimitWindow.MINUTE,
                increment=0
            )
            
            status["email_limits"] = {
                "daily": email_daily.to_dict(),
                "burst": email_burst.to_dict()
            }
            
            # API limits
            api_limits = await self.check_rate_limit(
                RateLimitType.API_CALLS,
                str(user_id),
                RateLimitWindow.HOUR,
                increment=0
            )
            
            status["api_limits"] = api_limits.to_dict()
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"error": "Failed to retrieve rate limit status"}

# Global instance
rate_limit = RateLimitService()
