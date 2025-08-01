from pydantic import BaseModel, HttpUrl, Field
from typing import Union, Literal


# definitions for the different types of messages that can be sent over the websocket by tasks
class WarmupMessage(BaseModel):
    type: Literal["warmup"]
    message: str = Field(..., min_length=1)


class ScrapedImageMessage(BaseModel):
    type: Literal["scraped_image"]
    pin_id: str
    image_title: str
    url: HttpUrl
    pin_url: HttpUrl


class ValidationMessage(BaseModel):
    type: Literal["validation"]
    pin_id: str
    score: float = Field(..., ge=0, le=1)
    label: str = Field(..., min_length=1)
    valid: bool


# union of all possible message types
UpdateMessage = Union[WarmupMessage, ScrapedImageMessage, ValidationMessage]
