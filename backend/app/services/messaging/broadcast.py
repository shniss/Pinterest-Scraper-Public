"""
broadcast.py

Broadcasts messages to the frontend via Redis pub/sub
"""

import json
import redis
from app.util.config import get_settings
from typing import Dict, Any

_redis = redis.Redis.from_url(get_settings().redis_url, decode_responses=True)


def broadcast(job_id: str, message: Dict[str, Any]) -> None:
    # Push a JSON event onto the Redis pub/sub channel for this job.
    # The message should already be a validated Pydantic model dict from the tasks.
    try:
        _redis.publish(f"job:{job_id}", json.dumps(message))
    except Exception as e:
        # TODO: handle more gracefully - should log / properly display error to user
        raise ValueError(f"Failed to broadcast message: {e}")
