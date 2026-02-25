"""Slack message data model."""

from datetime import datetime
from pydantic import Field
from typing import Optional, List
from .base import BaseModel


class SlackMessage(BaseModel):
    """Model representing a Slack message."""

    channel: str = Field(description="Slack channel name or ID")
    user: str = Field(description="User who posted the message")
    text: str = Field(description="Message text content")
    timestamp: datetime = Field(description="Message timestamp")
    thread_ts: Optional[str] = Field(
        default=None,
        description="Parent thread timestamp if this is a threaded reply",
    )
    reactions: List[str] = Field(
        default_factory=list,
        description="Emoji reactions on the message",
    )
    files: List[dict] = Field(
        default_factory=list,
        description="Files attached to the message",
    )
    reply_count: int = Field(
        default=0,
        description="Number of replies in thread (if parent message)",
    )
    thread_url: Optional[str] = Field(
        default=None,
        description="URL to the message thread",
    )
    edited_timestamp: Optional[datetime] = Field(
        default=None,
        description="When message was last edited",
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "msg-slack-001",
                "source": "slack",
                "channel": "incidents",
                "user": "botname",
                "text": "Perlmutter nodes down",
                "timestamp": "2025-01-20T10:30:00Z",
                "reply_count": 5,
            }
        }
