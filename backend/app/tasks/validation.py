"""
Pinterest Pin Validation Task

This Celery task validates scraped Pinterest pins against the user's original prompt.
The task uses AI-powered image evaluation to score how well each pin matches the prompt.

Validation Process:
1. Retrieves all scraped pins for a given prompt from the database
2. Uses OpenAI's GPT-4 Vision to evaluate each image against the prompt
3. Scores images on object relevance and style matching (0-1 scale)
4. Updates pin status (approved/disqualified) based on minimum score threshold
5. Broadcasts validation results to frontend for real-time updates

Architecture:
- Asynchronous processing of multiple pins
- AI-powered image evaluation with timeout protection
- Real-time progress updates via WebSocket broadcasting
- Database updates for pin status and scores
- Comprehensive error handling and logging

The validation ensures that only high-quality, relevant images are presented to users.
"""

from app.services.celery_app import celery_app
from app.services.messaging.broadcast import broadcast
from app.services.database.db import db
from app.models.update_messages import ValidationMessage
from bson import ObjectId
import time
import random
from app.services.database.repo import SessionRepo, PinRepo, PromptRepo
import asyncio
import nest_asyncio
from app.services.automation.image_evaluator import score_image_against_prompt

# Configuration constants
VALIDATION_CONFIG = {
    "min_score": 0.5,
    "timeout_seconds": 30,
    "max_retries": 3
}

@celery_app.task(name="app.tasks.validation")
def validate(pid: str, session_id: str, prompt: str):
    """
    Main Celery task that validates scraped Pinterest pins against the user's prompt.
    
    This task orchestrates the validation workflow:
    1. Validates input parameters
    2. Sets up async event loop management
    3. Retrieves pins from database for validation
    4. Processes each pin through AI evaluation
    5. Updates database with validation results
    6. Broadcasts results to frontend in real-time
    
    Args:
        pid: Prompt ID for retrieving pins and tracking validation
        session_id: Session ID for progress tracking and logging
        prompt: Original user prompt used for image evaluation
        
    Returns:
        None (validation results are communicated via WebSocket broadcasts)
        
    Raises:
        ValueError: If input parameters are invalid
        RuntimeError: If validation process fails
    """
    # Input validation
    if not pid or not session_id or not prompt:
        raise ValueError("All parameters (pid, session_id, prompt) must be provided and non-empty")
    
    if not isinstance(pid, str) or not isinstance(session_id, str) or not isinstance(prompt, str):
        raise TypeError("All parameters must be strings")
    try:
        # Apply nest_asyncio only when we need it for the task
        try:
            nest_asyncio.apply()
        except ValueError as e:
            if "uvloop" in str(e):
                print("uvloop detected, nest_asyncio not needed")
            else:
                print(f"nest_asyncio error: {e}")
        
        # Get the current event loop or create a new one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the async function in the current loop
        return loop.run_until_complete(_validate_async(pid, session_id, prompt))
    except Exception as e:
        print(f"Task failed with error: {e}")
        import traceback
        print(f"Task traceback: {traceback.format_exc()}")
        return None
    finally:
        # Clean up any remaining tasks in the event loop
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_closed():
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception as cleanup_error:
            print(f"Error during cleanup: {cleanup_error}")

    

async def _validate_async(pid: str, session_id: str, prompt: str):
    """
    Async implementation of the pin validation workflow.
    
    This function handles the core validation logic:
    - Database repository initialization
    - Session status management
    - Pin retrieval and processing
    - AI-powered image evaluation
    - Database updates and real-time broadcasting
    
    Args:
        pid: Prompt ID for database operations
        session_id: Session ID for progress tracking
        prompt: User's original prompt for image evaluation
        
    Raises:
        RuntimeError: If validation process fails
    
    #TODO:
        -while we want real time updates to the frontend over websockets, we should switch to batching the mongodb updates so all images are evaluated and then the results are send to mongo in a single message
    """
    try:
        # Initialize database repositories for session, pin, and prompt operations
        session_repo = SessionRepo()
        pin_repo = PinRepo()
        prompt_repo = PromptRepo()

        # Update session status to indicate validation phase
        try:
            await session_repo.update_stage(session_id, "validation")
        except Exception as e:
            print(f"Failed to update session {session_id} stage: {e}")
            raise RuntimeError(f"Failed to initialize validation session {session_id}: {e}")

        # Retrieve all scraped pins for this prompt from database
        pins = await pin_repo.get_pins_by_prompt_id(pid)
        
        print(f"Found {len(pins) if pins else 0} pins for prompt {pid}")
        
        # Handle case where no pins were found for validation
        if pins is None:
            print(f"No pins found for prompt {pid}")
            await session_repo.update_status(session_id, "completed")
            return

        # Handle case where pins list is empty
        if not pins:
            print(f"Empty pins list for prompt {pid}")
            await session_repo.update_status(session_id, "completed")
            return

        # Process each pin through AI-powered validation
        for pin in pins:
            try:
                # Evaluate image against prompt using AI with timeout protection
                try:
                    score, detail = await asyncio.wait_for(
                        asyncio.to_thread(score_image_against_prompt, pin.image_url, prompt),
                        timeout=VALIDATION_CONFIG["timeout_seconds"]
                    )
                except asyncio.TimeoutError:
                    print(f"Image evaluation timed out for pin {pin.id}")
                    await session_repo.add_log(session_id, f"Pin {pin.id} evaluation timed out")
                    score = 0.0
                    detail = {"explanation": "Evaluation timed out"}
                
                # Update pin status based on validation score threshold
                if score < VALIDATION_CONFIG["min_score"]:
                    await pin_repo.update_pin_status(pin.id, "disqualified")
                    await session_repo.add_log(session_id, f"Pin {pin.id} disqualified: {score}, {detail}")
                else:
                    await pin_repo.update_pin_status(pin.id, "approved")
                    await session_repo.add_log(session_id, f"Pin {pin.id} approved: {score}, {detail}")
                
                # Store validation results in database
                await pin_repo.update_pin_match_score(pin.id, score)
                await pin_repo.update_pin_ai_explanation(pin.id, detail.get("explanation", ""))

                # Prepare validation result for frontend broadcasting
                # Convert score to float and ensure it's in 0-1 range
                score_float = float(score) if score is not None else 0.0
                score_float = max(0.0, min(1.0, score_float))  # Clamp to 0-1 range
                
                # Create validation message for real-time frontend updates
                updateMessage = ValidationMessage(
                    type="validation",
                    pin_id=pin.id,
                    score=score_float,
                    label=detail.get("explanation", ""),
                    valid=score_float >= VALIDATION_CONFIG["min_score"]
                )
                
                # Broadcast validation result to frontend via WebSocket
                try:
                    broadcast(pid, updateMessage.model_dump(mode='json'))
                except Exception as broadcast_error:
                    print(f"Broadcast error: {broadcast_error}")
                    await session_repo.add_log(session_id, f"Broadcast error: {broadcast_error}")
                    
            except Exception as pin_error:
                # Handle individual pin validation failures gracefully
                print(f"Error processing pin {pin.id} during validation: {pin_error}")
                await session_repo.add_log(session_id, f"Validation failed for pin {pin.id}: {pin_error}")

        # Mark validation process as completed
        await session_repo.update_status(session_id, "completed")
        await prompt_repo.update_status(pid, "completed")

    except Exception as e:
        # Handle validation workflow failures
        print(f"Exception caught: {e}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        
        # Update session status to failed and log error
        try:
            if session_repo and session_id:
                await session_repo.update_status(session_id, "failed")
                await session_repo.add_log(session_id, f"Validation task failed: {e}")
        except Exception as log_error:
            print(f"Error logging validation failure: {log_error}")
            
        # Update prompt status to error
        try:
            if prompt_repo and pid:
                await prompt_repo.update_status(pid, "error")
        except Exception as prompt_error:
            print(f"Error updating prompt status after validation failure: {prompt_error}")
        
        # Log the original error for debugging
        print(f"Original validation error: {e}")
        print(f"Error type: {type(e).__name__}")
        
        # Re-raise the exception to ensure the task is marked as failed
        raise