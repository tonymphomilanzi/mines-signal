from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ml_prediction import (
    MLPrediction,
)

from app.models.result import (
    SignalResult,
)

from app.models.signal import (
    PredictionEngine,
    Signal,
    SignalStatus,
)

from app.services.engines.pattern_engine import (
    PatternEngine,
)

from app.services.ml.predictor import (
    MLPredictor,
)

from app.services.ml_prediction_service import (
    create_ml_prediction,
)

from app.services.prediction_service import (
    create_prediction,
    get_model_for_signal,
)


# ------------------------------------------------------------
# ML HISTORICAL RECORDS
# ------------------------------------------------------------

def _build_ml_historical_records(
    historical_results: list[
        tuple[SignalResult, Signal]
    ],
) -> list[dict[str, Any]]:
    """
    Convert historical SignalResult + Signal pairs into
    the position-level records expected by MLPredictor.

    The current signal is never included here.
    Only completed historical games are used.
    """

    records: list[dict[str, Any]] = []

    for result, historical_signal in historical_results:
        total_cells = (
            historical_signal.board_size
            * historical_signal.board_size
        )

        actual_mines = {
            int(position)
            for position in (
                result.actual_mine_positions
                or []
            )
        }

        actual_safe = {
            int(position)
            for position in (
                result.actual_safe_positions
                or []
            )
        }

        # ----------------------------------------------------
        # VALIDATE COMPLETE BOARD
        # ----------------------------------------------------

        if len(
            actual_mines
            | actual_safe
        ) != total_cells:
            continue

        # ----------------------------------------------------
        # VALIDATE NO OVERLAP
        # ----------------------------------------------------

        if actual_mines & actual_safe:
            continue

        # ----------------------------------------------------
        # VALIDATE MINE COUNT
        # ----------------------------------------------------

        if len(actual_mines) != (
            historical_signal.mine_count
        ):
            continue

        # ----------------------------------------------------
        # BUILD POSITION RECORDS
        # ----------------------------------------------------

        for position in range(
            1,
            total_cells + 1,
        ):
            row, column = divmod(
                position - 1,
                historical_signal.board_size,
            )

            if position in actual_safe:
                label = 1

            elif position in actual_mines:
                label = 0

            else:
                continue

            records.append(
                {
                    "signal_id": str(
                        historical_signal.id
                    ),
                    "result_id": str(
                        result.id
                    ),
                    "board_size": (
                        historical_signal.board_size
                    ),
                    "mine_count": (
                        historical_signal.mine_count
                    ),
                    "total_cells": total_cells,
                    "position": position,
                    "row": row,
                    "column": column,
                    "label": label,
                    "generated_at": (
                        historical_signal.generated_at
                    ),
                    "recorded_at": (
                        result.recorded_at
                    ),
                }
            )

    return records


# ------------------------------------------------------------
# ML PRODUCTION OUTPUT
# ------------------------------------------------------------

def _build_ml_production_output(
    prediction,
    mine_count: int,
) -> tuple[
    list[int],
    list[int],
    float,
]:
    """
    Convert an ML PredictionResult into the format used
    by the production Signal + Prediction models.

    Returns:

        safe_positions
        predicted_mine_positions
        confidence

    ML safe positions come from the model's top-ranked
    safe positions.

    Mine positions are selected from the remaining cells
    with the highest mine probability.

    This prevents the same position from being both a
    predicted safe position and a predicted mine.
    """

    safe_positions = list(
        prediction.top_positions
    )

    # --------------------------------------------------------
    # SELECT MINE POSITIONS
    # --------------------------------------------------------

    ranked_mines = sorted(
        (
            item
            for item in prediction.predictions
            if item.position not in safe_positions
        ),
        key=lambda item: item.mine_probability,
        reverse=True,
    )

    predicted_mine_positions = [
        item.position
        for item in ranked_mines[:mine_count]
    ]

    # --------------------------------------------------------
    # CALCULATE CONFIDENCE
    # --------------------------------------------------------

    selected_safe_predictions = [
        item
        for item in prediction.predictions
        if item.position in safe_positions
    ]

    if selected_safe_predictions:
        confidence = (
            sum(
                item.safe_probability
                for item in selected_safe_predictions
            )
            / len(selected_safe_predictions)
        ) * 100.0
    else:
        confidence = 0.0

    return (
        safe_positions,
        predicted_mine_positions,
        round(confidence, 2),
    )


# ------------------------------------------------------------
# ANALYZE SIGNAL
# ------------------------------------------------------------

def analyze_signal(
    db: Session,
    signal: Signal,
):
    """
    Analyze a DRAFT signal using the engine selected
    when the signal was created.

    Production engine behavior:

        PATTERN
            -> PatternEngine

        ML
            -> MLPredictor / Random Forest

    The selected engine controls:

        - recommended_positions
        - predicted mine positions
        - confidence
        - normal Prediction record

    Pattern Engine itself is not modified.

    ML predictions are persisted in ml_predictions.

    When PATTERN is selected, ML may additionally be
    generated and persisted for comparison.

    When ML is selected, ML failure is fatal for analysis.
    We never silently fall back to Pattern Engine.
    """

    # --------------------------------------------------------
    # VALIDATE SIGNAL STATUS
    # --------------------------------------------------------

    if signal.status != SignalStatus.DRAFT:
        raise ValueError(
            "Only DRAFT signals can be analyzed."
        )

    # --------------------------------------------------------
    # LOAD SELECTED SIGNAL MODEL
    # --------------------------------------------------------

    model = get_model_for_signal(
        db=db,
        signal=signal,
    )

    if model.board_size != signal.board_size:
        raise ValueError(
            "The selected model does not support "
            "this signal's board size."
        )

    if signal.attempts > model.maximum_attempts:
        raise ValueError(
            "Signal attempts exceed the selected "
            "model's maximum attempts."
        )

    # --------------------------------------------------------
    # LOAD HISTORICAL RESULTS
    # --------------------------------------------------------
    #
    # We load SignalResult + Signal together because:
    #
    # Pattern Engine needs SignalResult objects.
    #
    # ML needs both SignalResult and historical Signal
    # metadata such as board size and mine count.
    #
    # The current DRAFT signal is not included because it
    # does not yet have a result.
    # --------------------------------------------------------

    historical_results_statement = (
        select(
            SignalResult,
            Signal,
        )
        .join(
            Signal,
            Signal.id == SignalResult.signal_id,
        )
        .where(
            Signal.board_size
            == signal.board_size,

            Signal.mine_count
            == signal.mine_count,
        )
        .order_by(
            SignalResult.recorded_at.asc(),
        )
    )

    historical_results = list(
        db.execute(
            historical_results_statement
        ).all()
    )

    # --------------------------------------------------------
    # PRODUCTION OUTPUT
    # --------------------------------------------------------

    production_safe_positions: list[int] = []
    production_mine_positions: list[int] = []
    production_confidence: float = 0.0

    # Keep the Pattern model version as the selected
    # SignalModel snapshot for backwards compatibility.
    production_model_version = model.version

    # ML persistence record.
    ml_prediction_record: (
        MLPrediction | None
    ) = None

    # --------------------------------------------------------
    # PATTERN ENGINE
    # --------------------------------------------------------

    if signal.prediction_engine == PredictionEngine.PATTERN:
        pattern_engine = PatternEngine()

        pattern_prediction = pattern_engine.predict(
            db=db,
            signal=signal,
            model=model,
            historical_results=[
                result
                for result, _signal
                in historical_results
            ],
        )

        production_safe_positions = list(
            pattern_prediction.safe_positions
        )

        production_mine_positions = list(
            pattern_prediction.predicted_mine_positions
        )

        production_confidence = (
            pattern_prediction.confidence
        )

        # ----------------------------------------------------
        # OPTIONAL ML COMPARISON
        # ----------------------------------------------------
        #
        # Pattern remains production.
        #
        # ML is allowed to fail here without affecting the
        # Pattern prediction.
        #
        # This gives us ongoing ML comparison data while
        # Pattern Engine remains the production engine.
        # ----------------------------------------------------

        try:
            ml_historical_records = (
                _build_ml_historical_records(
                    historical_results
                )
            )

            ml_predictor = MLPredictor()

            ml_prediction = (
                ml_predictor.predict_board(
                    board_size=signal.board_size,
                    mine_count=signal.mine_count,
                    historical_records=(
                        ml_historical_records
                    ),
                    top_n=5,
                )
            )

            ml_prediction_record = (
                create_ml_prediction(
                    db=db,
                    signal_id=signal.id,
                    prediction=ml_prediction,
                )
            )

        except Exception as exc:
            print(
                "ML comparison prediction failed:",
                str(exc),
                flush=True,
            )

            print(
                "Pattern Engine production prediction "
                "will continue.",
                flush=True,
            )

    # --------------------------------------------------------
    # ML ENGINE
    # --------------------------------------------------------

    elif signal.prediction_engine == PredictionEngine.ML:
        try:
            ml_historical_records = (
                _build_ml_historical_records(
                    historical_results
                )
            )

            ml_predictor = MLPredictor()

            ml_prediction = (
                ml_predictor.predict_board(
                    board_size=signal.board_size,
                    mine_count=signal.mine_count,
                    historical_records=(
                        ml_historical_records
                    ),
                    top_n=5,
                )
            )

            # ------------------------------------------------
            # PERSIST ML PREDICTION
            # ------------------------------------------------

            ml_prediction_record = (
                create_ml_prediction(
                    db=db,
                    signal_id=signal.id,
                    prediction=ml_prediction,
                )
            )

            # ------------------------------------------------
            # CONVERT ML OUTPUT INTO PRODUCTION OUTPUT
            # ------------------------------------------------

            (
                production_safe_positions,
                production_mine_positions,
                production_confidence,
            ) = _build_ml_production_output(
                prediction=ml_prediction,
                mine_count=signal.mine_count,
            )

            # ------------------------------------------------
            # VALIDATE ML OUTPUT
            # ------------------------------------------------

            if not production_safe_positions:
                raise ValueError(
                    "ML engine returned no safe positions."
                )

            if len(
                production_mine_positions
            ) != signal.mine_count:
                raise ValueError(
                    "ML engine did not return the required "
                    "number of predicted mine positions."
                )

            # ------------------------------------------------
            # IMPORTANT
            # ------------------------------------------------
            #
            # We intentionally do NOT fall back to Pattern
            # Engine here.
            #
            # If the admin selected ML, this signal must be
            # produced by ML.
            # ------------------------------------------------

        except Exception as exc:
            raise ValueError(
                f"ML prediction failed: {exc}"
            ) from exc

    # --------------------------------------------------------
    # UNKNOWN ENGINE
    # --------------------------------------------------------

    else:
        raise ValueError(
            f"Unsupported prediction engine: "
            f"{signal.prediction_engine}"
        )

    # --------------------------------------------------------
    # APPLY PRODUCTION PREDICTION TO SIGNAL
    # --------------------------------------------------------

    signal.recommended_positions = list(
        production_safe_positions
    )

    signal.confidence = (
        production_confidence
    )

    signal.model_version = (
        production_model_version
    )

    signal.status = SignalStatus.ANALYZED

    # --------------------------------------------------------
    # CREATE NORMAL PRODUCTION PREDICTION
    # --------------------------------------------------------
    #
    # This is the prediction used by the existing lifecycle.
    #
    # Its contents now come from whichever engine the admin
    # selected when creating the signal.
    # --------------------------------------------------------

    prediction = create_prediction(
        db=db,
        signal=signal,
        model=model,
        safe_positions=list(
            production_safe_positions
        ),
        predicted_mine_positions=list(
            production_mine_positions
        ),
        confidence=(
            production_confidence
        ),
    )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    db.add(signal)

    db.commit()

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    db.refresh(signal)

    db.refresh(prediction)

    if ml_prediction_record is not None:
        db.refresh(
            ml_prediction_record
        )

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return (
        signal,
        prediction,
        ml_prediction_record,
    )
 
