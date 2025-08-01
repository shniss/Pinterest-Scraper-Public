"""
Database Connection

This module provides a connection to the MongoDB database using Motor async driver.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from app.util.config import get_settings

settings = get_settings()
client = AsyncIOMotorClient(settings.mongo_uri)
db = client.pinmatch
