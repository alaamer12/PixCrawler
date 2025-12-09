from pydantic import BaseModel, Field


class DashboardStats(BaseModel):
    """Dashboard statistics response."""

    total_projects: int = Field(
        ...,
        description="Total number of projects owned by the user",
        ge=0,
        examples=[12]
    )
    active_jobs: int = Field(
        ...,
        description="Number of currently active (pending or running) jobs",
        ge=0,
        examples=[3]
    )
    total_datasets: int = Field(
        ...,
        description="Total number of datasets across all projects",
        ge=0,
        examples=[45]
    )
    total_images: int = Field(
        ...,
        description="Total number of images collected",
        ge=0,
        examples=[125000]
    )
    storage_used: str = Field(
        ...,
        description="Total storage used in human-readable format",
        examples=["12.5 GB"]
    )
    processing_speed: str = Field(
        ...,
        description="Average processing speed in images per minute",
        examples=["150/min"]
    )
    credits_remaining: int = Field(
        default=0,
        description="Remaining credits in user account",
        ge=0,
        examples=[5000]
    )
