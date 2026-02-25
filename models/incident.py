"""Incident data model for tracking system issues and maintenance."""

from datetime import datetime
from pydantic import Field
from typing import Optional, List
from .base import BaseModel


class Incident(BaseModel):
    """Model representing a system incident or maintenance event."""

    title: str = Field(description="Incident title/summary")
    description: str = Field(description="Detailed incident description")
    date_found: datetime = Field(description="When the incident was discovered")
    date_resolved: Optional[datetime] = Field(
        default=None, description="When incident was resolved"
    )
    severity: str = Field(
        description="Severity level: critical, high, medium, low",
        pattern="^(critical|high|medium|low)$",
    )
    systems_affected: List[str] = Field(
        default_factory=list,
        description="List of affected systems (e.g., perlmutter, archive, dtn)",
    )
    resolution_notes: str = Field(
        default="",
        description="How the incident was resolved",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="URLs/references to source documents (Google Docs links, Slack messages, etc.)",
    )
    impact_summary: Optional[str] = Field(
        default=None,
        description="Summary of impact on users/workloads",
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "inc-2025-01-001",
                "source": "google_docs",
                "title": "Perlmutter maintenance window",
                "severity": "high",
                "systems_affected": ["perlmutter"],
                "date_found": "2025-01-20T10:30:00Z",
            }
        }
