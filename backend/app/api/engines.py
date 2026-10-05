from datetime import datetime
from statistics import mean
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_administrator,
)
from app.db.session import get_db
from app.models.model import SignalModel
from app.models.result import SignalResult
from app.models.signal import Signal
from app.schemas.engine import (
    PatternBacktestGameResult,
    PatternBacktestRequest,
    PatternBacktestResponse,
    PatternBacktestSkippedGame,
    PatternBacktestSummary,
    PatternEngineDiagnosticsResponse,
    PatternEngineTestRequest,
    PatternEngineTestResponse,
)
from app.services.engines.pattern_diagnostics import (
    pattern_diagnostics_service,
)
from app.services.engines.pattern_engine import (
    PatternEngine,
)


router = APIRouter(
    prefix="/api/engines",
    tags=["Engines"],
)


# ============================================================
# VALIDATE BOARD CONFIGURATION
# ============================================================

def _validate_board_configuration(
    board_size: int,
    mine_count: int,
) -> None:
    if board_size < 1:
        raise HTTPException(
            status_code=400,
            detail="Board size must be at least 1.",
        )

    if board_size > 20:
        raise HTTPException(
            status_code=400,
            detail="Board size cannot exceed 20.",
        )

    if mine_count < 1:
        raise HTTPException(
            status_code=400,
            detail="Mine count must be at least 1.",
        )

    total_cells = board_size * board_size

    if mine_count >= total_cells:
        raise HTTPException(
            status_code=400,
            detail=(
                "Mine count must be less than "
                "the total number of board cells."
            ),
        )


# ============================================================
# PATTERN TEST
# ============================================================

@router.post(
    "/pattern/test",
    response_model=PatternEngineTestResponse,
)
def pattern_engine_test(
    payload: PatternEngineTestRequest,
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    _validate_board_configuration(
        board_size=payload.board_size,
        mine_count=payload.mine_count,
    )

    model = db.get(
        SignalModel,
        payload.model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    signal = Signal(
        board_size=payload.board_size,
        mine_count=payload.mine_count,
        model_id=model.id,
        model_version=model.version,
    )

    engine = PatternEngine()

    prediction = engine.predict(
        db=db,
        signal=signal,
        model=model,
    )

    historical_results = (
        engine._get_historical_results(
            db=db,
            board_size=payload.board_size,
            mine_count=payload.mine_count,
        )
    )

    return PatternEngineTestResponse(
        engine=engine.name,
        engine_version=engine.version,
        model_id=model.id,
        board_size=payload.board_size,
        mine_count=payload.mine_count,
        historical_results_used=len(
            historical_results
        ),
        safe_positions=prediction.safe_positions,
        predicted_mine_positions=(
            prediction.predicted_mine_positions
        ),
        confidence=prediction.confidence,
    )


# ============================================================
# PATTERN DIAGNOSTICS
# ============================================================

@router.post(
    "/pattern/diagnostics",
    response_model=PatternEngineDiagnosticsResponse,
)
def pattern_engine_diagnostics(
    model_id: UUID,
    board_size: int = 5,
    mine_count: int = 3,
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    _validate_board_configuration(
        board_size=board_size,
        mine_count=mine_count,
    )

    model = db.get(
        SignalModel,
        model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    signal = Signal(
        board_size=board_size,
        mine_count=mine_count,
        model_id=model.id,
        model_version=model.version,
    )

    engine = PatternEngine()

    prediction = engine.predict(
        db=db,
        signal=signal,
        model=model,
    )

    diagnostics = (
        pattern_diagnostics_service.diagnose(
            db=db,
            board_size=board_size,
            mine_count=mine_count,
        )
    )

    historical_results = diagnostics[
        "historical_results"
    ]

    return PatternEngineDiagnosticsResponse(
        engine=engine.name,
        engine_version=engine.version,
        model_id=model.id,
        board_size=board_size,
        mine_count=mine_count,
        historical_results_used=len(
            historical_results
        ),
        safe_positions=prediction.safe_positions,
        predicted_mine_positions=(
            prediction.predicted_mine_positions
        ),
        confidence=prediction.confidence,
        position_diagnostics=diagnostics[
            "position_diagnostics"
        ],
        repeated_pairs=diagnostics[
            "repeated_pairs"
        ][:20],
        repeated_triplets=diagnostics[
            "repeated_triplets"
        ][:20],
        row_patterns=diagnostics[
            "row_patterns"
        ],
        column_patterns=diagnostics[
            "column_patterns"
        ],
        structural_patterns=diagnostics[
            "structural_patterns"
        ],
    )


# ============================================================
# PATTERN HISTORICAL BACKTEST
# ============================================================

@router.post(
    "/pattern/backtest",
    response_model=PatternBacktestResponse,
)
def pattern_engine_backtest(
    payload: PatternBacktestRequest,
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Run an expanding-window historical backtest.

    Example with 10 historical games:

        Game 1 -> no prior history -> skipped
        Game 2 -> uses Game 1
        Game 3 -> uses Games 1-2
        Game 4 -> uses Games 1-3
        ...
        Game 10 -> uses Games 1-9

    The target game's result is NEVER included in the history
    used to generate its own prediction.
    """

    _validate_board_configuration(
        board_size=payload.board_size,
        mine_count=payload.mine_count,
    )

    model = db.get(
        SignalModel,
        payload.model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    engine = PatternEngine()

    # --------------------------------------------------------
    # LOAD HISTORICAL RESULTS
    # --------------------------------------------------------

    historical_results = (
        db.query(SignalResult)
        .join(
            Signal,
            Signal.id == SignalResult.signal_id,
        )
        .filter(
            Signal.board_size
            == payload.board_size,
            Signal.mine_count
            == payload.mine_count,
        )
        .order_by(
            SignalResult.recorded_at.asc(),
        )
        .limit(payload.limit)
        .all()
    )

    total_completed_results = len(
        historical_results
    )

    games = []
    skipped_games = []

    # --------------------------------------------------------
    # AGGREGATE METRICS
    # --------------------------------------------------------

    total_safe_predictions = 0
    total_safe_hits = 0

    total_safe_actual = 0

    total_mine_predictions = 0
    total_mine_hits = 0

    total_mine_actual = 0

    total_combined_predictions = 0
    total_combined_hits = 0

    confidences = []

    games_with_safe_hit = 0
    games_with_all_safe_correct = 0
    games_with_all_mine_correct = 0

    # --------------------------------------------------------
    # EXPANDING WINDOW
    # --------------------------------------------------------

    for index, target_result in enumerate(
        historical_results
    ):
        sequence = index + 1

        target_signal = db.get(
            Signal,
            target_result.signal_id,
        )

        if target_signal is None:
            skipped_games.append(
                PatternBacktestSkippedGame(
                    sequence=sequence,
                    signal_id=target_result.signal_id,
                    result_id=target_result.id,
                    recorded_at=target_result.recorded_at,
                    reason="SIGNAL_NOT_FOUND",
                )
            )

            continue

        # First game has no prior history.
        if index == 0:
            skipped_games.append(
                PatternBacktestSkippedGame(
                    sequence=sequence,
                    signal_id=target_signal.id,
                    result_id=target_result.id,
                    recorded_at=target_result.recorded_at,
                    reason="NO_PRIOR_HISTORY",
                )
            )

            continue

        # ----------------------------------------------------
        # CRITICAL:
        # Only results BEFORE the target game are supplied.
        # ----------------------------------------------------

        prior_results = historical_results[
            :index
        ]

        backtest_signal = Signal(
            board_size=target_signal.board_size,
            mine_count=target_signal.mine_count,
            model_id=model.id,
            model_version=model.version,
        )

        prediction = engine.predict(
            db=db,
            signal=backtest_signal,
            model=model,
            historical_results=prior_results,
        )

        predicted_safe = set(
            int(position)
            for position in prediction.safe_positions
        )

        predicted_mines = set(
            int(position)
            for position in (
                prediction.predicted_mine_positions
            )
        )

        actual_safe = set(
            int(position)
            for position in (
                target_result.actual_safe_positions
                or []
            )
        )

        actual_mines = set(
            int(position)
            for position in (
                target_result.actual_mine_positions
                or []
            )
        )

        # ----------------------------------------------------
        # SAFE METRICS
        # ----------------------------------------------------

        safe_hits = len(
            predicted_safe & actual_safe
        )

        safe_misses = (
            len(predicted_safe)
            - safe_hits
        )

        safe_precision = (
            (
                safe_hits
                / len(predicted_safe)
            )
            * 100.0
            if predicted_safe
            else 0.0
        )

        safe_recall = (
            (
                safe_hits
                / len(actual_safe)
            )
            * 100.0
            if actual_safe
            else 0.0
        )

        # ----------------------------------------------------
        # MINE METRICS
        # ----------------------------------------------------

        mine_hits = len(
            predicted_mines & actual_mines
        )

        mine_misses = (
            len(predicted_mines)
            - mine_hits
        )

        mine_precision = (
            (
                mine_hits
                / len(predicted_mines)
            )
            * 100.0
            if predicted_mines
            else 0.0
        )

        mine_recall = (
            (
                mine_hits
                / len(actual_mines)
            )
            * 100.0
            if actual_mines
            else 0.0
        )

        # ----------------------------------------------------
        # COMBINED METRICS
        # ----------------------------------------------------

        overlap_count = len(
            predicted_safe
            & predicted_mines
        )

        combined_hits = (
            safe_hits
            + mine_hits
        )

        combined_predictions = (
            len(predicted_safe)
            + len(predicted_mines)
        )

        combined_precision = (
            (
                combined_hits
                / combined_predictions
            )
            * 100.0
            if combined_predictions
            else 0.0
        )

        # ----------------------------------------------------
        # AGGREGATE
        # ----------------------------------------------------

        total_safe_predictions += len(
            predicted_safe
        )

        total_safe_hits += safe_hits

        total_safe_actual += len(
            actual_safe
        )

        total_mine_predictions += len(
            predicted_mines
        )

        total_mine_hits += mine_hits

        total_mine_actual += len(
            actual_mines
        )

        total_combined_predictions += (
            combined_predictions
        )

        total_combined_hits += (
            combined_hits
        )

        if prediction.confidence is not None:
            confidences.append(
                float(prediction.confidence)
            )

        if safe_hits > 0:
            games_with_safe_hit += 1

        if (
            predicted_safe
            and safe_hits == len(predicted_safe)
        ):
            games_with_all_safe_correct += 1

        if (
            predicted_mines
            and mine_hits == len(predicted_mines)
        ):
            games_with_all_mine_correct += 1

        signal_number = getattr(
            target_signal,
            "signal_number",
            None,
        )

        games.append(
            PatternBacktestGameResult(
                sequence=sequence,
                signal_id=target_signal.id,
                signal_number=signal_number,
                result_id=target_result.id,
                recorded_at=target_result.recorded_at,
                historical_results_used=len(
                    prior_results
                ),
                predicted_safe_positions=sorted(
                    predicted_safe
                ),
                predicted_mine_positions=sorted(
                    predicted_mines
                ),
                actual_safe_positions=sorted(
                    actual_safe
                ),
                actual_mine_positions=sorted(
                    actual_mines
                ),
                safe_hits=safe_hits,
                safe_misses=safe_misses,
                safe_precision_percent=round(
                    safe_precision,
                    2,
                ),
                safe_recall_percent=round(
                    safe_recall,
                    2,
                ),
                mine_hits=mine_hits,
                mine_misses=mine_misses,
                mine_precision_percent=round(
                    mine_precision,
                    2,
                ),
                mine_recall_percent=round(
                    mine_recall,
                    2,
                ),
                combined_hits=combined_hits,
                combined_predictions=(
                    combined_predictions
                ),
                combined_precision_percent=round(
                    combined_precision,
                    2,
                ),
                overlap_count=overlap_count,
                confidence=prediction.confidence,
            )
        )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    evaluated_games = len(games)

    safe_precision = (
        (
            total_safe_hits
            / total_safe_predictions
        )
        * 100.0
        if total_safe_predictions
        else None
    )

    safe_recall = (
        (
            total_safe_hits
            / total_safe_actual
        )
        * 100.0
        if total_safe_actual
        else None
    )

    mine_precision = (
        (
            total_mine_hits
            / total_mine_predictions
        )
        * 100.0
        if total_mine_predictions
        else None
    )

    mine_recall = (
        (
            total_mine_hits
            / total_mine_actual
        )
        * 100.0
        if total_mine_actual
        else None
    )

    combined_precision = (
        (
            total_combined_hits
            / total_combined_predictions
        )
        * 100.0
        if total_combined_predictions
        else None
    )

    average_confidence = (
        mean(confidences)
        if confidences
        else None
    )

    summary = PatternBacktestSummary(
        total_completed_results=(
            total_completed_results
        ),
        evaluated_games=evaluated_games,
        skipped_games=len(skipped_games),

        safe_predictions=(
            total_safe_predictions
        ),
        safe_hits=total_safe_hits,
        safe_precision_percent=(
            round(safe_precision, 2)
            if safe_precision is not None
            else None
        ),
        safe_recall_percent=(
            round(safe_recall, 2)
            if safe_recall is not None
            else None
        ),

        mine_predictions=(
            total_mine_predictions
        ),
        mine_hits=total_mine_hits,
        mine_precision_percent=(
            round(mine_precision, 2)
            if mine_precision is not None
            else None
        ),
        mine_recall_percent=(
            round(mine_recall, 2)
            if mine_recall is not None
            else None
        ),

        combined_predictions=(
            total_combined_predictions
        ),
        combined_hits=total_combined_hits,
        combined_precision_percent=(
            round(combined_precision, 2)
            if combined_precision is not None
            else None
        ),

        average_confidence=(
            round(average_confidence, 2)
            if average_confidence is not None
            else None
        ),

        games_with_safe_hit=(
            games_with_safe_hit
        ),

        games_with_all_safe_predictions_correct=(
            games_with_all_safe_correct
        ),

        games_with_all_mine_predictions_correct=(
            games_with_all_mine_correct
        ),
    )

    return PatternBacktestResponse(
        engine=engine.name,
        engine_version=engine.version,
        model_id=model.id,
        model_version=model.version,
        board_size=payload.board_size,
        mine_count=payload.mine_count,
        summary=summary,
        games=games,
        skipped_games=skipped_games,
    )