"""
config.py

Contains the configuration for the application
helper to avoid repeating os.getenv calls
"""

import os
from functools import lru_cache
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    mongo_uri: str
    redis_url: str
    openai_key: str

    def __init__(self):
        self.mongo_uri = os.getenv("MONGO_URI")
        self.redis_url = os.getenv("REDIS_URL")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        # Handle CORS_ORIGINS - support both string and JSON array formats
        cors_origins = os.getenv("CORS_ORIGINS")
        if cors_origins:
            # If it's a JSON array string, parse it
            if cors_origins.startswith("[") and cors_origins.endswith("]"):
                import json
                try:
                    self.CORS_ORIGINS = json.loads(cors_origins)
                except json.JSONDecodeError:
                    self.CORS_ORIGINS = [cors_origins]
            else:
                # If it's a comma-separated string, split it
                self.CORS_ORIGINS = [origin.strip() for origin in cors_origins.split(",")]
        else:
            self.CORS_ORIGINS = ["http://localhost", "http://localhost:80", "http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
