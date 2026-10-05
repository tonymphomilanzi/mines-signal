import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.model import (
    ModelStatus,
    SignalModel,
)

from app.models.signal import (
    PredictionEngine,
    Signal,
    SignalStatus,
)


# ============================================================
# SIGNAL NUMBER
# ============================================================

def generate_signal_number(
    db: Session,
) -> str:
    """
    Generate a human-readable unique signal number.

    Example:
        SIG-20260930-0001
    """

    date_part = datetime.now(
        timezone.utc
    ).strftime("%Y%m%d")

    prefix = f"SIG-{date_part}-"

    statement = (
        select(func.count(Signal.id))
        .where(
            Signal.signal_number.like(
                f"{prefix}%"
            )
        )
    )

    count = db.scalar(statement) or 0

    return f"{prefix}{count + 1:04d}"


# ============================================================
# GET SELECTED MODEL
# ============================================================

def get_signal_model(
    db: Session,
    model_id: uuid.UUID,
    board_size: int,
    attempts: int,
) -> SignalModel:
    """
    Validate and return the model selected for a signal.

    The model record is still used for:
    - board-size validation
    - maximum-attempt validation
    - model version snapshot
    """

    statement = (
        select(SignalModel)
        .where(
            SignalModel.id == model_id
        )
    )

    model = db.scalar(statement)

    if model is None:
        raise ValueError(
            "Selected model was not found."
        )

    if model.status not in (
        ModelStatus.ACTIVE,
        ModelStatus.READY,
    ):
        raise ValueError(
            "Selected model is not available."
        )

    if model.board_size != board_size:
        raise ValueError(
            "Selected model does not support "
            f"a {board_size}x{board_size} board."
        )

    if attempts > model.maximum_attempts:
        raise ValueError(
            "Attempts exceed the selected "
            "model's maximum attempts."
        )

    return model


# ============================================================
# CREATE
# ============================================================

def create_signal(
    db: Session,
    *,
    game: str,
    board_size: int,
    mine_count: int,
    attempts: int,
    model_id: uuid.UUID,
    prediction_engine: PredictionEngine = (
        PredictionEngine.PATTERN
    ),
) -> Signal:
    """
    Create a new DRAFT signal.

    prediction_engine determines which prediction engine
    will become the production engine during analysis.

    PATTERN:
        Pattern Engine 2.0.0

    ML:
        Random Forest ML Engine 1.0.0
    """

    # --------------------------------------------------------
    # VALIDATE MODEL
    # --------------------------------------------------------

    model = get_signal_model(
        db=db,
        model_id=model_id,
        board_size=board_size,
        attempts=attempts,
    )

    # --------------------------------------------------------
    # GENERATE SIGNAL NUMBER
    # --------------------------------------------------------

    signal_number = generate_signal_number(
        db
    )

    # --------------------------------------------------------
    # CREATE SIGNAL
    # --------------------------------------------------------

    signal = Signal(
        id=uuid.uuid4(),

        signal_number=signal_number,

        game=game,

        board_size=board_size,

        mine_count=mine_count,

        model_id=model.id,

        prediction_engine=prediction_engine,

        model_version=model.version,

        attempts=attempts,

        recommended_positions=[],

        status=SignalStatus.DRAFT,
    )

    db.add(signal)

    db.commit()

    db.refresh(signal)

    return signal


# ============================================================
# GET ALL
# ============================================================

def get_signals(
    db: Session,
) -> tuple[list[Signal], int]:

    statement = (
        select(Signal)
        .order_by(
            Signal.generated_at.desc()
        )
    )

    signals = list(
        db.scalars(statement).all()
    )

    return signals, len(signals)


# ============================================================
# GET BY ID
# ============================================================

def get_signal_by_id(
    db: Session,
    signal_id: uuid.UUID,
) -> Signal | None:

    statement = select(Signal).where(
        Signal.id == signal_id
    )

    return db.scalar(statement)


# ============================================================
# STATUS VALIDATION
# ============================================================

def ensure_signal_status(
    signal: Signal,
    expected_status: SignalStatus,
) -> None:

    if signal.status != expected_status:
        raise ValueError(
            f"Signal must be in "
            f"{expected_status.value} status."
        )


# ============================================================
# CONFIRM
# ============================================================

def confirm_signal(
    db: Session,
    signal: Signal,
) -> Signal:

    ensure_signal_status(
        signal,
        SignalStatus.ANALYZED,
    )

    signal.status = SignalStatus.CONFIRMED

    signal.confirmed_at = datetime.now(
        timezone.utc
    )

    db.commit()

    db.refresh(signal)

    return signal


# ============================================================
# PUBLISH
# ============================================================

def publish_signal(
    db: Session,
    signal: Signal,
) -> Signal:

    ensure_signal_status(
        signal,
        SignalStatus.CONFIRMED,
    )

    signal.status = SignalStatus.PUBLISHED

    signal.published_at = datetime.now(
        timezone.utc
    )

    db.commit()

    db.refresh(signal)

    return signal


# ============================================================
# RESULT PENDING
# ============================================================

def mark_result_pending(
    db: Session,
    signal: Signal,
) -> Signal:

    ensure_signal_status(
        signal,
        SignalStatus.PUBLISHED,
    )

    signal.status = (
        SignalStatus.RESULT_PENDING
    )

    db.commit()

    db.refresh(signal)

    return signal


# ============================================================
# SUCCESS
# ============================================================

def mark_signal_success(
    db: Session,
    signal: Signal,
) -> Signal:

    signal.status = SignalStatus.SUCCESS

    signal.result_status = "SUCCESS"

    db.commit()

    db.refresh(signal)

    return signal


# ============================================================
# FAILED
# ============================================================

def mark_signal_failed(
    db: Session,
    signal: Signal,
) -> Signal:

    signal.status = SignalStatus.FAILED

    signal.result_status = "FAILED"

    db.commit()

    db.refresh(signal)

    return signal
 
