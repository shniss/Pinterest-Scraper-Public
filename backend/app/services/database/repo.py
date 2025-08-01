"""
Database Repository Layer

This module provides data access layer for all application entities:
- PromptRepo: Manages user prompts and their status
- PinterestAccountRepo: Handles Pinterest account credentials and settings
- SessionRepo: Tracks scraping sessions and progress
- PinRepo: Manages scraped Pinterest pins and validation results

All repositories use MongoDB with Motor async driver
Each repository provides CRUD operations for its respective entity
Only required operations are implemented

TODO:
- Break out into separate files for each entity
"""

from typing import Any, Dict, List, Optional
from bson import ObjectId
from datetime import datetime
from app.services.database.db import db
from app.models.pinterest_account import PinterestAccount
from app.models.prompt import Prompt
from app.models.session import Session
from app.models.pin import Pin
import logging

logger = logging.getLogger(__name__)


class PromptRepo:
    """
    Repository for managing user prompts and their processing status.

    Handles CRUD operations for prompts including creation, retrieval,
    status updates, and deletion. All operations are logged and include
    proper error handling.
    """

    _col = db.prompts

    async def create(self, text: str) -> Optional[str]:
        """
        Create a new prompt in the database.

        Args:
            text: The user's search prompt text

        Returns:
            str: The created prompt ID, or None if creation failed

        Raises:
            None: All exceptions are caught and logged
        """
        # Input validation
        if not text or not isinstance(text, str):
            logger.error("Invalid text parameter provided for prompt creation")
            return None

        try:
            res = Prompt(text=text, status="pending", created_at=datetime.utcnow())
            res = await self._col.insert_one(res.model_dump())
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create prompt: {e}")
            return None

    async def get(self, pid: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a prompt by its ID.

        Args:
            pid: Prompt ID to retrieve

        Returns:
            dict: Prompt data, or None if not found or error occurred
        """
        # Input validation
        if not pid or not isinstance(pid, str):
            logger.error("Invalid prompt ID provided")
            return None

        try:
            return await self._col.find_one({"_id": ObjectId(pid)})
        except Exception as e:
            logger.error(f"Failed to get prompt {pid}: {e}")
            return None

    async def update_status(self, pid: str, status: str) -> bool:
        """
        Update the status of a prompt.

        Args:
            pid: Prompt ID to update
            status: New status value

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not pid or not isinstance(pid, str):
            logger.error("Invalid prompt ID provided for status update")
            return False
        if not status or not isinstance(status, str):
            logger.error("Invalid status provided for prompt update")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(pid)}, {"$set": {"status": status}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update status for prompt {pid}: {e}")
            return False

    async def delete(self, pid: str) -> bool:
        """
        Delete a prompt from the database.

        Args:
            pid: Prompt ID to delete

        Returns:
            bool: True if deletion successful, False otherwise
        """
        # Input validation
        if not pid or not isinstance(pid, str):
            logger.error("Invalid prompt ID provided for deletion")
            return False

        try:
            await self._col.delete_one({"_id": ObjectId(pid)})
            return True
        except Exception as e:
            logger.error(f"Failed to delete prompt {pid}: {e}")
            return False


class PinterestAccountRepo:
    """
    Repository for managing Pinterest account credentials and settings.

    Handles CRUD operations for Pinterest accounts including creation,
    updates, and retrieval. Provides methods for managing account
    credentials, cookies, and proxy settings.
    """

    _col = db.pinterest_accounts

    async def create(self, account: PinterestAccount) -> Optional[str]:
        """
        Create a new Pinterest account in the database.

        Args:
            account: PinterestAccount object with credentials and settings

        Returns:
            str: The created account ID, or None if creation failed
        """
        # Input validation
        if not account or not isinstance(account, PinterestAccount):
            logger.error("Invalid PinterestAccount object provided for creation")
            return None

        try:
            res = await self._col.insert_one(account.model_dump())
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create account: {e}")
            return None

    async def update_state(self, account_id: str, state: PinterestAccount) -> bool:
        """
        Update an existing Pinterest account with new state.

        Args:
            account_id: Account ID to update
            state: New PinterestAccount state

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not account_id or not isinstance(account_id, str):
            logger.error("Invalid account ID provided for state update")
            return False
        if not state or not isinstance(state, PinterestAccount):
            logger.error("Invalid PinterestAccount state provided")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(account_id)}, {"$set": state.model_dump()}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update state for account {account_id}: {e}")
            return False

    async def get_first_account(self) -> Optional[PinterestAccount]:
        """
        Retrieve the first available Pinterest account.

        Returns:
            PinterestAccount: First account found, or None if no accounts exist
        """
        try:
            account = await self._col.find_one()
            if account:
                return await self.get_account_by_id(str(account["_id"]))
            return None
        except Exception as e:
            logger.error(f"Failed to get first account: {e}")
            return None

    async def get_account_by_id(self, account_id: str) -> Optional[PinterestAccount]:
        """
        Retrieve a Pinterest account by its ID.

        Args:
            account_id: Account ID to retrieve

        Returns:
            PinterestAccount: Account object, or None if not found or error occurred
        """
        # Input validation
        if not account_id or not isinstance(account_id, str):
            logger.error("Invalid account ID provided")
            return None

        try:
            account_data = await self._col.find_one({"_id": ObjectId(account_id)})

            if not account_data:
                logger.error(f"Account {account_id} not found")
                return None

            return PinterestAccount(**account_data)

        except Exception as e:
            logger.error(f"Failed to load account {account_id}: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return None  # Fixed: return None instead of False


class SessionRepo:
    """
    Repository for managing scraping sessions and progress tracking.

    Handles CRUD operations for sessions including creation, retrieval,
    status updates, and logging. Provides methods for tracking session
    progress through different stages (warmup, scraping, validation).
    """

    _col = db.sessions

    async def create(self, pid: str) -> Optional[str]:
        """
        Create a new session for a prompt.

        Args:
            pid: Prompt ID to associate with the session

        Returns:
            str: The created session ID, or None if creation failed
        """
        # Input validation
        if not pid or not isinstance(pid, str):
            logger.error("Invalid prompt ID provided for session creation")
            return None

        try:
            session = Session(prompt_id=pid, stage="warmup", status="pending", log=[])
            res = await self._col.insert_one(session.model_dump())
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return None

    async def get_by_prompt_id(self, prompt_id: str) -> Optional[Session]:
        """
        Retrieve a session by its associated prompt ID.

        Args:
            prompt_id: Prompt ID to find session for

        Returns:
            Session: Session object, or None if not found or error occurred
        """
        # Input validation
        if not prompt_id or not isinstance(prompt_id, str):
            logger.error("Invalid prompt ID provided for session retrieval")
            return None

        try:
            return await self._col.find_one(
                {"prompt_id": prompt_id}
            )  # Fixed: use string comparison
        except Exception as e:
            logger.error(f"Failed to get session by prompt_id {prompt_id}: {e}")
            return None

    async def get_sessionid_by_prompt_id(self, prompt_id: str) -> Optional[str]:
        """
        Get session ID by prompt ID.

        Args:
            prompt_id: Prompt ID to find session ID for

        Returns:
            str: Session ID, or None if not found or error occurred
        """
        # Input validation
        if not prompt_id or not isinstance(prompt_id, str):
            logger.error("Invalid prompt ID provided for session ID retrieval")
            return None

        try:
            session = await self._col.find_one(
                {"prompt_id": prompt_id}
            )  # Fixed: use string comparison
            return str(session["_id"]) if session else None
        except Exception as e:
            logger.error(f"Failed to get sessionid by prompt_id {prompt_id}: {e}")
            return None

    async def update_status(self, session_id: str, status: str) -> bool:
        """
        Update the status of a session.

        Args:
            session_id: Session ID to update
            status: New status value (pending, completed, failed, etc.)

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not session_id or not isinstance(session_id, str):
            logger.error("Invalid session ID provided for status update")
            return False
        if not status or not isinstance(status, str):
            logger.error("Invalid status provided for session update")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(session_id)}, {"$set": {"status": status}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update status for session {session_id}: {e}")
            return False

    async def update_stage(self, session_id: str, stage: str) -> bool:
        """
        Update the stage of a session (warmup, scraping, validation).

        Args:
            session_id: Session ID to update
            stage: New stage value

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not session_id or not isinstance(session_id, str):
            logger.error("Invalid session ID provided for stage update")
            return False
        if not stage or not isinstance(stage, str):
            logger.error("Invalid stage provided for session update")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(session_id)}, {"$set": {"stage": stage}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update stage for session {session_id}: {e}")
            return False

    async def add_log(self, session_id: str, log: str) -> bool:
        """
        Add a log entry to a session's log array.

        Args:
            session_id: Session ID to add log to
            log: Log message to add

        Returns:
            bool: True if log addition successful, False otherwise
        """
        # Input validation
        if not session_id or not isinstance(session_id, str):
            logger.error("Invalid session ID provided for log addition")
            return False
        if not log or not isinstance(log, str):
            logger.error("Invalid log message provided")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(session_id)}, {"$push": {"log": log}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to add log to session {session_id}: {e}")
            return False


class PinRepo:
    """
    Repository for managing Pinterest pins and validation results.

    Handles CRUD operations for pins including creation, retrieval,
    and updates. Provides methods for managing pin metadata, validation
    scores, and status updates. Supports bulk operations for validation workflows.
    """

    _col = db.pins

    async def create(self, pin: Pin) -> Optional[str]:
        """
        Create a new pin in the database.

        Args:
            pin: Pin object with image data and metadata

        Returns:
            str: The created pin ID, or None if creation failed
        """
        # Input validation
        if not pin or not isinstance(pin, Pin):
            logger.error("Invalid Pin object provided for creation")
            return None

        try:
            res = await self._col.insert_one(pin.model_dump())
            return str(res.inserted_id)
        except Exception as e:
            logger.error(f"Failed to create pin: {e}")
            return None

    async def get_pin_by_id(self, pin_id: str) -> Optional[Pin]:
        """
        Retrieve a pin by its ID.

        Args:
            pin_id: Pin ID to retrieve

        Returns:
            Pin: Pin object, or None if not found or error occurred
        """
        # Input validation
        if not pin_id or not isinstance(pin_id, str):
            logger.error("Invalid pin ID provided")
            return None

        try:
            return await self._col.find_one({"_id": ObjectId(pin_id)})
        except Exception as e:
            logger.error(f"Failed to get pin by id {pin_id}: {e}")
            return None

    async def get_pins_by_prompt_id(self, prompt_id: str) -> Optional[List[Pin]]:
        """
        Retrieve all pins associated with a prompt ID.

        Args:
            prompt_id: Prompt ID to find pins for

        Returns:
            List[Pin]: List of Pin objects, or None if error occurred
        """
        # Input validation
        if not prompt_id or not isinstance(prompt_id, str):
            logger.error("Invalid prompt ID provided for pin retrieval")
            return None

        try:
            # Query pins by prompt_id (using string comparison)
            cursor = self._col.find({"prompt_id": prompt_id})
            pins_data = await cursor.to_list(length=None)

            # Convert MongoDB documents to Pin objects with error handling
            pins = []
            for pin_data in pins_data:
                try:
                    # Convert ObjectId to string for the id field
                    pin_data["_id"] = str(pin_data["_id"])
                    pin = Pin(**pin_data)
                    pins.append(pin)
                except Exception as pin_error:
                    logger.error(f"Failed to create Pin object from data: {pin_error}")
                    continue

            return pins
        except Exception as e:
            logger.error(f"Failed to get pins by prompt_id {prompt_id}: {e}")
            return None

    async def update_pin_description(self, pin_id: str, description: str) -> bool:
        """
        Update the description of a pin.

        Args:
            pin_id: Pin ID to update
            description: New description text

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not pin_id or not isinstance(pin_id, str):
            logger.error("Invalid pin ID provided for description update")
            return False
        if not isinstance(description, str):
            logger.error("Invalid description provided for pin update")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(pin_id)}, {"$set": {"description": description}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update pin description for {pin_id}: {e}")
            return False

    async def update_pin_match_score(self, pin_id: str, match_score: float) -> bool:
        """
        Update the AI validation match score of a pin.

        Args:
            pin_id: Pin ID to update
            match_score: New match score (0.0 to 1.0)

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not pin_id or not isinstance(pin_id, str):
            logger.error("Invalid pin ID provided for match score update")
            return False
        if not isinstance(match_score, (int, float)) or not (0 <= match_score <= 1):
            logger.error("Invalid match score provided (must be 0.0 to 1.0)")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(pin_id)}, {"$set": {"match_score": match_score}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update pin match score for {pin_id}: {e}")
            return False

    async def update_pin_ai_explanation(self, pin_id: str, ai_explanation: str) -> bool:
        """
        Update the AI explanation for a pin's validation result.

        Args:
            pin_id: Pin ID to update
            ai_explanation: New AI explanation text

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not pin_id or not isinstance(pin_id, str):
            logger.error("Invalid pin ID provided for AI explanation update")
            return False
        if not isinstance(ai_explanation, str):
            logger.error("Invalid AI explanation provided for pin update")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(pin_id)}, {"$set": {"ai_explanation": ai_explanation}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update pin ai explanation for {pin_id}: {e}")
            return False

    async def update_pin_status(self, pin_id: str, status: str) -> bool:
        """
        Update the status of a pin (pending, approved, disqualified).

        Args:
            pin_id: Pin ID to update
            status: New status value

        Returns:
            bool: True if update successful, False otherwise
        """
        # Input validation
        if not pin_id or not isinstance(pin_id, str):
            logger.error("Invalid pin ID provided for status update")
            return False
        if not status or not isinstance(status, str):
            logger.error("Invalid status provided for pin update")
            return False

        try:
            await self._col.update_one(
                {"_id": ObjectId(pin_id)}, {"$set": {"status": status}}
            )
            return True
        except Exception as e:
            logger.error(f"Failed to update pin status for {pin_id}: {e}")
            return False
