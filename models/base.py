"""Base model for all DOE_METRICS_REPORTER data types."""

from datetime import datetime, timezone
from pydantic import BaseModel as PydanticBaseModel, Field
from typing import Optional


class BaseModel(PydanticBaseModel):
    """Base class for all cached data models.

    Provides common fields for tracking source, cache timestamp, and origin.
    """

    id: str = Field(description="Unique identifier for this data")
    source: str = Field(description="Source system (e.g., 'google_docs', 'slack')")
    cached_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this data was cached",
    )
    cached_from: str = Field(
        description="Origin reference (URL, doc_id, query, etc.)"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }
