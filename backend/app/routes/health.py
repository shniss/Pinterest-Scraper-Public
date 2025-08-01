"""
Health check routes for the Pinterest Agent Platform

This module provides health check endpoints for monitoring and load balancers.
"""

from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from app.util.config import get_settings
import redis.asyncio as redis
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Checks:
    - Application status
    - MongoDB connectivity
    - Redis connectivity
    
    Returns:
        dict: Health status with detailed information
    """
    health_status = {
        "status": "healthy",
        "service": "pinterest-agent-backend",
        "checks": {
            "application": "healthy",
            "mongodb": "unknown",
            "redis": "unknown"
        }
    }
    
    # Check MongoDB connectivity
    try:
        settings = get_settings()
        # Use the MongoDB URI directly (it should already be configured for Docker)
        mongo_uri = settings.mongo_uri
        if not mongo_uri:
            raise ValueError("MongoDB URI not configured")
        client = AsyncIOMotorClient(mongo_uri)
        await client.admin.command('ping')
        health_status["checks"]["mongodb"] = "healthy"
        client.close()
    except Exception as e:
        logger.error(f"MongoDB health check failed: {e}")
        health_status["checks"]["mongodb"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check Redis connectivity
    try:
        settings = get_settings()
        # Use the Redis URL directly (it should already be configured for Docker)
        redis_url = settings.redis_url
        if not redis_url:
            raise ValueError("Redis URL not configured")
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        await redis_client.close()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status["checks"]["redis"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Determine overall status
    if health_status["checks"]["mongodb"] == "unhealthy" and health_status["checks"]["redis"] == "unhealthy":
        health_status["status"] = "unhealthy"
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    return health_status

@router.get("/health/simple")
async def simple_health_check():
    """
    Simple health check endpoint for basic monitoring.
    
    Returns:
        dict: Simple health status
    """
    return {"status": "healthy", "service": "pinterest-agent-backend"} 