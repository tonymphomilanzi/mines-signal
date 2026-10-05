import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_administrator,
)

from app.db.session import get_db

from app.models.administrator import (
    Administrator,
)

from app.models.result import (
    SignalResult,
)

from app.schemas.signal import (
    AnalyzeSignalResponse,
    ConfirmSignalResponse,
    CreateSignalRequest,
    CreateSignalResultRequest,
    CreateSignalResultResponse,
    PredictionResponse,
    SignalDetailResponse,
    SignalListResponse,
    SignalResponse,
    SignalResultResponse,
)

from app.services.analysis_service import (
    analyze_signal,
)

from app.services.ml_prediction_service import (
    get_ml_prediction,
)

from app.services.prediction_service import (
    get_predictions,
)

from app.services.result_service import (
    create_signal_result,
)

from app.services.signal_service import (
    confirm_signal,
    create_signal,
    get_signal_by_id,
    get_signals,
    mark_result_pending,
    publish_signal,
)

from app.services.telegram_service import (
    get_or_create_configuration,
    publish_signal_to_telegram,
)


router = APIRouter(
    prefix="/api/signals",
    tags=["Signals"],
)


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    response_model=SignalResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_signal_endpoint(
    payload: CreateSignalRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    total_positions = (
        payload.board_size
        * payload.board_size
    )

    if payload.mine_count >= total_positions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mine count must be smaller "
                "than the total board positions."
            ),
        )

    try:
        signal = create_signal(
            db=db,
            game=payload.game,
            board_size=payload.board_size,
            mine_count=payload.mine_count,
            attempts=payload.attempts,
            model_id=payload.model_id,
            prediction_engine=(
                payload.prediction_engine
            ),
        )

        return signal

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ============================================================
# LIST
# ============================================================

@router.get(
    "",
    response_model=SignalListResponse,
)
def list_signals(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signals, total = get_signals(db)

    return SignalListResponse(
        items=signals,
        total=total,
    )


# ============================================================
# DETAIL
# ============================================================

@router.get(
    "/{signal_id}",
    response_model=SignalDetailResponse,
)
def get_signal(
    signal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signal = get_signal_by_id(
        db,
        signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Signal not found.",
        )

    # --------------------------------------------------------
    # PRODUCTION PREDICTIONS
    # --------------------------------------------------------

    predictions = get_predictions(
        db,
        signal.id,
    )

    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    ml_prediction = get_ml_prediction(
        db,
        signal.id,
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    result = db.scalar(
        select(SignalResult).where(
            SignalResult.signal_id
            == signal.id
        )
    )

    return SignalDetailResponse(
        id=signal.id,
        signal_number=signal.signal_number,
        game=signal.game,
        board_size=signal.board_size,
        mine_count=signal.mine_count,
        model_id=signal.model_id,
        prediction_engine=(
            signal.prediction_engine
        ),
        confidence=signal.confidence,
        attempts=signal.attempts,
        recommended_positions=(
            signal.recommended_positions
        ),
        status=signal.status,
        model_version=(
            signal.model_version
        ),
        generated_at=(
            signal.generated_at
        ),
        published_at=(
            signal.published_at
        ),
        confirmed_at=(
            signal.confirmed_at
        ),
        result_status=(
            signal.result_status
        ),
        predictions=predictions,
        ml_prediction=ml_prediction,
        result=result,
    )


# ============================================================
# ANALYZE
# ============================================================

@router.post(
    "/{signal_id}/analyze",
    response_model=AnalyzeSignalResponse,
)
def analyze_signal_endpoint(
    signal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signal = get_signal_by_id(
        db,
        signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Signal not found.",
        )

    try:
        # ----------------------------------------------------
        # ANALYZE SIGNAL
        # ----------------------------------------------------
        #
        # The selected prediction_engine determines
        # which engine becomes the production engine.
        #
        # PATTERN:
        #   Pattern Engine 2.0.0
        #
        # ML:
        #   Random Forest ML Engine 1.0.0
        #
        # The selected engine's result becomes:
        #
        #   signal.recommended_positions
        #
        # and the normal Prediction record.
        # ----------------------------------------------------

        signal, prediction, ml_prediction = (
            analyze_signal(
                db,
                signal,
            )
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return AnalyzeSignalResponse(
        message=(
            "Signal analyzed successfully."
        ),
        signal=signal,
        prediction=prediction,
        ml_prediction=ml_prediction,
    )


# ============================================================
# CONFIRM
# ============================================================

@router.post(
    "/{signal_id}/confirm",
    response_model=ConfirmSignalResponse,
)
def confirm_signal_endpoint(
    signal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signal = get_signal_by_id(
        db,
        signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Signal not found.",
        )

    try:
        signal = confirm_signal(
            db,
            signal,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return ConfirmSignalResponse(
        message=(
            "Signal confirmed successfully."
        ),
        signal=signal,
    )


# ============================================================
# PUBLISH
# ============================================================

@router.post(
    "/{signal_id}/publish",
    response_model=SignalResponse,
)
def publish_signal_endpoint(
    signal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signal = get_signal_by_id(
        db,
        signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Signal not found.",
        )

    # --------------------------------------------------------
    # PUBLISH SIGNAL INTERNALLY
    # --------------------------------------------------------

    try:
        signal = publish_signal(
            db,
            signal,
        )

        signal = mark_result_pending(
            db,
            signal,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    # --------------------------------------------------------
    # TELEGRAM AUTOMATIC PUBLISHING
    # --------------------------------------------------------
    #
    # Telegram publishing is deliberately handled AFTER the
    # signal has successfully become PUBLISHED / RESULT_PENDING.
    #
    # If Telegram fails, the signal remains published and the
    # TelegramMessage record becomes FAILED and can be retried.
    #
    # --------------------------------------------------------

    try:
        configuration = get_or_create_configuration(
            db
        )

        should_publish_to_telegram = (
            configuration.automatic_publishing
            and configuration.publish_confirmed_signals
        )

        if should_publish_to_telegram:
            publish_signal_to_telegram(
                db,
                signal,
            )

    except Exception:
        # ----------------------------------------------------
        # IMPORTANT
        # ----------------------------------------------------
        # Do NOT undo signal publication when Telegram fails.
        #
        # publish_signal_to_telegram() already records:
        #
        #   status = FAILED
        #   sync_status = FAILED
        #   error_message = ...
        #
        # The administrator can later use the Telegram retry
        # endpoint.
        # ----------------------------------------------------

        pass

    return signal


# ============================================================
# PREDICTIONS
# ============================================================

@router.get(
    "/{signal_id}/predictions",
    response_model=list[
        PredictionResponse
    ],
)
def list_predictions(
    signal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signal = get_signal_by_id(
        db,
        signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Signal not found.",
        )

    return get_predictions(
        db,
        signal.id,
    )


# ============================================================
# CREATE RESULT
# ============================================================

@router.post(
    "/{signal_id}/result",
    response_model=CreateSignalResultResponse,
)
def create_result(
    signal_id: uuid.UUID,
    payload: CreateSignalResultRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    signal = get_signal_by_id(
        db,
        signal_id,
    )

    if signal is None:
        raise HTTPException(
            status_code=404,
            detail="Signal not found.",
        )

    try:
        result = create_signal_result(
            db=db,
            signal=signal,
            actual_mine_positions=(
                payload.actual_mine_positions
            ),
            actual_safe_positions=(
                payload.actual_safe_positions
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return CreateSignalResultResponse(
        message=(
            "Signal result recorded successfully."
        ),
        signal=signal,
        result=result,
    )


# ============================================================
# GET RESULT
# ============================================================

@router.get(
    "/{signal_id}/result",
    response_model=SignalResultResponse,
)
def get_result(
    signal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    result = db.scalar(
        select(SignalResult).where(
            SignalResult.signal_id
            == signal_id
        )
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Signal result not found.",
        )

    return result
 
