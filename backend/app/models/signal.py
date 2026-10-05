import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


# ============================================================
# SIGNAL STATUS
# ============================================================

class SignalStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ANALYZED = "ANALYZED"
    CONFIRMED = "CONFIRMED"
    PUBLISHED = "PUBLISHED"
    RESULT_PENDING = "RESULT_PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ============================================================
# PREDICTION ENGINE
# ============================================================

class PredictionEngine(str, enum.Enum):
    """
    Engine used to generate the production prediction
    for a signal.
    """

    PATTERN = "PATTERN"
    ML = "ML"


# ============================================================
# SIGNAL
# ============================================================

class Signal(Base):
    __tablename__ = "signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    signal_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    game: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Mines Classic",
    )

    board_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
    )

    mine_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # ========================================================
    # SELECTED MODEL
    # ========================================================

    model_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "models.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    # ========================================================
    # PREDICTION ENGINE
    # ========================================================

    prediction_engine: Mapped[PredictionEngine] = mapped_column(
        Enum(
            PredictionEngine,
            name="prediction_engine",
        ),
        nullable=False,
        default=PredictionEngine.PATTERN,
        index=True,
    )

    # ========================================================
    # ANALYSIS
    # ========================================================

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
    )

    recommended_positions: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=list,
    )

    # ========================================================
    # STATUS
    # ========================================================

    status: Mapped[SignalStatus] = mapped_column(
        Enum(
            SignalStatus,
            name="signal_status",
        ),
        nullable=False,
        default=SignalStatus.DRAFT,
        index=True,
    )

    # ========================================================
    # MODEL VERSION SNAPSHOT
    # ========================================================

    model_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # ========================================================
    # TIMESTAMPS
    # ========================================================

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    result_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
 
