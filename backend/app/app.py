"""
FastAPI backend for the Pinterest Agent Platform

This is the main FastAPI application that sets up the server and middleware and includes the routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.util.config import get_settings
from app.routes import prompts, websockets, health

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().CORS_ORIGINS,  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(prompts.router, tags=["prompts"])
app.include_router(websockets.router, tags=["websockets"])
