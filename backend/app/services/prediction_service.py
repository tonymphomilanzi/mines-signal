import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import (
    ModelStatus,
    SignalModel,
)

from app.models.prediction import (
    Prediction,
)

from app.models.signal import (
    Signal,
)


# ============================================================
# GET ACTIVE MODEL
# ============================================================

def get_active_model(
    db: Session,
    board_size: int,
) -> SignalModel | None:
    """
    Return the currently ACTIVE model for a board size.

    Kept for compatibility with other parts of the system.

    Signal analysis should use get_model_for_signal().
    """

    statement = (
        select(SignalModel)
        .where(
            SignalModel.status
            == ModelStatus.ACTIVE,

            SignalModel.board_size
            == board_size,
        )
        .order_by(
            SignalModel.activated_at.desc()
        )
    )

    return db.scalar(statement)


# ============================================================
# GET MODEL FOR SIGNAL
# ============================================================

def get_model_for_signal(
    db: Session,
    signal: Signal,
) -> SignalModel:
    """
    Return the exact model assigned to the signal.

    This is intentionally different from get_active_model().
    """

    if signal.model_id is None:
        raise ValueError(
            "This signal does not have a model assigned."
        )

    statement = (
        select(SignalModel)
        .where(
            SignalModel.id
            == signal.model_id
        )
    )

    model = db.scalar(statement)

    if model is None:
        raise ValueError(
            "The model assigned to this signal "
            "does not exist."
        )

    if model.status not in (
        ModelStatus.ACTIVE,
        ModelStatus.READY,
    ):
        raise ValueError(
            "The model assigned to this signal "
            "is no longer available."
        )

    return model


# ============================================================
# CREATE PREDICTION
# ============================================================

def create_prediction(
    db: Session,
    *,
    signal: Signal,
    model: SignalModel | None,
    safe_positions: list[int],
    predicted_mine_positions: list[int],
    confidence: float | None,
) -> Prediction:
    """
    Create a Prediction record.

    The transaction is committed by the caller.
    """

    prediction = Prediction(
        id=uuid.uuid4(),

        signal_id=signal.id,

        model_id=(
            model.id
            if model
            else None
        ),

        safe_positions=list(
            safe_positions
        ),

        predicted_mine_positions=list(
            predicted_mine_positions
        ),

        confidence=confidence,

        attempts=signal.attempts,

        model_version=(
            model.version
            if model
            else None
        ),
    )

    db.add(prediction)

    return prediction


# ============================================================
# GET PREDICTIONS
# ============================================================

def get_predictions(
    db: Session,
    signal_id: uuid.UUID,
) -> list[Prediction]:

    statement = (
        select(Prediction)
        .where(
            Prediction.signal_id
            == signal_id
        )
        .order_by(
            Prediction.created_at.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


# ============================================================
# GET LATEST PREDICTION
# ============================================================

def get_latest_prediction(
    db: Session,
    signal_id: uuid.UUID,
) -> Prediction | None:

    statement = (
        select(Prediction)
        .where(
            Prediction.signal_id
            == signal_id
        )
        .order_by(
            Prediction.created_at.desc()
        )
        .limit(1)
    )

    return db.scalar(statement)