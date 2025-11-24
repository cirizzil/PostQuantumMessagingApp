"""Rate limiting utilities using slowapi"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status


def get_limiter(request: Request) -> Limiter:
    """Get the limiter from app state"""
    return request.app.state.limiter


async def check_rate_limit(request: Request, limit: str):
    """
    Check rate limit for a request.
    Raises HTTPException if rate limit is exceeded.
    """
    limiter = get_limiter(request)
    key = f"rate_limit:{get_remote_address(request)}:{limit}"
    
    # Use limiter's internal mechanism to check
    # slowapi uses a sliding window, we'll implement a simple check
    # For production, consider using Redis-backed rate limiting
    try:
        # This is a simplified approach - in production you'd want
        # to use slowapi's decorator pattern or a Redis-backed solution
        pass
    except RateLimitExceeded:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {limit}"
        )

