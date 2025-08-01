from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class Session(BaseModel):
    """Model for tracking Pinterest bot sessions"""

    # MongoDB ObjectId as string (will be converted to ObjectId when stored)
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))

    # Reference to the prompt that initiated this session
    prompt_id: str = Field(..., description="ObjectId of the associated prompt")

    # Current stage of the session
    stage: Literal["warmup", "scraping", "validation"] = Field(
        ..., description="Current stage of the session"
    )

    # Status of the current stage
    status: Literal["pending", "completed", "failed"] = Field(
        default="pending", description="Status of the current stage"
    )

    # Timestamp of when this session record was created/updated
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of the session update"
    )

    # Array of log messages for this session
    log: List[str] = Field(
        default_factory=list,
        description="Array of log messages for debugging and tracking",
    )

    class Config:
        # Allow population by field name (for MongoDB compatibility)
        populate_by_name = True
        # Allow extra fields (for future extensibility)
        extra = "allow"
        # Use JSON serialization for datetime
        json_encoders = {datetime: lambda v: v.isoformat()}
