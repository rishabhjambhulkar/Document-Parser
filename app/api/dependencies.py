from fastapi import Request, HTTPException, status, Depends
from redis.asyncio import Redis
from app.core.config import settings
from app.db.repository import JobRepository, get_job_repository
import time

# Async Redis client for rate limiting
async def get_redis():
    redis = await Redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield redis
    finally:
        await redis.close()

async def rate_limiter(request: Request, redis: Redis = Depends(get_redis)):
    # Simple fixed window rate limiting per second
    client_ip = request.client.host
    current_time = int(time.time())
    key = f"rate_limit:{client_ip}:{current_time}"
    
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 2) # Expire in 2 seconds to be safe
        
    if count > settings.RATE_LIMIT_PER_SEC:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 10 requests per second."
        )

# Dependency to get JobRepository
async def get_repository():
    return await get_job_repository()
