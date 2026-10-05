from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml_prediction import MLPrediction
from app.services.ml.predictor import PredictionResult


# ============================================================
# CREATE ML PREDICTION
# ============================================================

def create_ml_prediction(
    db: Session,
    *,
    signal_id: uuid.UUID,
    prediction: PredictionResult,
) -> MLPrediction:
    """
    Persist an ML prediction for a signal.

    This is observational ML output.

    It does NOT modify:
        - Signal
        - Pattern Engine prediction
        - Signal lifecycle
        - production recommendation
    """

    position_predictions = [
        {
            "position": item.position,
            "row": item.row,
            "column": item.column,
            "safe_probability": item.safe_probability,
            "mine_probability": item.mine_probability,
            "rank": item.rank,
        }
        for item in prediction.predictions
    ]

    ml_prediction = MLPrediction(
        id=uuid.uuid4(),

        signal_id=signal_id,

        model_name=prediction.model_name,

        model_version=prediction.model_version,

        feature_version=prediction.feature_version,

        board_size=prediction.board_size,

        mine_count=prediction.mine_count,

        top_positions=list(
            prediction.top_positions
        ),

        position_predictions=(
            position_predictions
        ),
    )

    db.add(ml_prediction)

    return ml_prediction


# ============================================================
# GET ML PREDICTION
# ============================================================

def get_ml_prediction(
    db: Session,
    signal_id: uuid.UUID,
) -> MLPrediction | None:

    statement = (
        select(MLPrediction)
        .where(
            MLPrediction.signal_id
            == signal_id
        )
        .order_by(
            MLPrediction.created_at.desc()
        )
        .limit(1)
    )

    return db.scalar(statement)


# ============================================================
# GET ALL ML PREDICTIONS
# ============================================================

def get_ml_predictions(
    db: Session,
    signal_id: uuid.UUID,
) -> list[MLPrediction]:

    statement = (
        select(MLPrediction)
        .where(
            MLPrediction.signal_id
            == signal_id
        )
        .order_by(
            MLPrediction.created_at.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )
 
