from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import SignalModel
from app.models.prediction import Prediction
from app.models.result import SignalResult
from app.models.signal import Signal


# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------


def _percentage(
    numerator: int | float,
    denominator: int | float,
) -> float | None:
    if denominator <= 0:
        return None

    return round(
        (numerator / denominator) * 100,
        2,
    )


def _average(
    values: list[float],
) -> float | None:
    if not values:
        return None

    return round(
        sum(values) / len(values),
        2,
    )


def _build_metrics(
    results: list[SignalResult],
) -> dict:
    """
    Build aggregate performance metrics from signal results.

    All percentages are calculated from the stored prediction
    hit/miss metrics rather than from signal success/failure alone.
    """

    total_completed_signals = len(results)

    successful_signals = sum(
        1
        for result in results
        if result.status.value == "SUCCESS"
    )

    failed_signals = sum(
        1
        for result in results
        if result.status.value == "FAILED"
    )

    # --------------------------------------------------------
    # GENERAL PREDICTION METRICS
    # --------------------------------------------------------

    correct_predictions = sum(
        result.correct_predictions
        for result in results
    )

    incorrect_predictions = sum(
        result.incorrect_predictions
        for result in results
    )

    total_predictions = (
        correct_predictions
        + incorrect_predictions
    )

    prediction_accuracy = _percentage(
        correct_predictions,
        total_predictions,
    )

    # --------------------------------------------------------
    # SAFE PREDICTION METRICS
    # --------------------------------------------------------

    correct_safe_predictions = sum(
        result.correct_safe_predictions
        for result in results
    )

    incorrect_safe_predictions = sum(
        result.incorrect_safe_predictions
        for result in results
    )

    total_safe_predictions = (
        correct_safe_predictions
        + incorrect_safe_predictions
    )

    safe_prediction_precision = _percentage(
        correct_safe_predictions,
        total_safe_predictions,
    )

    # --------------------------------------------------------
    # MINE PREDICTION METRICS
    # --------------------------------------------------------

    correct_mine_predictions = sum(
        result.correct_mine_predictions
        for result in results
    )

    incorrect_mine_predictions = sum(
        result.incorrect_mine_predictions
        for result in results
    )

    total_mine_predictions = (
        correct_mine_predictions
        + incorrect_mine_predictions
    )

    mine_prediction_precision = _percentage(
        correct_mine_predictions,
        total_mine_predictions,
    )

    # --------------------------------------------------------
    # RESULT ACCURACY
    # --------------------------------------------------------

    result_accuracy_values = [
        result.accuracy
        for result in results
        if result.accuracy is not None
    ]

    average_result_accuracy = _average(
        result_accuracy_values
    )

    return {
        "total_completed_signals": total_completed_signals,
        "successful_signals": successful_signals,
        "failed_signals": failed_signals,

        "success_rate": _percentage(
            successful_signals,
            total_completed_signals,
        ),

        "total_predictions": total_predictions,
        "correct_predictions": correct_predictions,
        "incorrect_predictions": incorrect_predictions,

        "prediction_accuracy": prediction_accuracy,

        "correct_safe_predictions": (
            correct_safe_predictions
        ),
        "incorrect_safe_predictions": (
            incorrect_safe_predictions
        ),
        "safe_prediction_precision": (
            safe_prediction_precision
        ),

        "correct_mine_predictions": (
            correct_mine_predictions
        ),
        "incorrect_mine_predictions": (
            incorrect_mine_predictions
        ),
        "mine_prediction_precision": (
            mine_prediction_precision
        ),

        "average_result_accuracy": (
            average_result_accuracy
        ),
    }


# ------------------------------------------------------------
# COMPLETED RESULTS
# ------------------------------------------------------------


def get_completed_results(
    db: Session,
) -> list[SignalResult]:
    """
    Return all recorded signal results.

    Results are ordered chronologically so they can also be
    reused later for historical performance/trend calculations.
    """

    statement = (
        select(SignalResult)
        .order_by(
            SignalResult.recorded_at.asc()
        )
    )

    return list(
        db.scalars(statement).all()
    )


# ------------------------------------------------------------
# OVERVIEW
# ------------------------------------------------------------


def get_performance_overview(
    db: Session,
) -> dict:
    """
    Return system-wide performance metrics.
    """

    results = get_completed_results(db)

    return _build_metrics(results)


# ------------------------------------------------------------
# MODEL PERFORMANCE
# ------------------------------------------------------------


def _get_latest_predictions_by_signal(
    db: Session,
) -> dict[UUID, Prediction]:
    """
    Return the latest prediction for each signal.

    A signal can have more than one prediction record, so joining
    all predictions directly can duplicate SignalResult rows and
    inflate performance metrics.

    This function loads predictions ordered newest-first and keeps
    only the first prediction for each signal.
    """

    statement = (
        select(Prediction)
        .order_by(
            Prediction.signal_id,
            Prediction.created_at.desc(),
        )
    )

    predictions = list(
        db.scalars(statement).all()
    )

    latest_by_signal: dict[
        UUID,
        Prediction,
    ] = {}

    for prediction in predictions:
        if prediction.signal_id not in latest_by_signal:
            latest_by_signal[
                prediction.signal_id
            ] = prediction

    return latest_by_signal


def get_model_performance(
    db: Session,
) -> list[dict]:
    """
    Return performance grouped by model.

    Each completed signal contributes at most once to the model
    statistics by using its latest prediction.
    """

    results_statement = (
        select(
            Signal,
            SignalResult,
        )
        .join(
            SignalResult,
            SignalResult.signal_id == Signal.id,
        )
        .order_by(
            SignalResult.recorded_at.asc()
        )
    )

    result_rows = db.execute(
        results_statement
    ).all()

    latest_predictions = (
        _get_latest_predictions_by_signal(db)
    )

    models = list(
        db.scalars(
            select(SignalModel)
            .order_by(
                SignalModel.created_at.asc()
            )
        ).all()
    )

    grouped: dict[
        UUID,
        list[SignalResult],
    ] = {}

    for signal, result in result_rows:
        prediction = latest_predictions.get(
            signal.id
        )

        if prediction is None:
            continue

        if prediction.model_id is None:
            continue

        grouped.setdefault(
            prediction.model_id,
            [],
        ).append(result)

    response = []

    for model in models:
        results = grouped.get(
            model.id,
            [],
        )

        if not results:
            continue

        metrics = _build_metrics(results)

        response.append(
            {
                "model_id": model.id,
                "model_version": model.version,
                "model_name": model.name,
                **metrics,
            }
        )

    return response


def get_single_model_performance(
    db: Session,
    model_id: UUID,
) -> dict | None:
    """
    Return performance for one model.
    """

    model = db.scalar(
        select(SignalModel).where(
            SignalModel.id == model_id
        )
    )

    if model is None:
        return None

    latest_predictions = (
        _get_latest_predictions_by_signal(db)
    )

    results_statement = (
        select(
            Signal,
            SignalResult,
        )
        .join(
            SignalResult,
            SignalResult.signal_id == Signal.id,
        )
        .order_by(
            SignalResult.recorded_at.asc()
        )
    )

    rows = db.execute(
        results_statement
    ).all()

    results: list[SignalResult] = []

    for signal, result in rows:
        prediction = latest_predictions.get(
            signal.id
        )

        if prediction is None:
            continue

        if prediction.model_id != model_id:
            continue

        results.append(result)

    metrics = _build_metrics(results)

    return {
        "model_id": model.id,
        "model_version": model.version,
        "model_name": model.name,
        **metrics,
    }


# ------------------------------------------------------------
# BOARD / MINE CONFIGURATION PERFORMANCE
# ------------------------------------------------------------


def get_board_performance(
    db: Session,
) -> list[dict]:
    """
    Return performance grouped by board size and mine count.

    Example:

        5x5 + 3 mines
        5x5 + 5 mines
        5x5 + 7 mines
    """

    statement = (
        select(
            Signal,
            SignalResult,
        )
        .join(
            SignalResult,
            SignalResult.signal_id == Signal.id,
        )
        .order_by(
            SignalResult.recorded_at.asc()
        )
    )

    rows = db.execute(
        statement
    ).all()

    grouped: dict[
        tuple[int, int],
        list[SignalResult],
    ] = {}

    for signal, result in rows:
        key = (
            signal.board_size,
            signal.mine_count,
        )

        grouped.setdefault(
            key,
            [],
        ).append(result)

    response = []

    for (
        board_size,
        mine_count,
    ), results in grouped.items():

        metrics = _build_metrics(results)

        response.append(
            {
                "board_size": board_size,
                "mine_count": mine_count,
                **metrics,
            }
        )

    response.sort(
        key=lambda item: (
            item["board_size"],
            item["mine_count"],
        )
    )

    return response


# ------------------------------------------------------------
# RECENT PERFORMANCE
# ------------------------------------------------------------


def get_recent_performance(
    db: Session,
    limit: int = 20,
) -> list[dict]:
    """
    Return the most recent completed signal results.

    The latest prediction for each signal is used so prediction
    history does not create duplicate rows.
    """

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    latest_predictions = (
        _get_latest_predictions_by_signal(db)
    )

    statement = (
        select(
            Signal,
            SignalResult,
        )
        .join(
            SignalResult,
            SignalResult.signal_id == Signal.id,
        )
        .order_by(
            SignalResult.recorded_at.desc()
        )
        .limit(limit)
    )

    rows = db.execute(
        statement
    ).all()

    response = []

    for signal, result in rows:
        prediction = latest_predictions.get(
            signal.id
        )

        response.append(
            {
                "signal_id": signal.id,
                "result_id": result.id,

                "game": signal.game,
                "board_size": signal.board_size,
                "mine_count": signal.mine_count,

                "model_id": (
                    prediction.model_id
                    if prediction
                    else None
                ),

                "model_version": (
                    prediction.model_version
                    if prediction
                    else None
                ),

                "status": result.status.value,

                "correct_predictions": (
                    result.correct_predictions
                ),
                "incorrect_predictions": (
                    result.incorrect_predictions
                ),

                "accuracy": result.accuracy,

                "correct_safe_predictions": (
                    result.correct_safe_predictions
                ),
                "incorrect_safe_predictions": (
                    result.incorrect_safe_predictions
                ),

                "correct_mine_predictions": (
                    result.correct_mine_predictions
                ),
                "incorrect_mine_predictions": (
                    result.incorrect_mine_predictions
                ),

                "confidence": (
                    prediction.confidence
                    if prediction
                    else None
                ),

                "recorded_at": result.recorded_at,
            }
        )

    return response
 
