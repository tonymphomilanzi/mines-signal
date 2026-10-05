import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "signals.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    feature_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    board_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    mine_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    top_positions: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=list,
    )

    position_predictions: Mapped[
        list[dict[str, Any]]
    ] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
 
