import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_administrator,
)
from app.db.session import get_db
from app.models.result import SignalResult
from app.models.signal import Signal, SignalStatus
from app.schemas.signal import (
    SignalResultDetailResponse,
    SignalResultListItem,
    SignalResultListResponse,
)
from app.services.prediction_service import (
    get_latest_prediction,
)


router = APIRouter(
    prefix="/api/results",
    tags=["Results"],
)


# ============================================================
# LIST RESULTS
# ============================================================

@router.get(
    "",
    response_model=SignalResultListResponse,
)
def list_results(
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Return completed results plus confirmed signals
    that are still waiting for an actual outcome.
    """

    statement = (
        select(
            Signal,
            SignalResult,
        )
        .outerjoin(
            SignalResult,
            SignalResult.signal_id == Signal.id,
        )
        .where(
            Signal.status.in_(
                [
                    SignalStatus.CONFIRMED,
                    SignalStatus.RESULT_PENDING,
                    SignalStatus.SUCCESS,
                    SignalStatus.FAILED,
                ]
            )
        )
        .order_by(
            Signal.generated_at.desc()
        )
    )

    rows = db.execute(statement).all()

    items: list[SignalResultListItem] = []

    for signal, result in rows:
        prediction = get_latest_prediction(
            db,
            signal.id,
        )

        predicted_safe = (
            prediction.safe_positions
            if prediction
            else signal.recommended_positions or []
        )

        confidence = (
            prediction.confidence
            if prediction
            else signal.confidence
        )

        attempts = (
            prediction.attempts
            if prediction
            else signal.attempts
        )

        model_version = (
            prediction.model_version
            if prediction
            else signal.model_version
        )

        if result is None:
            status = "PENDING"

            actual_safe_positions = []
            actual_mine_positions = []

            correct_predictions = 0
            incorrect_predictions = 0
            accuracy = None

            recorded_at = None

        else:
            status = result.status.value

            actual_safe_positions = (
                result.actual_safe_positions or []
            )

            actual_mine_positions = (
                result.actual_mine_positions or []
            )

            correct_predictions = (
                result.correct_predictions
            )

            incorrect_predictions = (
                result.incorrect_predictions
            )

            accuracy = result.accuracy

            recorded_at = result.recorded_at

        items.append(
            SignalResultListItem(
                id=result.id if result else None,
                signal_id=signal.id,
                signal_number=signal.signal_number,
                game=signal.game,
                board_size=signal.board_size,
                mine_count=signal.mine_count,
                confidence=confidence,
                predicted_safe_positions=predicted_safe,
                actual_safe_positions=actual_safe_positions,
                actual_mine_positions=actual_mine_positions,
                correct_predictions=correct_predictions,
                incorrect_predictions=incorrect_predictions,
                accuracy=accuracy,
                status=status,
                attempts=attempts,
                model_version=model_version,
                signal_created_at=signal.generated_at,
                recorded_at=recorded_at,
            )
        )

    return SignalResultListResponse(
        items=items,
        total=len(items),
    )


# ============================================================
# RESULT DETAIL
# ============================================================

@router.get(
    "/{result_id}",
    response_model=SignalResultDetailResponse,
)
def get_result_detail(
    result_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    result = db.get(
        SignalResult,
        result_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Result not found.",
        )

    signal = db.get(
        Signal,
        result.signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Source signal not found.",
        )

    prediction = get_latest_prediction(
        db,
        signal.id,
    )

    predicted_safe = (
        prediction.safe_positions
        if prediction
        else signal.recommended_positions or []
    )

    confidence = (
        prediction.confidence
        if prediction
        else signal.confidence
    )

    attempts = (
        prediction.attempts
        if prediction
        else signal.attempts
    )

    model_version = (
        prediction.model_version
        if prediction
        else signal.model_version
    )

    return SignalResultDetailResponse(
        id=result.id,
        signal_id=signal.id,
        signal_number=signal.signal_number,
        game=signal.game,
        board_size=signal.board_size,
        mine_count=signal.mine_count,
        confidence=confidence,
        predicted_safe_positions=predicted_safe,
        actual_safe_positions=(
            result.actual_safe_positions or []
        ),
        actual_mine_positions=(
            result.actual_mine_positions or []
        ),
        correct_predictions=(
            result.correct_predictions
        ),
        incorrect_predictions=(
            result.incorrect_predictions
        ),
        accuracy=result.accuracy,
        status=result.status.value,
        attempts=attempts,
        model_version=model_version,
        signal_created_at=signal.generated_at,
        recorded_at=result.recorded_at,
    )