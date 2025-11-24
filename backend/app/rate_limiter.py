"""Simple in-memory rate limiter for FastAPI"""
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import HTTPException, status
from slowapi.util import get_remote_address
from fastapi import Request


class SimpleRateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Check if request is allowed within rate limit"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=window_seconds)
        
        # Clean old entries
        self._requests[key] = [
            req_time for req_time in self._requests[key]
            if req_time > window_start
        ]
        
        # Check if limit exceeded
        if len(self._requests[key]) >= limit:
            return False
        
        # Record this request
        self._requests[key].append(now)
        return True


# Global rate limiter instance
_rate_limiter = SimpleRateLimiter()


def check_rate_limit(request: Request, limit: str):
    """
    Check rate limit. Format: "5/minute" or "10/hour"
    Raises HTTPException if limit exceeded.
    """
    # Parse limit string (e.g., "5/minute" -> 5 requests per 60 seconds)
    try:
        limit_num, period = limit.split("/")
        limit_num = int(limit_num)
        
        if period == "minute":
            window_seconds = 60
        elif period == "hour":
            window_seconds = 3600
        elif period == "second":
            window_seconds = 1
        else:
            raise ValueError(f"Unknown period: {period}")
    except ValueError as e:
        raise ValueError(f"Invalid rate limit format: {limit}. Use format like '5/minute'")
    
    # Get client identifier
    client_id = get_remote_address(request)
    key = f"{client_id}:{limit}"
    
    # Check rate limit
    if not _rate_limiter.is_allowed(key, limit_num, window_seconds):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit}. Please try again later."
        )

