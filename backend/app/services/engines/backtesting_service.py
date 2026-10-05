from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import SignalModel
from app.models.result import ResultStatus, SignalResult
from app.models.signal import Signal

from app.services.engines.pattern_engine import PatternEngine


@dataclass
class BacktestGameResult:
    sequence: int
    signal_id: UUID
    result_id: UUID
    recorded_at: datetime

    historical_results_used: int

    predicted_safe_positions: list[int]
    actual_safe_positions: list[int]
    correct_safe_positions: list[int]

    predicted_mine_positions: list[int]
    actual_mine_positions: list[int]
    correct_mine_positions: list[int]

    safe_predictions: int
    safe_hits: int
    safe_accuracy: float

    mine_predictions: int
    mine_hits: int
    mine_accuracy: float

    total_predictions: int
    total_hits: int
    combined_accuracy: float

    engine_confidence: float | None


class PatternBacktestingService:
    """
    Chronological walk-forward backtesting service.

    Each historical result is evaluated using only results that
    occurred before it.

    The target result is NEVER included in the historical dataset
    used to generate its prediction.
    """

    def _get_completed_results(
        self,
        db: Session,
        board_size: int,
        mine_count: int,
    ) -> list[SignalResult]:

        statement = (
            select(SignalResult)
            .join(
                Signal,
                Signal.id == SignalResult.signal_id,
            )
            .where(
                Signal.board_size == board_size,
                Signal.mine_count == mine_count,
                SignalResult.status.in_(
                    [
                        ResultStatus.SUCCESS,
                        ResultStatus.FAILED,
                    ]
                ),
            )
            .order_by(
                SignalResult.recorded_at.asc(),
                SignalResult.id.asc(),
            )
        )

        return list(
            db.scalars(statement).all()
        )

    def _get_signal(
        self,
        db: Session,
        signal_id: UUID,
    ) -> Signal | None:

        return db.get(
            Signal,
            signal_id,
        )

    def run(
        self,
        db: Session,
        model: SignalModel,
        board_size: int,
        mine_count: int,
    ) -> dict:

        results = self._get_completed_results(
            db=db,
            board_size=board_size,
            mine_count=mine_count,
        )

        if not results:
            return {
                "historical_results": 0,
                "evaluated_results": 0,
                "skipped_results": 0,
                "results": [],
            }

        engine = PatternEngine()

        backtest_results: list[
            BacktestGameResult
        ] = []

        skipped_results = 0

        # --------------------------------------------------------
        # WALK FORWARD THROUGH HISTORY
        # --------------------------------------------------------

        for index, target_result in enumerate(
            results
        ):

            # The first result has no previous historical
            # information available.
            if index == 0:
                skipped_results += 1
                continue

            previous_results = results[
                :index
            ]

            target_signal = self._get_signal(
                db=db,
                signal_id=target_result.signal_id,
            )

            if target_signal is None:
                skipped_results += 1
                continue

            # ----------------------------------------------------
            # CREATE IN-MEMORY SIGNAL
            # ----------------------------------------------------

            test_signal = Signal(
                board_size=target_signal.board_size,
                mine_count=target_signal.mine_count,
                model_id=model.id,
                model_version=model.version,
            )

            # ----------------------------------------------------
            # RUN ENGINE USING ONLY PAST RESULTS
            # ----------------------------------------------------

            prediction = engine.predict(
                db=db,
                signal=test_signal,
                model=model,
                historical_results=previous_results,
            )

            predicted_safe = set(
                prediction.safe_positions
            )

            predicted_mines = set(
                prediction.predicted_mine_positions
            )

            actual_safe = set(
                target_result.actual_safe_positions
                or []
            )

            actual_mines = set(
                target_result.actual_mine_positions
                or []
            )

            # ----------------------------------------------------
            # SAFE EVALUATION
            # ----------------------------------------------------

            correct_safe = sorted(
                predicted_safe.intersection(
                    actual_safe
                )
            )

            safe_predictions = len(
                predicted_safe
            )

            safe_hits = len(
                correct_safe
            )

            safe_accuracy = (
                (
                    safe_hits
                    / safe_predictions
                    * 100.0
                )
                if safe_predictions
                else 0.0
            )

            # ----------------------------------------------------
            # MINE EVALUATION
            # ----------------------------------------------------

            correct_mines = sorted(
                predicted_mines.intersection(
                    actual_mines
                )
            )

            mine_predictions = len(
                predicted_mines
            )

            mine_hits = len(
                correct_mines
            )

            mine_accuracy = (
                (
                    mine_hits
                    / mine_predictions
                    * 100.0
                )
                if mine_predictions
                else 0.0
            )

            # ----------------------------------------------------
            # COMBINED EVALUATION
            # ----------------------------------------------------

            total_predictions = (
                safe_predictions
                + mine_predictions
            )

            total_hits = (
                safe_hits
                + mine_hits
            )

            combined_accuracy = (
                (
                    total_hits
                    / total_predictions
                    * 100.0
                )
                if total_predictions
                else 0.0
            )

            backtest_results.append(
                BacktestGameResult(
                    sequence=index + 1,
                    signal_id=target_signal.id,
                    result_id=target_result.id,
                    recorded_at=target_result.recorded_at,
                    historical_results_used=len(
                        previous_results
                    ),
                    predicted_safe_positions=sorted(
                        predicted_safe
                    ),
                    actual_safe_positions=sorted(
                        actual_safe
                    ),
                    correct_safe_positions=correct_safe,
                    predicted_mine_positions=sorted(
                        predicted_mines
                    ),
                    actual_mine_positions=sorted(
                        actual_mines
                    ),
                    correct_mine_positions=correct_mines,
                    safe_predictions=safe_predictions,
                    safe_hits=safe_hits,
                    safe_accuracy=round(
                        safe_accuracy,
                        2,
                    ),
                    mine_predictions=mine_predictions,
                    mine_hits=mine_hits,
                    mine_accuracy=round(
                        mine_accuracy,
                        2,
                    ),
                    total_predictions=total_predictions,
                    total_hits=total_hits,
                    combined_accuracy=round(
                        combined_accuracy,
                        2,
                    ),
                    engine_confidence=prediction.confidence,
                )
            )

        # --------------------------------------------------------
        # AGGREGATE METRICS
        # --------------------------------------------------------

        evaluated = len(
            backtest_results
        )

        total_safe_predictions = sum(
            result.safe_predictions
            for result in backtest_results
        )

        total_safe_hits = sum(
            result.safe_hits
            for result in backtest_results
        )

        total_mine_predictions = sum(
            result.mine_predictions
            for result in backtest_results
        )

        total_mine_hits = sum(
            result.mine_hits
            for result in backtest_results
        )

        total_predictions = sum(
            result.total_predictions
            for result in backtest_results
        )

        total_hits = sum(
            result.total_hits
            for result in backtest_results
        )

        safe_accuracy = (
            (
                total_safe_hits
                / total_safe_predictions
                * 100.0
            )
            if total_safe_predictions
            else 0.0
        )

        mine_accuracy = (
            (
                total_mine_hits
                / total_mine_predictions
                * 100.0
            )
            if total_mine_predictions
            else 0.0
        )

        combined_accuracy = (
            (
                total_hits
                / total_predictions
                * 100.0
            )
            if total_predictions
            else 0.0
        )

        confidence_values = [
            result.engine_confidence
            for result in backtest_results
            if result.engine_confidence
            is not None
        ]

        average_confidence = (
            sum(confidence_values)
            / len(confidence_values)
            if confidence_values
            else None
        )

        return {
            "historical_results": len(
                results
            ),
            "evaluated_results": evaluated,
            "skipped_results": skipped_results,

            "total_safe_predictions":
                total_safe_predictions,

            "total_safe_hits":
                total_safe_hits,

            "safe_accuracy":
                round(
                    safe_accuracy,
                    2,
                ),

            "total_mine_predictions":
                total_mine_predictions,

            "total_mine_hits":
                total_mine_hits,

            "mine_accuracy":
                round(
                    mine_accuracy,
                    2,
                ),

            "total_predictions":
                total_predictions,

            "total_hits":
                total_hits,

            "combined_accuracy":
                round(
                    combined_accuracy,
                    2,
                ),

            "average_confidence":
                (
                    round(
                        average_confidence,
                        2,
                    )
                    if average_confidence
                    is not None
                    else None
                ),

            "results": [
                {
                    "sequence":
                        result.sequence,

                    "signal_id":
                        str(result.signal_id),

                    "result_id":
                        str(result.result_id),

                    "recorded_at":
                        result.recorded_at,

                    "historical_results_used":
                        result.historical_results_used,

                    "predicted_safe_positions":
                        result.predicted_safe_positions,

                    "actual_safe_positions":
                        result.actual_safe_positions,

                    "correct_safe_positions":
                        result.correct_safe_positions,

                    "predicted_mine_positions":
                        result.predicted_mine_positions,

                    "actual_mine_positions":
                        result.actual_mine_positions,

                    "correct_mine_positions":
                        result.correct_mine_positions,

                    "safe_predictions":
                        result.safe_predictions,

                    "safe_hits":
                        result.safe_hits,

                    "safe_accuracy":
                        result.safe_accuracy,

                    "mine_predictions":
                        result.mine_predictions,

                    "mine_hits":
                        result.mine_hits,

                    "mine_accuracy":
                        result.mine_accuracy,

                    "total_predictions":
                        result.total_predictions,

                    "total_hits":
                        result.total_hits,

                    "combined_accuracy":
                        result.combined_accuracy,

                    "engine_confidence":
                        result.engine_confidence,
                }
                for result in backtest_results
            ],
        }


pattern_backtesting_service = (
    PatternBacktestingService()
)
 
