"""SLURM job data model from sacct output."""

from datetime import datetime
from pydantic import Field
from typing import Optional
from .base import BaseModel


class Job(BaseModel):
    """Model representing a SLURM job from sacct."""

    job_id: str = Field(description="SLURM job ID")
    user: str = Field(description="Job owner username")
    account: str = Field(description="SLURM account charged")
    partition: str = Field(description="Partition where job ran")
    status: str = Field(
        description="Job status (COMPLETED, FAILED, TIMEOUT, RUNNING, etc.)",
    )
    submit_time: datetime = Field(description="When job was submitted")
    start_time: Optional[datetime] = Field(
        default=None,
        description="When job started running",
    )
    end_time: Optional[datetime] = Field(
        default=None,
        description="When job ended",
    )
    elapsed_seconds: int = Field(
        default=0,
        description="Total elapsed time in seconds",
    )
    cpu_count: int = Field(default=0, description="Number of CPUs requested")
    gpu_count: int = Field(default=0, description="Number of GPUs requested")
    memory_mb: int = Field(default=0, description="Memory requested in MB")
    exit_code: Optional[int] = Field(
        default=None,
        description="Job exit code",
    )
    node_count: int = Field(default=1, description="Number of nodes used")
    nodes: Optional[str] = Field(
        default=None,
        description="Comma-separated list of nodes",
    )

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "id": "job-12345",
                "source": "slurm",
                "job_id": "12345",
                "user": "researcher",
                "status": "COMPLETED",
                "submit_time": "2025-01-20T10:00:00Z",
                "end_time": "2025-01-20T12:30:00Z",
                "cpu_count": 256,
            }
        }
