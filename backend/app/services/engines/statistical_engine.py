from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.model import SignalModel
from app.models.result import ResultStatus, SignalResult
from app.models.signal import Signal

from app.services.engines.base_engine import (
    BaseEngine,
    EnginePrediction,
)


class StatisticalEngine(BaseEngine):
    """
    Historical statistical prediction engine.

    The engine examines completed SignalResult records that match
    the current signal's board size and mine count.

    Historical results include both successful and failed signals
    because the actual board outcome is useful regardless of whether
    the previous prediction was correct.

    Lower historical mine frequency:
        -> stronger safe-position candidate

    Higher historical mine frequency:
        -> stronger predicted-mine candidate

    This is a baseline statistical model. It does not claim that
    historical frequency can determine future random outcomes.
    """

    name = "statistical"
    version = "1.0.0"

    def predict(
        self,
        db: Session,
        signal: Signal,
        model: SignalModel,
    ) -> EnginePrediction:

        total_positions = (
            signal.board_size * signal.board_size
        )

        positions = list(
            range(1, total_positions + 1)
        )

        mine_count = signal.mine_count

        safe_count = min(
            8,
            total_positions - mine_count,
        )

        if safe_count <= 0:
            return EnginePrediction(
                safe_positions=[],
                predicted_mine_positions=positions[
                    :mine_count
                ],
                confidence=None,
            )

        # ---------------------------------------------------------
        # LOAD HISTORICAL RESULTS
        # ---------------------------------------------------------
        #
        # Only completed results matching the current board
        # configuration are used.
        #
        # Both SUCCESS and FAILED results are included because
        # the actual mine/safe positions are valuable historical
        # observations regardless of the previous prediction result.
        # ---------------------------------------------------------

        historical_results = self._get_historical_results(
            db=db,
            board_size=signal.board_size,
            mine_count=signal.mine_count,
        )

        # ---------------------------------------------------------
        # NO HISTORY
        # ---------------------------------------------------------

        if not historical_results:
            return self._neutral_prediction(
                positions=positions,
                mine_count=mine_count,
                safe_count=safe_count,
            )

        # ---------------------------------------------------------
        # CALCULATE POSITION FREQUENCIES
        # ---------------------------------------------------------

        mine_counts: dict[int, int] = defaultdict(int)
        safe_counts: dict[int, int] = defaultdict(int)

        total_games = len(historical_results)

        for result in historical_results:
            actual_mines = set(
                result.actual_mine_positions
            )

            actual_safe = set(
                result.actual_safe_positions
            )

            for position in actual_mines:
                mine_counts[position] += 1

            for position in actual_safe:
                safe_counts[position] += 1

        # ---------------------------------------------------------
        # SCORE POSITIONS
        # ---------------------------------------------------------

        position_scores = []

        for position in positions:
            mine_frequency = (
                mine_counts[position] / total_games
            )

            safe_frequency = (
                safe_counts[position] / total_games
            )

            # Higher score means historically safer.
            safety_score = (
                safe_frequency - mine_frequency
            )

            position_scores.append(
                (
                    position,
                    safety_score,
                    mine_frequency,
                )
            )

        # ---------------------------------------------------------
        # SAFE POSITIONS
        # ---------------------------------------------------------

        safe_ranked = sorted(
            position_scores,
            key=lambda item: (
                item[1],
                -item[2],
            ),
            reverse=True,
        )

        safe_positions = [
            item[0]
            for item in safe_ranked[:safe_count]
        ]

        # ---------------------------------------------------------
        # PREDICTED MINES
        # ---------------------------------------------------------

        mine_ranked = sorted(
            position_scores,
            key=lambda item: (
                item[2],
                -item[1],
            ),
            reverse=True,
        )

        predicted_mine_positions = [
            item[0]
            for item in mine_ranked[:mine_count]
        ]

        # ---------------------------------------------------------
        # CONFIDENCE
        # ---------------------------------------------------------

        confidence = self._calculate_confidence(
            total_games=total_games,
            position_scores=position_scores,
            safe_positions=safe_positions,
        )

        return EnginePrediction(
            safe_positions=sorted(
                safe_positions
            ),
            predicted_mine_positions=sorted(
                predicted_mine_positions
            ),
            confidence=confidence,
        )

    # -------------------------------------------------------------
    # HISTORICAL RESULTS
    # -------------------------------------------------------------

    def _get_historical_results(
        self,
        db: Session,
        board_size: int,
        mine_count: int,
    ) -> list[SignalResult]:
        """
        Load completed historical results that match the current
        signal configuration.

        We intentionally include both SUCCESS and FAILED results.

        A SUCCESS or FAILED status describes how the previous
        prediction performed. It does not change the fact that the
        recorded result contains an actual board outcome.

        Matching mine_count is important because a 5x5 board with
        3 mines represents a different configuration from a 5x5
        board with 5 or 7 mines.
        """

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
                SignalResult.recorded_at.asc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    # -------------------------------------------------------------
    # NEUTRAL BASELINE
    # -------------------------------------------------------------

    def _neutral_prediction(
        self,
        positions: list[int],
        mine_count: int,
        safe_count: int,
    ) -> EnginePrediction:
        """
        There is not enough historical data yet.

        We deliberately do not manufacture a confidence score.

        Positions are selected deterministically so that the system
        can operate while the historical dataset is being collected.
        """

        predicted_mine_positions = positions[
            :mine_count
        ]

        remaining_positions = [
            position
            for position in positions
            if position
            not in predicted_mine_positions
        ]

        safe_positions = remaining_positions[
            :safe_count
        ]

        return EnginePrediction(
            safe_positions=sorted(
                safe_positions
            ),
            predicted_mine_positions=sorted(
                predicted_mine_positions
            ),
            confidence=None,
        )

    # -------------------------------------------------------------
    # CONFIDENCE
    # -------------------------------------------------------------

    def _calculate_confidence(
        self,
        total_games: int,
        position_scores: list[
            tuple[int, float, float]
        ],
        safe_positions: list[int],
    ) -> float | None:

        if total_games <= 0:
            return None

        if not safe_positions:
            return None

        selected_scores = []

        for position, safety_score, _ in position_scores:
            if position in safe_positions:
                selected_scores.append(
                    safety_score
                )

        if not selected_scores:
            return None

        average_score = (
            sum(selected_scores)
            / len(selected_scores)
        )

        # Convert the historical separation score into a
        # conservative 0-100 confidence value.
        #
        # This is NOT prediction probability.
        normalized_score = (
            (average_score + 1.0)
            / 2.0
        )

        sample_factor = min(
            total_games / 100.0,
            1.0,
        )

        confidence = (
            normalized_score
            * sample_factor
            * 100.0
        )

        return round(
            max(
                0.0,
                min(
                    confidence,
                    100.0,
                ),
            ),
            2,
        )
 
