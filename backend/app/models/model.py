import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class ModelStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    READY = "READY"
    ARCHIVED = "ARCHIVED"


class ModelType(str, enum.Enum):
    PRODUCTION = "PRODUCTION"
    EXPERIMENTAL = "EXPERIMENTAL"
    DEVELOPMENT = "DEVELOPMENT"


class SignalModel(Base):
    __tablename__ = "models"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    model_type: Mapped[ModelType] = mapped_column(
        Enum(ModelType, name="model_type"),
        nullable=False,
        default=ModelType.PRODUCTION,
    )

    status: Mapped[ModelStatus] = mapped_column(
        Enum(ModelStatus, name="model_status"),
        nullable=False,
        default=ModelStatus.READY,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    observed_accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    confidence_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    board_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    maximum_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    activated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )