"""
Prompt routes for the Pinterest Agent Platform API.

This module handles all prompt-related endpoints including creation
and management of user search prompts.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from celery import chain

from app.services.database.repo import PromptRepo, SessionRepo
from app.tasks.warmup_and_scraping import warm_up_scraping
from app.tasks.validation import validate

router = APIRouter()


class PromptIn(BaseModel):
    text: str


class PromptOut(BaseModel):
    id: str


@router.post("/prompts", response_model=PromptOut)
async def create_prompt(p: PromptIn):
    """
    Creates a new prompt and session in mongodb
    Starts the task chain
    Returns the prompt id to the frontend so it can be used to connect to the websocket
    TODO: return the session id instead of the prompt id
    """
    # Create a new prompt and session in mongodb
    promptRepo = PromptRepo()
    pid = await promptRepo.create(p.text)

    session_repo = SessionRepo()
    session_id = await session_repo.create(pid)

    # Start the task chain
    pipe = chain(
        warm_up_scraping.si(pid, session_id, p.text),  # freeze the initial arg
        validate.si(pid, session_id, p.text),  # receives scrape's return
    )
    pipe.apply_async()

    # Return the prompt id to the frontend so it can be used to connect to the websocket
    return {"id": pid}
