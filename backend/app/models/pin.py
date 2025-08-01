from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from bson import ObjectId


class PinMetadata(BaseModel):
    """Metadata for pins and eval"""

    collected_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the pin was collected"
    )


class Pin(BaseModel):
    """Model for pins and eval"""

    # MongoDB ObjectId as string (will be converted to ObjectId when stored)
    id: str = Field(alias="_id", default_factory=lambda: str(ObjectId()))

    # Reference to the prompt that initiated this evaluation
    prompt_id: str = Field(..., description="ObjectId of the associated prompt")

    # Pin information
    image_url: str = Field(..., description="Direct URL to the pin image")
    pin_url: str = Field(..., description="URL to the Pinterest pin page")
    title: str = Field(default="", description="Title of the pin")
    description: str = Field(default="", description="Description/alt text of the pin")

    # Evaluation results
    match_score: float = Field(
        ..., ge=0.0, le=1.0, description="AI-generated match score between 0 and 1"
    )
    status: Literal["approved", "disqualified", "pending"] = Field(
        ..., description="Evaluation status"
    )
    ai_explanation: str = Field(
        ..., description="AI explanation for the evaluation decision"
    )

    # Metadata
    metadata: PinMetadata = Field(
        default_factory=PinMetadata, description="Additional metadata"
    )

    class Config:
        # Allow population by field name (for MongoDB compatibility)
        populate_by_name = True
        # Allow extra fields (for future extensibility)
        extra = "allow"
        # Use JSON serialization for datetime
        json_encoders = {datetime: lambda v: v.isoformat()}
