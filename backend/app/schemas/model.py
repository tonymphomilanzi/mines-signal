from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateModelRequest(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=150,
    )

    version: str = Field(
        min_length=1,
        max_length=50,
    )

    model_type: str = "PRODUCTION"

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    board_size: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    maximum_attempts: int = Field(
        default=3,
        ge=1,
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class UpdateModelRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=150,
    )

    version: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )

    model_type: str | None = None

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    board_size: int | None = Field(
        default=None,
        ge=1,
        le=20,
    )

    maximum_attempts: int | None = Field(
        default=None,
        ge=1,
    )

    confidence_score: float | None = Field(
        default=None,
        ge=0,
        le=100,
    )


class ModelResponse(BaseModel):
    id: UUID
    version: str
    name: str
    model_type: str
    status: str
    description: str | None
    observed_accuracy: float | None
    confidence_score: float | None
    board_size: int
    maximum_attempts: int
    created_at: datetime
    updated_at: datetime
    activated_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )


class ModelListResponse(BaseModel):
    items: list[ModelResponse]
    total: int