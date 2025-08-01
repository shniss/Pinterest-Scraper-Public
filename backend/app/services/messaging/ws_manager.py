"""
WebSocket Manager for real-time communication between backend tasks and frontend clients.

This module manages WebSocket connections and Redis pub/sub to enable real-time updates
from Celery tasks (like scraping and validation) to connected frontend clients.

Architecture:
- Each job_id can have multiple WebSocket connections (multiple browser tabs/windows)
- Redis pub/sub channel "job:{job_id}" receives messages from backend tasks
- Messages are relayed to all connected WebSocket clients for that job_id
- Automatic cleanup when all clients disconnect for a job_id
"""

import asyncio
import contextlib
from collections import defaultdict
from app.util.config import get_settings
import redis.asyncio as aioredis
from fastapi import WebSocket

REDIS_URL = get_settings().redis_url


class WSManager:
    """
    Manages WebSocket connections and Redis pub/sub for real-time task updates.

    Maintains a mapping of job_id -> set of WebSocket connections and handles
    message relay from Redis to all connected clients for each job.
    """

    def __init__(self):
        """
        Initialize the WebSocket manager with Redis connection and data structures.
        """
        # job_id -> set of WebSocket connections (multiple clients per job)
        self._conns = defaultdict(set)
        # job_id -> asyncio.Task for Redis pub/sub listener
        self._tasks = {}
        # Redis connection for pub/sub messaging
        self._redis = aioredis.from_url(REDIS_URL, decode_responses=True)

    async def connect(self, job_id: str, ws: WebSocket):
        """
        Accept a new WebSocket connection for a job_id.

        Args:
            job_id: Unique identifier for the job/session
            ws: WebSocket connection from FastAPI

        Creates a Redis pub/sub listener for this job_id if this is the first client.
        """
        await ws.accept()
        self._conns[job_id].add(ws)

        # Start Redis listener if this is the first client for this job_id
        if job_id not in self._tasks:
            self._tasks[job_id] = asyncio.create_task(self._relay(job_id))

        print(f"WS connected job={job_id} cnt={len(self._conns[job_id])}")

    async def disconnect(self, job_id: str, ws: WebSocket):
        """
        Remove a WebSocket connection for a job_id.

        Args:
            job_id: Unique identifier for the job/session
            ws: WebSocket connection to remove

        Stops the Redis listener if this was the last client for this job_id.
        """
        self._conns[job_id].discard(ws)
        print(f"WS disconnected job={job_id} cnt={len(self._conns[job_id])}")

        # Stop Redis listener if no more clients for this job_id
        if not self._conns[job_id]:
            await self._cancel_listener(job_id)

    async def _relay(self, job_id: str):
        """
        Listen to Redis pub/sub channel for a job_id and relay messages to WebSocket clients.

        Args:
            job_id: Unique identifier for the job/session

        This method runs as a background task and continuously listens for messages
        from backend tasks (scraping, validation) and forwards them to all connected
        WebSocket clients for this job_id.
        """
        chan = f"job:{job_id}"
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(chan)
        print(f"Subscribed to {chan}")

        try:
            async for msg in pubsub.listen():
                # Only process actual messages, ignore subscription confirmations
                if msg["type"] != "message":
                    continue

                # Forward the JSON payload to all connected WebSocket clients
                payload = msg["data"]  # JSON string from backend tasks
                await self._fanout(job_id, payload)
        finally:
            # Clean up Redis subscription
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(chan)
                await pubsub.close()
            print(f"Unsubscribed from {chan}")

    async def _fanout(self, job_id: str, payload: str):
        """
        Send a message to all WebSocket clients connected to a job_id.

        Args:
            job_id: Unique identifier for the job/session
            payload: JSON string message to send to all clients

        Handles dead connections by removing them from the connection set.
        """
        dead = []

        # Try to send message to all connected clients
        for ws in list(self._conns[job_id]):
            try:
                await ws.send_text(payload)
            except Exception:
                # Mark connection as dead if send fails
                dead.append(ws)

        # Remove dead connections
        for ws in dead:
            self._conns[job_id].discard(ws)

    async def _cancel_listener(self, job_id: str):
        """
        Cancel the Redis listener task and clean up resources for a job_id.

        Args:
            job_id: Unique identifier for the job/session

        Called when the last WebSocket client disconnects to free up resources.
        """
        # Cancel the background Redis listener task
        task = self._tasks.pop(job_id, None)
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

        # Clean up connection set for this job_id
        self._conns.pop(job_id, None)


# Global WebSocket manager instance
ws_manager = WSManager()
