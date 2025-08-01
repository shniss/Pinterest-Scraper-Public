from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class Prompt(BaseModel):
    text: str = Field(...)
    status: Literal["pending", "completed", "error"] = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.utcnow)


# MongoDB document format (for reference)
# {
#     "_id": ObjectId("..."),
#     "text": "boho minimalist bedroom",
#     "status": "pending",
#     "created_at": datetime.utcnow()
# }
