"""System utilization and metrics data model."""

from datetime import datetime
from pydantic import Field
from typing import Optional
from .base import BaseModel


class UtilizationMetric(BaseModel):
    """Model representing system utilization metrics."""

    system: str = Field(description="System name (e.g., perlmutter, archive, dtn)")
    metric_type: str = Field(
        description="Type of metric (cpu, gpu, memory, network, storage)"
    )
    timestamp: datetime = Field(description="When metric was recorded")
    value: float = Field(description="Metric value (percentage or count)")
    unit: str = Field(default="%", description="Unit of measurement")
    node_id: Optional[str] = Field(
        default=None,
        description="Specific node ID if node-level metric",
    )
    gpu_id: Optional[int] = Field(
        default=None,
        description="GPU index if GPU-level metric",
    )
    threshold_warning: Optional[float] = Field(
        default=None,
        description="Warning threshold value",
    )
    threshold_critical: Optional[float] = Field(
        default=None,
        description="Critical threshold value",
    )
    status: str = Field(
        default="normal",
        description="Status: normal, warning, critical",
        pattern="^(normal|warning|critical)$",
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "util-pm-001",
                "source": "elasticsearch",
                "system": "perlmutter",
                "metric_type": "gpu",
                "timestamp": "2025-01-26T14:30:00Z",
                "value": 85.5,
                "unit": "%",
                "status": "warning",
            }
        }
