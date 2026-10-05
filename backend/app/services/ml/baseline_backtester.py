"""
Chronological positional-frequency baseline for Mines ML validation.

IMPORTANT:
This module is an evaluation baseline only.

It does NOT:
- modify Pattern Engine
- modify MLPredictor
- modify the trained RandomForest
- modify the live prediction pipeline

For every target historical game, positions are ranked using only
the completed games that occurred BEFORE the target game.

Baseline score:
    SAFE FREQUENCY = historical safe occurrences / historical games

Higher SAFE FREQUENCY means the position is ranked earlier.
"""


from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.ml.backtester import (
    GameBacktestResult,
)
from app.services.ml.dataset_builder import (
    MLDatasetBuilder,
)


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class PositionFrequency:
    """
    Historical frequency information for one board position.
    """

    position: int
    historical_games: int
    safe_count: int
    mine_count: int
    safe_rate: float
    mine_rate: float


@dataclass
class BaselineSummary:
    """
    Aggregate results for the positional-frequency baseline.
    """

    board_size: int
    mine_count: int
    total_cells: int

    games_evaluated: int

    average_top_1_precision: float
    average_top_3_precision: float
    average_top_5_precision: float

    top_1_hit_rate: float

    average_top_3_hits: float
    average_top_5_hits: float

    average_mine_hits_in_top_5: float

    model_name: str = "position_frequency_baseline"
    model_version: str = "1.0.0"
    feature_version: str = "none"
    model_path: str | None = None

    results: list[GameBacktestResult] | None = None


# ============================================================
# BACKTESTER
# ============================================================


class PositionFrequencyBacktester:
    """
    Chronological positional-frequency baseline.

    For each target game:

        1. Collect only games before the target.
        2. Calculate SAFE/MINE frequency for positions 1..N.
        3. Rank positions by historical SAFE frequency.
        4. Select the Top-N positions.
        5. Compare predictions with the target result.

    Target labels are NEVER used when generating the baseline
    prediction.
    """

    MODEL_NAME = "position_frequency_baseline"
    MODEL_VERSION = "1.0.0"

    def __init__(self, db: Session) -> None:
        self.db = db
        self.dataset_builder = MLDatasetBuilder(db)

    # ========================================================
    # PUBLIC API
    # ========================================================

    def run(
        self,
        board_size: int = 5,
        mine_count: int = 3,
        min_historical_games: int = 5,
        top_n: int = 5,
    ) -> BaselineSummary:
        """
        Run the chronological positional-frequency baseline.
        """

        if board_size <= 0:
            raise ValueError(
                "board_size must be greater than zero."
            )

        if mine_count <= 0:
            raise ValueError(
                "mine_count must be greater than zero."
            )

        total_cells = board_size * board_size

        if mine_count >= total_cells:
            raise ValueError(
                "mine_count must be smaller than the total "
                "number of cells."
            )

        if min_historical_games < 0:
            raise ValueError(
                "min_historical_games cannot be negative."
            )

        if top_n <= 0:
            raise ValueError(
                "top_n must be greater than zero."
            )

        top_n = min(
            top_n,
            total_cells,
        )

        # ----------------------------------------------------
        # Build complete chronological dataset.
        #
        # min_historical_games=0 is intentional here.
        # We need the complete history so that we can manually
        # construct the leakage-safe walk-forward windows.
        # ----------------------------------------------------

        records = self.dataset_builder.build_feature_records(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=0,
        )

        if not records:
            raise ValueError(
                "No historical ML dataset records were found."
            )

        games = self._group_games(records)

        if not games:
            raise ValueError(
                "No complete historical games were found."
            )

        games.sort(
            key=self._game_sort_key,
        )

        results: list[GameBacktestResult] = []

        # ====================================================
        # CHRONOLOGICAL WALK-FORWARD LOOP
        # ====================================================

        for game_index, target_game in enumerate(games):

            # ------------------------------------------------
            # Require enough previous games.
            # ------------------------------------------------

            if game_index < min_historical_games:
                continue

            # ------------------------------------------------
            # Validate target.
            # ------------------------------------------------

            self._validate_complete_game(
                target_game,
                board_size=board_size,
                mine_count=mine_count,
            )

            # ------------------------------------------------
            # ONLY previous games are available to the
            # baseline.
            # ------------------------------------------------

            historical_games = games[:game_index]

            if len(historical_games) < min_historical_games:
                continue

            # ------------------------------------------------
            # Rank positions using historical SAFE frequency.
            # ------------------------------------------------

            ranked_positions = self.rank_positions(
                historical_games=historical_games,
                total_cells=total_cells,
            )

            predicted_positions = ranked_positions[:top_n]

            # ------------------------------------------------
            # Evaluate target AFTER prediction.
            # ------------------------------------------------

            result = self._evaluate_game(
                game_records=target_game,
                predicted_positions=predicted_positions,
                historical_games_used=len(
                    historical_games
                ),
            )

            results.append(result)

        if not results:
            raise ValueError(
                "No games were eligible for baseline "
                "backtesting. Try reducing "
                "min_historical_games."
            )

        return self._build_summary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,
            results=results,
        )

    # ========================================================
    # POSITION FREQUENCY
    # ========================================================

    def calculate_position_frequencies(
        self,
        historical_games: list[list[dict[str, Any]]],
        total_cells: int,
    ) -> list[PositionFrequency]:
        """
        Calculate historical SAFE/MINE frequency for every
        board position.

        This method only uses the supplied historical games.
        """

        safe_counts = {
            position: 0
            for position in range(
                1,
                total_cells + 1,
            )
        }

        mine_counts = {
            position: 0
            for position in range(
                1,
                total_cells + 1,
            )
        }

        for game in historical_games:
            for record in game:
                position = int(
                    record["position"]
                )

                label = int(
                    record["label"]
                )

                if label == 1:
                    safe_counts[position] += 1

                elif label == 0:
                    mine_counts[position] += 1

                else:
                    raise ValueError(
                        f"Invalid label {label} at "
                        f"position {position}."
                    )

        frequencies: list[PositionFrequency] = []

        for position in range(
            1,
            total_cells + 1,
        ):
            safe_count = safe_counts[position]
            mine_count = mine_counts[position]

            historical_games_count = (
                safe_count + mine_count
            )

            if historical_games_count > 0:
                safe_rate = (
                    safe_count
                    / historical_games_count
                )

                mine_rate = (
                    mine_count
                    / historical_games_count
                )
            else:
                safe_rate = 0.0
                mine_rate = 0.0

            frequencies.append(
                PositionFrequency(
                    position=position,
                    historical_games=(
                        historical_games_count
                    ),
                    safe_count=safe_count,
                    mine_count=mine_count,
                    safe_rate=safe_rate,
                    mine_rate=mine_rate,
                )
            )

        return frequencies

    # ========================================================
    # RANK POSITIONS
    # ========================================================

    def rank_positions(
        self,
        historical_games: list[list[dict[str, Any]]],
        total_cells: int,
    ) -> list[int]:
        """
        Rank positions using historical SAFE frequency.

        Ranking order:

            1. Highest SAFE rate
            2. Highest SAFE count
            3. Lowest MINE count
            4. Lowest position number

        The final position-number tie-breaker makes the baseline
        deterministic.
        """

        frequencies = (
            self.calculate_position_frequencies(
                historical_games=historical_games,
                total_cells=total_cells,
            )
        )

        frequencies.sort(
            key=lambda item: (
                -item.safe_rate,
                -item.safe_count,
                item.mine_count,
                item.position,
            )
        )

        return [
            item.position
            for item in frequencies
        ]

    # ========================================================
    # GROUP GAMES
    # ========================================================

    def _group_games(
        self,
        records: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:
        """
        Group position records by result_id.
        """

        grouped: dict[
            str,
            list[dict[str, Any]],
        ] = {}

        for record in records:
            result_id = record.get(
                "result_id"
            )

            if result_id is None:
                raise ValueError(
                    "Dataset record is missing "
                    "result_id."
                )

            key = str(result_id)

            grouped.setdefault(
                key,
                [],
            ).append(record)

        return list(
            grouped.values()
        )

    # ========================================================
    # CHRONOLOGICAL SORT
    # ========================================================

    def _game_sort_key(
        self,
        game_records: list[dict[str, Any]],
    ) -> datetime:
        """
        Sort using recorded_at first, then generated_at.
        """

        first_record = game_records[0]

        recorded_at = first_record.get(
            "recorded_at"
        )

        if isinstance(
            recorded_at,
            datetime,
        ):
            return recorded_at

        generated_at = first_record.get(
            "generated_at"
        )

        if isinstance(
            generated_at,
            datetime,
        ):
            return generated_at

        return datetime.min

    # ========================================================
    # VALIDATION
    # ========================================================

    def _validate_complete_game(
        self,
        game_records: list[dict[str, Any]],
        board_size: int,
        mine_count: int,
    ) -> None:
        """
        Validate complete board and label distribution.
        """

        total_cells = (
            board_size * board_size
        )

        if len(game_records) != total_cells:
            result_id = game_records[0].get(
                "result_id"
            )

            raise ValueError(
                f"Historical game {result_id} has "
                f"{len(game_records)} records, expected "
                f"{total_cells}."
            )

        positions: set[int] = set()
        safe_positions: set[int] = set()
        mine_positions: set[int] = set()

        for record in game_records:
            position = int(
                record["position"]
            )

            if position < 1 or position > total_cells:
                raise ValueError(
                    f"Invalid board position {position}. "
                    f"Expected 1-{total_cells}."
                )

            if position in positions:
                raise ValueError(
                    f"Duplicate board position {position}."
                )

            positions.add(position)

            label = int(
                record["label"]
            )

            if label == 1:
                safe_positions.add(position)

            elif label == 0:
                mine_positions.add(position)

            else:
                raise ValueError(
                    f"Invalid label {label}. "
                    "Expected 0 or 1."
                )

        expected_positions = set(
            range(
                1,
                total_cells + 1,
            )
        )

        if positions != expected_positions:
            missing = sorted(
                expected_positions - positions
            )

            extra = sorted(
                positions - expected_positions
            )

            raise ValueError(
                "Historical game does not contain "
                f"the complete board. Missing={missing}, "
                f"Extra={extra}"
            )

        if len(mine_positions) != mine_count:
            result_id = game_records[0].get(
                "result_id"
            )

            raise ValueError(
                f"Historical game {result_id} has "
                f"{len(mine_positions)} mines, expected "
                f"{mine_count}."
            )

        expected_safe_count = (
            total_cells - mine_count
        )

        if len(safe_positions) != expected_safe_count:
            result_id = game_records[0].get(
                "result_id"
            )

            raise ValueError(
                f"Historical game {result_id} has "
                f"{len(safe_positions)} safe positions, "
                f"expected {expected_safe_count}."
            )

    # ========================================================
    # EVALUATION
    # ========================================================

    def _evaluate_game(
        self,
        game_records: list[dict[str, Any]],
        predicted_positions: list[int],
        historical_games_used: int,
    ) -> GameBacktestResult:
        """
        Evaluate predictions against the target game's labels.

        This method is only called AFTER predictions have
        already been generated.
        """

        first_record = game_records[0]

        result_id = str(
            first_record["result_id"]
        )

        signal_id = str(
            first_record["signal_id"]
        )

        actual_safe_positions = sorted(
            int(record["position"])
            for record in game_records
            if int(record["label"]) == 1
        )

        actual_mine_positions = sorted(
            int(record["position"])
            for record in game_records
            if int(record["label"]) == 0
        )

        actual_safe_set = set(
            actual_safe_positions
        )

        actual_mine_set = set(
            actual_mine_positions
        )

        top_1 = predicted_positions[:1]
        top_3 = predicted_positions[:3]
        top_5 = predicted_positions[:5]

        top_1_safe_hits = sum(
            1
            for position in top_1
            if position in actual_safe_set
        )

        top_3_safe_hits = sum(
            1
            for position in top_3
            if position in actual_safe_set
        )

        top_5_safe_hits = sum(
            1
            for position in top_5
            if position in actual_safe_set
        )

        safe_precision_at_1 = (
            top_1_safe_hits / len(top_1)
            if top_1
            else 0.0
        )

        safe_precision_at_3 = (
            top_3_safe_hits / len(top_3)
            if top_3
            else 0.0
        )

        safe_precision_at_5 = (
            top_5_safe_hits / len(top_5)
            if top_5
            else 0.0
        )

        top_1_hit = (
            bool(top_1)
            and top_1[0] in actual_safe_set
        )

        mine_hits_in_top_5 = sum(
            1
            for position in top_5
            if position in actual_mine_set
        )

        return GameBacktestResult(
            result_id=result_id,
            signal_id=signal_id,
            board_size=int(
                first_record["board_size"]
            ),
            mine_count=int(
                first_record["mine_count"]
            ),
            total_cells=int(
                first_record["total_cells"]
            ),
            historical_games_used=(
                historical_games_used
            ),
            actual_safe_positions=(
                actual_safe_positions
            ),
            actual_mine_positions=(
                actual_mine_positions
            ),
            predicted_safe_positions=(
                predicted_positions
            ),
            top_1_hit=top_1_hit,
            top_3_hits=top_3_safe_hits,
            top_5_hits=top_5_safe_hits,
            safe_precision_at_1=(
                safe_precision_at_1
            ),
            safe_precision_at_3=(
                safe_precision_at_3
            ),
            safe_precision_at_5=(
                safe_precision_at_5
            ),
            mine_hits_in_top_5=(
                mine_hits_in_top_5
            ),
            generated_at=first_record.get(
                "generated_at"
            ),
            recorded_at=first_record.get(
                "recorded_at"
            ),
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    def _build_summary(
        self,
        board_size: int,
        mine_count: int,
        total_cells: int,
        results: list[GameBacktestResult],
    ) -> BaselineSummary:
        games_evaluated = len(results)

        return BaselineSummary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,
            games_evaluated=games_evaluated,
            average_top_1_precision=self._average(
                result.safe_precision_at_1
                for result in results
            ),
            average_top_3_precision=self._average(
                result.safe_precision_at_3
                for result in results
            ),
            average_top_5_precision=self._average(
                result.safe_precision_at_5
                for result in results
            ),
            top_1_hit_rate=self._average(
                1.0 if result.top_1_hit else 0.0
                for result in results
            ),
            average_top_3_hits=self._average(
                result.top_3_hits
                for result in results
            ),
            average_top_5_hits=self._average(
                result.top_5_hits
                for result in results
            ),
            average_mine_hits_in_top_5=self._average(
                result.mine_hits_in_top_5
                for result in results
            ),
            results=results,
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _average(values: Any) -> float:
        values = list(values)

        if not values:
            return 0.0

        return sum(
            float(value)
            for value in values
        ) / len(values)
 
