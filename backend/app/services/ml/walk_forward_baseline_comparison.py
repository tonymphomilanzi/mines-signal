"""
True walk-forward comparison between:

1. RandomForest ML
2. Historical positional-frequency baseline

Both methods are evaluated on exactly the same target games.

For every target game:

    historical games
          |
          +----> train RandomForest
          |
          +----> build historical-frequency baseline
          |
          v
      target game
          |
          v
      compare results

IMPORTANT:
- No future games are used.
- A fresh RandomForest is trained for every target game.
- The baseline only sees games before the target.
- Nothing is saved to the production model.
- Pattern Engine is not modified.

Usage:
    python -m app.services.ml.walk_forward_baseline_comparison
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.db.session import SessionLocal
from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.feature_builder import MLFeatureBuilder


# ------------------------------------------------------------
# MODEL CONFIGURATION
# ------------------------------------------------------------

MODEL_NAME = "mines_random_forest"
MODEL_VERSION = "1.0.0"
FEATURE_VERSION = "2.0.0"

N_ESTIMATORS = 300
MAX_DEPTH = 8
MIN_SAMPLES_SPLIT = 8
MIN_SAMPLES_LEAF = 4
CLASS_WEIGHT = "balanced"
RANDOM_STATE = 42


# ------------------------------------------------------------
# RESULT DATACLASS
# ------------------------------------------------------------

@dataclass
class ComparisonGameResult:
    result_id: str
    signal_id: str

    historical_games: int

    training_rows: int
    training_safe_rows: int
    training_mine_rows: int

    ml_predictions: list[int]
    baseline_predictions: list[int]

    actual_safe_positions: list[int]
    actual_mine_positions: list[int]

    ml_top_1_hit: bool
    ml_top_3_hits: int
    ml_top_5_hits: int

    baseline_top_1_hit: bool
    baseline_top_3_hits: int
    baseline_top_5_hits: int

    ml_mines_in_top_5: int
    baseline_mines_in_top_5: int

    ml_top_1_precision: float
    ml_top_3_precision: float
    ml_top_5_precision: float

    baseline_top_1_precision: float
    baseline_top_3_precision: float
    baseline_top_5_precision: float

    generated_at: datetime | None = None
    recorded_at: datetime | None = None


@dataclass
class ComparisonSummary:
    games_available: int
    games_skipped: int
    games_evaluated: int

    ml_average_top_1_precision: float
    ml_average_top_3_precision: float
    ml_average_top_5_precision: float

    ml_top_1_hit_rate: float
    ml_average_top_3_hits: float
    ml_average_top_5_hits: float
    ml_average_mines_in_top_5: float

    baseline_average_top_1_precision: float
    baseline_average_top_3_precision: float
    baseline_average_top_5_precision: float

    baseline_top_1_hit_rate: float
    baseline_average_top_3_hits: float
    baseline_average_top_5_hits: float
    baseline_average_mines_in_top_5: float

    ml_better_top_5_games: int
    baseline_better_top_5_games: int
    tied_top_5_games: int

    same_top_1_games: int

    results: list[ComparisonGameResult]

    model_name: str
    model_version: str
    feature_version: str


# ------------------------------------------------------------
# BACKTESTER
# ------------------------------------------------------------

class WalkForwardBaselineComparison:
    """
    Compares RandomForest against historical position frequency
    using strict chronological walk-forward evaluation.
    """

    def __init__(self, db) -> None:
        self.db = db

        self.dataset_builder = MLDatasetBuilder(db)

        self.feature_builder = MLFeatureBuilder()

        self.feature_names = (
            self.feature_builder.feature_names()
        )

    # --------------------------------------------------------
    # RUN
    # --------------------------------------------------------

    def run(
        self,
        *,
        board_size: int = 5,
        mine_count: int = 3,
        min_historical_games: int = 5,
        top_n: int = 5,
    ) -> ComparisonSummary:

        records = (
            self.dataset_builder.build_feature_records(
                board_size=board_size,
                mine_count=mine_count,
                min_historical_games=0,
            )
        )

        games = self._group_games(records)

        games_available = len(games)

        results: list[ComparisonGameResult] = []

        games_skipped = 0

        for game_index in range(len(games)):
            if game_index < min_historical_games:
                games_skipped += 1
                continue

            historical_games = games[:game_index]
            target_game = games[game_index]

            result = self._evaluate_game(
                historical_games=historical_games,
                target_game=target_game,
                board_size=board_size,
                mine_count=mine_count,
                top_n=top_n,
            )

            results.append(result)

        return self._build_summary(
            games_available=games_available,
            games_skipped=games_skipped,
            results=results,
        )

    # --------------------------------------------------------
    # GROUP GAMES
    # --------------------------------------------------------

    def _group_games(
        self,
        records: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for record in records:
            grouped[
                str(record["result_id"])
            ].append(record)

        games = list(grouped.values())

        games.sort(
            key=lambda game: (
                min(
                    (
                        record["recorded_at"]
                        for record in game
                        if record.get("recorded_at") is not None
                    ),
                    default=datetime.min,
                ),
                min(
                    (
                        record["generated_at"]
                        for record in game
                        if record.get("generated_at") is not None
                    ),
                    default=datetime.min,
                ),
            )
        )

        return games

    # --------------------------------------------------------
    # EVALUATE GAME
    # --------------------------------------------------------

    def _evaluate_game(
        self,
        *,
        historical_games: list[list[dict[str, Any]]],
        target_game: list[dict[str, Any]],
        board_size: int,
        mine_count: int,
        top_n: int,
    ) -> ComparisonGameResult:

        training_records = [
            record
            for game in historical_games
            for record in game
        ]

        training_x, training_y = (
            self._build_training_matrix(
                training_records
            )
        )

        model = self._train_model(
            training_x,
            training_y,
        )

        ml_predictions = self._predict_ml(
            model=model,
            historical_games=historical_games,
            board_size=board_size,
            mine_count=mine_count,
            top_n=top_n,
        )

        baseline_predictions = (
            self._predict_baseline(
                historical_games=historical_games,
                total_cells=board_size * board_size,
                top_n=top_n,
            )
        )

        actual_safe = sorted(
            int(record["position"])
            for record in target_game
            if int(record["label"]) == 1
        )

        actual_mines = sorted(
            int(record["position"])
            for record in target_game
            if int(record["label"]) == 0
        )

        ml_metrics = self._calculate_metrics(
            predictions=ml_predictions,
            actual_safe=actual_safe,
            actual_mines=actual_mines,
            top_n=top_n,
        )

        baseline_metrics = self._calculate_metrics(
            predictions=baseline_predictions,
            actual_safe=actual_safe,
            actual_mines=actual_mines,
            top_n=top_n,
        )

        first_record = target_game[0]

        return ComparisonGameResult(
            result_id=str(first_record["result_id"]),
            signal_id=str(first_record["signal_id"]),

            historical_games=len(historical_games),

            training_rows=len(training_y),
            training_safe_rows=int(
                np.sum(training_y == 1)
            ),
            training_mine_rows=int(
                np.sum(training_y == 0)
            ),

            ml_predictions=ml_predictions,
            baseline_predictions=baseline_predictions,

            actual_safe_positions=actual_safe,
            actual_mine_positions=actual_mines,

            ml_top_1_hit=ml_metrics["top_1_hit"],
            ml_top_3_hits=ml_metrics["top_3_hits"],
            ml_top_5_hits=ml_metrics["top_5_hits"],

            baseline_top_1_hit=baseline_metrics[
                "top_1_hit"
            ],
            baseline_top_3_hits=baseline_metrics[
                "top_3_hits"
            ],
            baseline_top_5_hits=baseline_metrics[
                "top_5_hits"
            ],

            ml_mines_in_top_5=ml_metrics[
                "mines_in_top_5"
            ],
            baseline_mines_in_top_5=baseline_metrics[
                "mines_in_top_5"
            ],

            ml_top_1_precision=ml_metrics[
                "top_1_precision"
            ],
            ml_top_3_precision=ml_metrics[
                "top_3_precision"
            ],
            ml_top_5_precision=ml_metrics[
                "top_5_precision"
            ],

            baseline_top_1_precision=baseline_metrics[
                "top_1_precision"
            ],
            baseline_top_3_precision=baseline_metrics[
                "top_3_precision"
            ],
            baseline_top_5_precision=baseline_metrics[
                "top_5_precision"
            ],

            generated_at=first_record.get(
                "generated_at"
            ),
            recorded_at=first_record.get(
                "recorded_at"
            ),
        )

    # --------------------------------------------------------
    # TRAINING MATRIX
    # --------------------------------------------------------

    def _build_training_matrix(
        self,
        records: list[dict[str, Any]],
    ) -> tuple[np.ndarray, np.ndarray]:

        x = np.asarray(
            [
                self.feature_builder.build_feature_row(
                    record
                )
                for record in records
            ],
            dtype=float,
        )

        y = np.asarray(
            [
                int(record["label"])
                for record in records
            ],
            dtype=int,
        )

        return x, y

    # --------------------------------------------------------
    # TRAIN MODEL
    # --------------------------------------------------------

    def _train_model(
        self,
        x: np.ndarray,
        y: np.ndarray,
    ) -> RandomForestClassifier:

        model = RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            max_depth=MAX_DEPTH,
            min_samples_split=MIN_SAMPLES_SPLIT,
            min_samples_leaf=MIN_SAMPLES_LEAF,
            class_weight=CLASS_WEIGHT,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

        model.fit(x, y)

        return model

    # --------------------------------------------------------
    # ML PREDICTION
    # --------------------------------------------------------

    def _predict_ml(
        self,
        *,
        model: RandomForestClassifier,
        historical_games: list[list[dict[str, Any]]],
        board_size: int,
        mine_count: int,
        top_n: int,
    ) -> list[int]:

        historical_records = [
            record
            for game in historical_games
            for record in game
        ]

        total_cells = board_size * board_size

        prediction_records: list[dict[str, Any]] = []

        for position in range(1, total_cells + 1):
            row = (position - 1) // board_size
            column = (position - 1) % board_size

            prediction_records.append(
                self._build_prediction_record(
                    historical_records=historical_records,
                    board_size=board_size,
                    mine_count=mine_count,
                    position=position,
                    row=row,
                    column=column,
                )
            )

        x = np.asarray(
            [
                self.feature_builder.build_feature_row(
                    record
                )
                for record in prediction_records
            ],
            dtype=float,
        )

        probabilities = model.predict_proba(x)

        class_index = list(
            model.classes_
        ).index(1)

        safe_probabilities = probabilities[
            :,
            class_index,
        ]

        ranked = sorted(
            zip(
                range(1, total_cells + 1),
                safe_probabilities,
            ),
            key=lambda item: (
                -float(item[1]),
                item[0],
            ),
        )

        return [
            position
            for position, _ in ranked[:top_n]
        ]

    # --------------------------------------------------------
    # PREDICTION RECORD
    # --------------------------------------------------------

    def _build_prediction_record(
        self,
        *,
        historical_records: list[dict[str, Any]],
        board_size: int,
        mine_count: int,
        position: int,
        row: int,
        column: int,
    ) -> dict[str, Any]:

        total_cells = board_size * board_size

        position_history = [
            record
            for record in historical_records
            if int(record["position"]) == position
        ]

        historical_games = len(
            historical_records
        ) // total_cells

        historical_safe_count = sum(
            int(record["label"]) == 1
            for record in position_history
        )

        historical_mine_count = sum(
            int(record["label"]) == 0
            for record in position_history
        )

        recent_records = sorted(
            historical_records,
            key=lambda record: (
                record.get("recorded_at")
                or datetime.min,
                record.get("generated_at")
                or datetime.min,
            ),
        )

        recent_games = self._get_recent_game_records(
            recent_records,
            total_cells,
            5,
        )

        recent_10_games = self._get_recent_game_records(
            recent_records,
            total_cells,
            10,
        )

        recent_5_position_records = [
            record
            for game in recent_games
            for record in game
            if int(record["position"]) == position
        ]

        recent_10_position_records = [
            record
            for game in recent_10_games
            for record in game
            if int(record["position"]) == position
        ]

        recent_5_safe_count = sum(
            int(record["label"]) == 1
            for record in recent_5_position_records
        )

        recent_5_mine_count = sum(
            int(record["label"]) == 0
            for record in recent_5_position_records
        )

        recent_10_safe_count = sum(
            int(record["label"]) == 1
            for record in recent_10_position_records
        )

        recent_10_mine_count = sum(
            int(record["label"]) == 0
            for record in recent_10_position_records
        )

        safe_streak = self._current_streak(
            historical_records,
            position,
            total_cells,
            desired_label=1,
        )

        mine_streak = self._current_streak(
            historical_records,
            position,
            total_cells,
            desired_label=0,
        )

        return {
            "signal_id": "prediction",
            "result_id": "prediction",

            "board_size": board_size,
            "mine_count": mine_count,
            "total_cells": total_cells,

            "position": position,
            "row": row,
            "column": column,

            "historical_games": historical_games,
            "historical_safe_count": historical_safe_count,
            "historical_mine_count": historical_mine_count,

            "recent_5_games": len(recent_games),
            "recent_5_safe_count": recent_5_safe_count,
            "recent_5_mine_count": recent_5_mine_count,

            "recent_10_games": len(recent_10_games),
            "recent_10_safe_count": recent_10_safe_count,
            "recent_10_mine_count": recent_10_mine_count,

            "safe_streak": safe_streak,
            "mine_streak": mine_streak,

            # Feature builder does not use label as a feature.
            "label": 1,
        }

    # --------------------------------------------------------
    # RECENT GAMES
    # --------------------------------------------------------

    @staticmethod
    def _get_recent_game_records(
        records: list[dict[str, Any]],
        total_cells: int,
        count: int,
    ) -> list[list[dict[str, Any]]]:

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(
            list
        )

        for record in records:
            grouped[
                str(record["result_id"])
            ].append(record)

        games = list(grouped.values())

        games.sort(
            key=lambda game: (
                min(
                    (
                        record["recorded_at"]
                        for record in game
                        if record.get("recorded_at") is not None
                    ),
                    default=datetime.min,
                ),
                min(
                    (
                        record["generated_at"]
                        for record in game
                        if record.get("generated_at") is not None
                    ),
                    default=datetime.min,
                ),
            )
        )

        return games[-count:]

    # --------------------------------------------------------
    # STREAK
    # --------------------------------------------------------

    @staticmethod
    def _current_streak(
        records: list[dict[str, Any]],
        position: int,
        total_cells: int,
        desired_label: int,
    ) -> int:

        games = (
            WalkForwardBaselineComparison
            ._get_recent_game_records(
                records,
                total_cells,
                len(records) // total_cells,
            )
        )

        streak = 0

        for game in reversed(games):
            matching = next(
                (
                    record
                    for record in game
                    if int(record["position"]) == position
                ),
                None,
            )

            if matching is None:
                break

            if int(matching["label"]) == desired_label:
                streak += 1
            else:
                break

        return streak

    # --------------------------------------------------------
    # BASELINE
    # --------------------------------------------------------

    def _predict_baseline(
        self,
        *,
        historical_games: list[list[dict[str, Any]]],
        total_cells: int,
        top_n: int,
    ) -> list[int]:

        stats: dict[int, dict[str, int]] = {
            position: {
                "safe": 0,
                "mine": 0,
            }
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
                    stats[position]["safe"] += 1
                else:
                    stats[position]["mine"] += 1

        def sort_key(position: int):
            safe = stats[position]["safe"]
            mine = stats[position]["mine"]
            total = safe + mine

            safe_rate = (
                safe / total
                if total > 0
                else 0.0
            )

            return (
                -safe_rate,
                -safe,
                mine,
                position,
            )

        ranked_positions = sorted(
            stats.keys(),
            key=sort_key,
        )

        return ranked_positions[:top_n]

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    @staticmethod
    def _calculate_metrics(
        *,
        predictions: list[int],
        actual_safe: list[int],
        actual_mines: list[int],
        top_n: int,
    ) -> dict[str, Any]:

        actual_safe_set = set(
            actual_safe
        )

        actual_mine_set = set(
            actual_mines
        )

        top_1 = predictions[:1]
        top_3 = predictions[:3]
        top_5 = predictions[:top_n]

        top_1_hits = len(
            set(top_1) & actual_safe_set
        )

        top_3_hits = len(
            set(top_3) & actual_safe_set
        )

        top_5_hits = len(
            set(top_5) & actual_safe_set
        )

        mines_in_top_5 = len(
            set(top_5) & actual_mine_set
        )

        return {
            "top_1_hit": top_1_hits > 0,

            "top_3_hits": top_3_hits,
            "top_5_hits": top_5_hits,

            "top_1_precision": (
                top_1_hits / len(top_1)
                if top_1
                else 0.0
            ),

            "top_3_precision": (
                top_3_hits / len(top_3)
                if top_3
                else 0.0
            ),

            "top_5_precision": (
                top_5_hits / len(top_5)
                if top_5
                else 0.0
            ),

            "mines_in_top_5": mines_in_top_5,
        }

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    def _build_summary(
        self,
        *,
        games_available: int,
        games_skipped: int,
        results: list[ComparisonGameResult],
    ) -> ComparisonSummary:

        games_evaluated = len(results)

        if not results:
            return ComparisonSummary(
                games_available=games_available,
                games_skipped=games_skipped,
                games_evaluated=0,

                ml_average_top_1_precision=0.0,
                ml_average_top_3_precision=0.0,
                ml_average_top_5_precision=0.0,

                ml_top_1_hit_rate=0.0,
                ml_average_top_3_hits=0.0,
                ml_average_top_5_hits=0.0,
                ml_average_mines_in_top_5=0.0,

                baseline_average_top_1_precision=0.0,
                baseline_average_top_3_precision=0.0,
                baseline_average_top_5_precision=0.0,

                baseline_top_1_hit_rate=0.0,
                baseline_average_top_3_hits=0.0,
                baseline_average_top_5_hits=0.0,
                baseline_average_mines_in_top_5=0.0,

                ml_better_top_5_games=0,
                baseline_better_top_5_games=0,
                tied_top_5_games=0,

                same_top_1_games=0,

                results=[],

                model_name=MODEL_NAME,
                model_version=MODEL_VERSION,
                feature_version=FEATURE_VERSION,
            )

        ml_top_1_precision = np.mean(
            [
                result.ml_top_1_precision
                for result in results
            ]
        )

        ml_top_3_precision = np.mean(
            [
                result.ml_top_3_precision
                for result in results
            ]
        )

        ml_top_5_precision = np.mean(
            [
                result.ml_top_5_precision
                for result in results
            ]
        )

        ml_top_1_hit_rate = np.mean(
            [
                result.ml_top_1_hit
                for result in results
            ]
        )

        ml_average_top_3_hits = np.mean(
            [
                result.ml_top_3_hits
                for result in results
            ]
        )

        ml_average_top_5_hits = np.mean(
            [
                result.ml_top_5_hits
                for result in results
            ]
        )

        ml_average_mines = np.mean(
            [
                result.ml_mines_in_top_5
                for result in results
            ]
        )

        baseline_top_1_precision = np.mean(
            [
                result.baseline_top_1_precision
                for result in results
            ]
        )

        baseline_top_3_precision = np.mean(
            [
                result.baseline_top_3_precision
                for result in results
            ]
        )

        baseline_top_5_precision = np.mean(
            [
                result.baseline_top_5_precision
                for result in results
            ]
        )

        baseline_top_1_hit_rate = np.mean(
            [
                result.baseline_top_1_hit
                for result in results
            ]
        )

        baseline_average_top_3_hits = np.mean(
            [
                result.baseline_top_3_hits
                for result in results
            ]
        )

        baseline_average_top_5_hits = np.mean(
            [
                result.baseline_top_5_hits
                for result in results
            ]
        )

        baseline_average_mines = np.mean(
            [
                result.baseline_mines_in_top_5
                for result in results
            ]
        )

        ml_better = sum(
            result.ml_top_5_hits
            > result.baseline_top_5_hits
            for result in results
        )

        baseline_better = sum(
            result.baseline_top_5_hits
            > result.ml_top_5_hits
            for result in results
        )

        tied = sum(
            result.ml_top_5_hits
            == result.baseline_top_5_hits
            for result in results
        )

        same_top_1 = sum(
            result.ml_predictions[0]
            == result.baseline_predictions[0]
            for result in results
        )

        return ComparisonSummary(
            games_available=games_available,
            games_skipped=games_skipped,
            games_evaluated=games_evaluated,

            ml_average_top_1_precision=float(
                ml_top_1_precision
            ),
            ml_average_top_3_precision=float(
                ml_top_3_precision
            ),
            ml_average_top_5_precision=float(
                ml_top_5_precision
            ),

            ml_top_1_hit_rate=float(
                ml_top_1_hit_rate
            ),
            ml_average_top_3_hits=float(
                ml_average_top_3_hits
            ),
            ml_average_top_5_hits=float(
                ml_average_top_5_hits
            ),
            ml_average_mines_in_top_5=float(
                ml_average_mines
            ),

            baseline_average_top_1_precision=float(
                baseline_top_1_precision
            ),
            baseline_average_top_3_precision=float(
                baseline_top_3_precision
            ),
            baseline_average_top_5_precision=float(
                baseline_top_5_precision
            ),

            baseline_top_1_hit_rate=float(
                baseline_top_1_hit_rate
            ),
            baseline_average_top_3_hits=float(
                baseline_average_top_3_hits
            ),
            baseline_average_top_5_hits=float(
                baseline_average_top_5_hits
            ),
            baseline_average_mines_in_top_5=float(
                baseline_average_mines
            ),

            ml_better_top_5_games=ml_better,
            baseline_better_top_5_games=baseline_better,
            tied_top_5_games=tied,

            same_top_1_games=same_top_1,

            results=results,

            model_name=MODEL_NAME,
            model_version=MODEL_VERSION,
            feature_version=FEATURE_VERSION,
        )


# ------------------------------------------------------------
# TEST RUNNER
# ------------------------------------------------------------

def main() -> None:
    db = SessionLocal()

    try:
        board_size = 5
        mine_count = 3
        min_historical_games = 5
        top_n = 5

        print("=" * 100)
        print(
            "MINES AI — WALK-FORWARD ML vs BASELINE"
        )
        print("=" * 100)

        print()
        print("CONFIGURATION")
        print("-" * 100)
        print(
            f"Board size            : "
            f"{board_size}x{board_size}"
        )
        print(
            f"Mine count            : "
            f"{mine_count}"
        )
        print(
            f"Minimum history       : "
            f"{min_historical_games}"
        )
        print(
            f"Top N                 : "
            f"{top_n}"
        )

        comparison = (
            WalkForwardBaselineComparison(db)
        )

        summary = comparison.run(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=min_historical_games,
            top_n=top_n,
        )

        print()
        print("MODEL")
        print("-" * 100)
        print(
            f"Model                 : "
            f"{summary.model_name}"
        )
        print(
            f"Model version         : "
            f"{summary.model_version}"
        )
        print(
            f"Feature version       : "
            f"{summary.feature_version}"
        )

        print()
        print("DATASET")
        print("-" * 100)
        print(
            f"Games available       : "
            f"{summary.games_available}"
        )
        print(
            f"Games skipped         : "
            f"{summary.games_skipped}"
        )
        print(
            f"Games evaluated       : "
            f"{summary.games_evaluated}"
        )

        if not summary.results:
            print()
            print(
                "No games were available "
                "for comparison."
            )
            return

        # ----------------------------------------------------
        # PER-GAME COMPARISON
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("PER-GAME COMPARISON")
        print("=" * 100)

        for index, result in enumerate(
            summary.results,
            start=1,
        ):
            if (
                result.ml_top_5_hits
                > result.baseline_top_5_hits
            ):
                winner = "ML"

            elif (
                result.baseline_top_5_hits
                > result.ml_top_5_hits
            ):
                winner = "BASELINE"

            else:
                winner = "TIE"

            print()
            print(
                f"GAME {index:02d} "
                f"| History: "
                f"{result.historical_games}"
            )

            print("-" * 100)

            print(
                "Training"
            )
            print(
                f"  Rows                : "
                f"{result.training_rows}"
            )
            print(
                f"  SAFE                : "
                f"{result.training_safe_rows}"
            )
            print(
                f"  MINE                : "
                f"{result.training_mine_rows}"
            )

            print()
            print(
                "ML RandomForest"
            )
            print(
                f"  Predictions         : "
                f"{result.ml_predictions}"
            )
            print(
                f"  Top-1 hit           : "
                f"{'YES' if result.ml_top_1_hit else 'NO'}"
            )
            print(
                f"  Top-3 hits          : "
                f"{result.ml_top_3_hits}/3"
            )
            print(
                f"  Top-5 hits          : "
                f"{result.ml_top_5_hits}/5"
            )
            print(
                f"  Mines in Top-5      : "
                f"{result.ml_mines_in_top_5}"
            )

            print()
            print(
                "Historical Baseline"
            )
            print(
                f"  Predictions         : "
                f"{result.baseline_predictions}"
            )
            print(
                f"  Top-1 hit           : "
                f"{'YES' if result.baseline_top_1_hit else 'NO'}"
            )
            print(
                f"  Top-3 hits          : "
                f"{result.baseline_top_3_hits}/3"
            )
            print(
                f"  Top-5 hits          : "
                f"{result.baseline_top_5_hits}/5"
            )
            print(
                f"  Mines in Top-5      : "
                f"{result.baseline_mines_in_top_5}"
            )

            print()
            print(
                f"Actual SAFE          : "
                f"{result.actual_safe_positions}"
            )
            print(
                f"Actual MINE          : "
                f"{result.actual_mine_positions}"
            )

            print()
            print(
                f"Top-5 result         : "
                f"{winner}"
            )

        # ----------------------------------------------------
        # AGGREGATE
        # ----------------------------------------------------

        print()
        print("=" * 100)
        print("AGGREGATE PERFORMANCE")
        print("=" * 100)

        print()
        print(
            f"{'Metric':<32}"
            f"{'RandomForest':>18}"
            f"{'Baseline':>18}"
        )

        print("-" * 70)

        print(
            f"{'Average Top-1 precision':<32}"
            f"{summary.ml_average_top_1_precision:>17.2%}"
            f"{summary.baseline_average_top_1_precision:>18.2%}"
        )

        print(
            f"{'Average Top-3 precision':<32}"
            f"{summary.ml_average_top_3_precision:>17.2%}"
            f"{summary.baseline_average_top_3_precision:>18.2%}"
        )

        print(
            f"{'Average Top-5 precision':<32}"
            f"{summary.ml_average_top_5_precision:>17.2%}"
            f"{summary.baseline_average_top_5_precision:>18.2%}"
        )

        print(
            f"{'Top-1 hit rate':<32}"
            f"{summary.ml_top_1_hit_rate:>17.2%}"
            f"{summary.baseline_top_1_hit_rate:>18.2%}"
        )

        print(
            f"{'Average Top-3 hits':<32}"
            f"{summary.ml_average_top_3_hits:>18.4f}"
            f"{summary.baseline_average_top_3_hits:>18.4f}"
        )

        print(
            f"{'Average Top-5 hits':<32}"
            f"{summary.ml_average_top_5_hits:>18.4f}"
            f"{summary.baseline_average_top_5_hits:>18.4f}"
        )

        print(
            f"{'Average mines in Top-5':<32}"
            f"{summary.ml_average_mines_in_top_5:>18.4f}"
            f"{summary.baseline_average_mines_in_top_5:>18.4f}"
        )

        print()
        print("HEAD-TO-HEAD")
        print("-" * 70)

        print(
            f"ML better Top-5 games : "
            f"{summary.ml_better_top_5_games}"
        )

        print(
            f"Baseline better games : "
            f"{summary.baseline_better_top_5_games}"
        )

        print(
            f"Tied Top-5 games      : "
            f"{summary.tied_top_5_games}"
        )

        print(
            f"Same Top-1 prediction : "
            f"{summary.same_top_1_games}/"
            f"{summary.games_evaluated}"
        )

        print()
        print("=" * 100)
        print(
            "WALK-FORWARD COMPARISON COMPLETE"
        )
        print("=" * 100)

    finally:
        db.close()


if __name__ == "__main__":
    main()
 
