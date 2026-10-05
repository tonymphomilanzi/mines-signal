import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# RESULT STATUS
# ============================================================


class ResultStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


# ============================================================
# SIGNAL RESULT
# ============================================================


class SignalResult(Base):
    __tablename__ = "results"

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
        unique=True,
        index=True,
    )

    # --------------------------------------------------------
    # ACTUAL BOARD RESULT
    # --------------------------------------------------------

    actual_mine_positions: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=list,
    )

    actual_safe_positions: Mapped[list[int]] = mapped_column(
        ARRAY(Integer),
        nullable=False,
        default=list,
    )

    # --------------------------------------------------------
    # SAFE PREDICTION METRICS
    # --------------------------------------------------------

    correct_safe_predictions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    incorrect_safe_predictions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # --------------------------------------------------------
    # MINE PREDICTION METRICS
    # --------------------------------------------------------

    correct_mine_predictions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    incorrect_mine_predictions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # --------------------------------------------------------
    # COMBINED PREDICTION METRICS
    # --------------------------------------------------------

    correct_predictions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    incorrect_predictions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    accuracy: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # --------------------------------------------------------
    # RESULT STATUS
    # --------------------------------------------------------

    status: Mapped[ResultStatus] = mapped_column(
        Enum(
            ResultStatus,
            name="result_status",
        ),
        nullable=False,
    )

    # --------------------------------------------------------
    # TIMESTAMP
    # --------------------------------------------------------

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )
 
