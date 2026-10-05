from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from itertools import product
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sqlalchemy.orm import Session

from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.feature_builder import MLFeatureBuilder


# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_NAME = "mines_random_forest"
MODEL_VERSION = "1.0.0"
FEATURE_VERSION = "2.0.0"

N_ESTIMATORS = 300
MAX_DEPTH = 8
MIN_SAMPLES_SPLIT = 8
MIN_SAMPLES_LEAF = 4
CLASS_WEIGHT = "balanced"
RANDOM_STATE = 42


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class PositionAnalysis:
    position: int

    games_evaluated: int

    historical_safe_count: int
    historical_mine_count: int
    historical_safe_rate: float

    ml_selected_count: int
    baseline_selected_count: int

    ml_selection_rate: float
    baseline_selection_rate: float

    ml_only_count: int
    baseline_only_count: int

    ml_selected_mines: int
    baseline_selected_mines: int

    ml_selected_mine_rate: float
    baseline_selected_mine_rate: float


@dataclass
class SegmentAnalysis:
    name: str

    first_game: int
    last_game: int

    games_evaluated: int

    ml_top_1_hit_rate: float
    baseline_top_1_hit_rate: float

    ml_average_top_3_hits: float
    baseline_average_top_3_hits: float

    ml_average_top_5_hits: float
    baseline_average_top_5_hits: float

    ml_average_mines_top_5: float
    baseline_average_mines_top_5: float

    ml_top_5_precision: float
    baseline_top_5_precision: float

    top_5_difference: float


@dataclass
class GameAnalysis:
    game_number: int
    result_id: str
    signal_id: str

    historical_games_used: int

    ml_positions: list[int]
    baseline_positions: list[int]

    actual_safe_positions: list[int]
    actual_mine_positions: list[int]

    ml_top_1_hit: bool
    baseline_top_1_hit: bool

    ml_top_3_hits: int
    baseline_top_3_hits: int

    ml_top_5_hits: int
    baseline_top_5_hits: int

    ml_mines_in_top_5: int
    baseline_mines_in_top_5: int

    ml_top_5_precision: float
    baseline_top_5_precision: float

    ml_only_positions: list[int]
    baseline_only_positions: list[int]

    ml_avoided_baseline_mines: list[int]

    winner: str

    generated_at: datetime | None = None
    recorded_at: datetime | None = None


@dataclass
class WalkForwardAnalysisSummary:
    board_size: int
    mine_count: int
    total_cells: int

    min_historical_games: int
    top_n: int

    games_available: int
    games_skipped: int
    games_evaluated: int

    ml_top_1_hit_rate: float
    baseline_top_1_hit_rate: float

    ml_average_top_3_hits: float
    baseline_average_top_3_hits: float

    ml_average_top_5_hits: float
    baseline_average_top_5_hits: float

    ml_average_top_5_precision: float
    baseline_average_top_5_precision: float

    ml_average_mines_top_5: float
    baseline_average_mines_top_5: float

    ml_better_games: int
    baseline_better_games: int
    tied_games: int

    exact_sign_test_p_value: float
    permutation_p_value_top_5: float

    segments: list[SegmentAnalysis]
    positions: list[PositionAnalysis]
    games: list[GameAnalysis]


# ============================================================
# ANALYZER
# ============================================================


class WalkForwardAnalyzer:
    """
    Leakage-safe statistical analysis of ML versus the
    historical positional-frequency baseline.

    For every target game:

        1. Only games before the target are used.
        2. A fresh RandomForest is trained on those games.
        3. ML ranks all board positions.
        4. The baseline ranks positions using historical
           safe frequency.
        5. Both models select Top-N positions.
        6. The target game's labels are used only afterward
           to score both methods.

    This class does NOT:
        - modify Pattern Engine
        - modify the production ML model
        - save a model
        - change production prediction behavior
    """

    def __init__(self, db: Session) -> None:
        self.db = db

        self.dataset_builder = MLDatasetBuilder(db)
        self.feature_builder = MLFeatureBuilder()

    # ========================================================
    # PUBLIC API
    # ========================================================

    def run(
        self,
        *,
        board_size: int = 5,
        mine_count: int = 3,
        min_historical_games: int = 5,
        top_n: int = 5,
    ) -> WalkForwardAnalysisSummary:

        self._validate_arguments(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=min_historical_games,
            top_n=top_n,
        )

        total_cells = board_size * board_size
        top_n = min(top_n, total_cells)

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

        games.sort(key=self._game_sort_key)

        games_available = len(games)
        games_skipped = min(
            min_historical_games,
            games_available,
        )

        results: list[GameAnalysis] = []

        for game_index, target_game in enumerate(games):

            if game_index < min_historical_games:
                continue

            historical_games = games[:game_index]

            self._validate_complete_game(
                target_game,
                board_size=board_size,
                mine_count=mine_count,
            )

            historical_records = [
                record
                for historical_game in historical_games
                for record in historical_game
            ]

            if not historical_records:
                continue

            model, X_train, y_train = self._train_model(
                historical_records=historical_records,
                board_size=board_size,
                mine_count=mine_count,
            )

            prediction_records = self._build_prediction_records(
                board_size=board_size,
                mine_count=mine_count,
                historical_records=historical_records,
            )

            X_predict = np.asarray(
                [
                    self.feature_builder.build_feature_row(record)
                    for record in prediction_records
                ],
                dtype=float,
            )

            safe_probabilities = self._safe_probabilities(
                model,
                X_predict,
            )

            ml_positions = self._rank_ml_positions(
                safe_probabilities,
                top_n=top_n,
            )

            baseline_positions = self._rank_baseline_positions(
                historical_records=historical_records,
                board_size=board_size,
                top_n=top_n,
            )

            result = self._evaluate_game(
                game_number=game_index + 1,
                target_game=target_game,
                historical_games_used=len(historical_games),
                ml_positions=ml_positions,
                baseline_positions=baseline_positions,
                top_n=top_n,
            )

            results.append(result)

        if not results:
            raise ValueError(
                "No games were eligible for analysis. "
                "Try reducing min_historical_games."
            )

        return self._build_summary(
            results=results,
            all_games=games,
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,
            min_historical_games=min_historical_games,
            top_n=top_n,
            games_available=games_available,
            games_skipped=games_skipped,
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_arguments(
        *,
        board_size: int,
        mine_count: int,
        min_historical_games: int,
        top_n: int,
    ) -> None:

        if board_size <= 0:
            raise ValueError(
                "board_size must be greater than zero."
            )

        total_cells = board_size * board_size

        if mine_count <= 0:
            raise ValueError(
                "mine_count must be greater than zero."
            )

        if mine_count >= total_cells:
            raise ValueError(
                "mine_count must be smaller than total cells."
            )

        if min_historical_games < 0:
            raise ValueError(
                "min_historical_games cannot be negative."
            )

        if top_n <= 0:
            raise ValueError(
                "top_n must be greater than zero."
            )

    # ========================================================
    # GROUP GAMES
    # ========================================================

    @staticmethod
    def _group_games(
        records: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:

        grouped: dict[str, list[dict[str, Any]]] = {}

        for record in records:
            result_id = str(record["result_id"])

            grouped.setdefault(
                result_id,
                [],
            ).append(record)

        return list(grouped.values())

    # ========================================================
    # GAME SORTING
    # ========================================================

    @staticmethod
    def _game_sort_key(
        game_records: list[dict[str, Any]],
    ) -> tuple[Any, Any, str]:

        first = game_records[0]

        return (
            first.get("recorded_at"),
            first.get("generated_at"),
            str(first.get("result_id", "")),
        )

    # ========================================================
    # GAME VALIDATION
    # ========================================================

    @staticmethod
    def _validate_complete_game(
        game_records: list[dict[str, Any]],
        *,
        board_size: int,
        mine_count: int,
    ) -> None:

        total_cells = board_size * board_size

        if len(game_records) != total_cells:
            raise ValueError(
                "Incomplete historical game detected. "
                f"Expected {total_cells} records, "
                f"got {len(game_records)}."
            )

        positions = sorted(
            int(record["position"])
            for record in game_records
        )

        expected_positions = list(
            range(1, total_cells + 1)
        )

        if positions != expected_positions:
            raise ValueError(
                "Historical game contains invalid "
                "or duplicate positions."
            )

        labels = [
            int(record["label"])
            for record in game_records
        ]

        mine_count_actual = labels.count(0)

        if mine_count_actual != mine_count:
            raise ValueError(
                "Historical game has unexpected mine count. "
                f"Expected {mine_count}, "
                f"got {mine_count_actual}."
            )

    # ========================================================
    # TRAIN MODEL
    # ========================================================

    def _train_model(
        self,
        *,
        historical_records: list[dict[str, Any]],
        board_size: int,
        mine_count: int,
    ) -> tuple[
        RandomForestClassifier,
        np.ndarray,
        np.ndarray,
    ]:

        X = np.asarray(
            [
                self.feature_builder.build_feature_row(record)
                for record in historical_records
            ],
            dtype=float,
        )

        y = np.asarray(
            [
                int(record["label"])
                for record in historical_records
            ],
            dtype=int,
        )

        expected_features = len(
            self.feature_builder.feature_names()
        )

        if X.shape[1] != expected_features:
            raise RuntimeError(
                "Unexpected training feature count. "
                f"Expected {expected_features}, "
                f"got {X.shape[1]}."
            )

        if len(np.unique(y)) < 2:
            raise ValueError(
                "Training history contains only one class. "
                "Cannot train RandomForest."
            )

        model = RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            max_depth=MAX_DEPTH,
            min_samples_split=MIN_SAMPLES_SPLIT,
            min_samples_leaf=MIN_SAMPLES_LEAF,
            class_weight=CLASS_WEIGHT,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

        model.fit(X, y)

        return model, X, y

    # ========================================================
    # PREDICTION RECORDS
    # ========================================================

    def _build_prediction_records(
        self,
        *,
        board_size: int,
        mine_count: int,
        historical_records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        total_cells = board_size * board_size

        records: list[dict[str, Any]] = []

        for position in range(1, total_cells + 1):

            position_records = [
                record
                for record in historical_records
                if (
                    int(record["board_size"]) == board_size
                    and int(record["mine_count"]) == mine_count
                    and int(record["position"]) == position
                )
            ]

            position_records.sort(
                key=lambda record: (
                    record["generated_at"],
                    record["recorded_at"],
                    str(record["result_id"]),
                )
            )

            labels = [
                int(record["label"])
                for record in position_records
            ]

            historical_games = len(labels)

            historical_safe_count = sum(
                label == 1
                for label in labels
            )

            historical_mine_count = sum(
                label == 0
                for label in labels
            )

            recent_5 = labels[-5:]
            recent_10 = labels[-10:]

            row, column = divmod(
                position - 1,
                board_size,
            )

            records.append(
                {
                    "signal_id": "",
                    "result_id": "prediction",

                    "board_size": board_size,
                    "mine_count": mine_count,
                    "total_cells": total_cells,

                    "position": position,
                    "row": row,
                    "column": column,

                    "historical_games": historical_games,

                    "historical_safe_count": (
                        historical_safe_count
                    ),

                    "historical_mine_count": (
                        historical_mine_count
                    ),

                    "recent_5_games": len(recent_5),

                    "recent_5_safe_count": sum(
                        label == 1
                        for label in recent_5
                    ),

                    "recent_5_mine_count": sum(
                        label == 0
                        for label in recent_5
                    ),

                    "recent_10_games": len(recent_10),

                    "recent_10_safe_count": sum(
                        label == 1
                        for label in recent_10
                    ),

                    "recent_10_mine_count": sum(
                        label == 0
                        for label in recent_10
                    ),

                    "safe_streak": self._safe_streak(
                        labels
                    ),

                    "mine_streak": self._mine_streak(
                        labels
                    ),

                    # Required by the common record structure.
                    # It is NOT used by MLFeatureBuilder.
                    "label": 0,

                    "generated_at": (
                        self._latest_datetime(
                            position_records
                        )
                    ),

                    "recorded_at": (
                        self._latest_datetime(
                            position_records
                        )
                    ),
                }
            )

        return records

    # ========================================================
    # STREAKS
    # ========================================================

    @staticmethod
    def _safe_streak(
        labels: list[int],
    ) -> int:

        streak = 0

        for label in reversed(labels):
            if label != 1:
                break

            streak += 1

        return streak

    @staticmethod
    def _mine_streak(
        labels: list[int],
    ) -> int:

        streak = 0

        for label in reversed(labels):
            if label != 0:
                break

            streak += 1

        return streak

    @staticmethod
    def _latest_datetime(
        records: list[dict[str, Any]],
    ) -> datetime | None:

        values: list[datetime] = []

        for record in records:
            for key in (
                "recorded_at",
                "generated_at",
            ):
                value = record.get(key)

                if isinstance(value, datetime):
                    values.append(value)

        if not values:
            return None

        return max(values)

    # ========================================================
    # SAFE PROBABILITIES
    # ========================================================

    @staticmethod
    def _safe_probabilities(
        model: RandomForestClassifier,
        X: np.ndarray,
    ) -> np.ndarray:

        probabilities = model.predict_proba(X)

        classes = list(model.classes_)

        if 1 not in classes:
            return np.zeros(
                len(X),
                dtype=float,
            )

        safe_index = classes.index(1)

        return probabilities[:, safe_index]

    # ========================================================
    # ML RANKING
    # ========================================================

    @staticmethod
    def _rank_ml_positions(
        safe_probabilities: np.ndarray,
        *,
        top_n: int,
    ) -> list[int]:

        ranked_indices = sorted(
            range(len(safe_probabilities)),
            key=lambda index: (
                -float(safe_probabilities[index]),
                index + 1,
            ),
        )

        return [
            index + 1
            for index in ranked_indices[:top_n]
        ]

    # ========================================================
    # BASELINE RANKING
    # ========================================================

    @staticmethod
    def _rank_baseline_positions(
        *,
        historical_records: list[dict[str, Any]],
        board_size: int,
        top_n: int,
    ) -> list[int]:

        total_cells = board_size * board_size

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

        for record in historical_records:

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

        ranked_positions = sorted(
            stats.keys(),
            key=lambda position: (
                -(
                    stats[position]["safe"]
                    / max(
                        stats[position]["safe"]
                        + stats[position]["mine"],
                        1,
                    )
                ),
                -stats[position]["safe"],
                stats[position]["mine"],
                position,
            ),
        )

        return ranked_positions[:top_n]

    # ========================================================
    # GAME EVALUATION
    # ========================================================

    @staticmethod
    def _evaluate_game(
        *,
        game_number: int,
        target_game: list[dict[str, Any]],
        historical_games_used: int,
        ml_positions: list[int],
        baseline_positions: list[int],
        top_n: int,
    ) -> GameAnalysis:

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

        actual_safe_set = set(actual_safe)
        actual_mine_set = set(actual_mines)

        ml_set = set(ml_positions)
        baseline_set = set(baseline_positions)

        ml_top_1 = (
            bool(ml_positions)
            and ml_positions[0] in actual_safe_set
        )

        baseline_top_1 = (
            bool(baseline_positions)
            and baseline_positions[0] in actual_safe_set
        )

        ml_top_3 = sum(
            position in actual_safe_set
            for position in ml_positions[:3]
        )

        baseline_top_3 = sum(
            position in actual_safe_set
            for position in baseline_positions[:3]
        )

        ml_top_5 = sum(
            position in actual_safe_set
            for position in ml_positions[:5]
        )

        baseline_top_5 = sum(
            position in actual_safe_set
            for position in baseline_positions[:5]
        )

        ml_mines = sum(
            position in actual_mine_set
            for position in ml_positions[:5]
        )

        baseline_mines = sum(
            position in actual_mine_set
            for position in baseline_positions[:5]
        )

        effective_top_n = min(
            top_n,
            5,
        )

        ml_precision = (
            ml_top_5 / effective_top_n
            if effective_top_n > 0
            else 0.0
        )

        baseline_precision = (
            baseline_top_5 / effective_top_n
            if effective_top_n > 0
            else 0.0
        )

        ml_only = sorted(
            ml_set - baseline_set
        )

        baseline_only = sorted(
            baseline_set - ml_set
        )

        ml_avoided_baseline_mines = sorted(
            position
            for position in (
                baseline_set - ml_set
            )
            if position in actual_mine_set
        )

        if ml_top_5 > baseline_top_5:
            winner = "ML"
        elif baseline_top_5 > ml_top_5:
            winner = "BASELINE"
        else:
            winner = "TIE"

        first = target_game[0]

        return GameAnalysis(
            game_number=game_number,

            result_id=str(
                first["result_id"]
            ),

            signal_id=str(
                first["signal_id"]
            ),

            historical_games_used=(
                historical_games_used
            ),

            ml_positions=list(
                ml_positions
            ),

            baseline_positions=list(
                baseline_positions
            ),

            actual_safe_positions=(
                actual_safe
            ),

            actual_mine_positions=(
                actual_mines
            ),

            ml_top_1_hit=ml_top_1,
            baseline_top_1_hit=baseline_top_1,

            ml_top_3_hits=ml_top_3,
            baseline_top_3_hits=baseline_top_3,

            ml_top_5_hits=ml_top_5,
            baseline_top_5_hits=baseline_top_5,

            ml_mines_in_top_5=ml_mines,
            baseline_mines_in_top_5=baseline_mines,

            ml_top_5_precision=ml_precision,
            baseline_top_5_precision=baseline_precision,

            ml_only_positions=ml_only,
            baseline_only_positions=baseline_only,

            ml_avoided_baseline_mines=(
                ml_avoided_baseline_mines
            ),

            winner=winner,

            generated_at=first.get(
                "generated_at"
            ),

            recorded_at=first.get(
                "recorded_at"
            ),
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    def _build_summary(
        self,
        *,
        results: list[GameAnalysis],
        all_games: list[list[dict[str, Any]]],
        board_size: int,
        mine_count: int,
        total_cells: int,
        min_historical_games: int,
        top_n: int,
        games_available: int,
        games_skipped: int,
    ) -> WalkForwardAnalysisSummary:

        ml_top_1_rate = self._mean(
            [
                float(result.ml_top_1_hit)
                for result in results
            ]
        )

        baseline_top_1_rate = self._mean(
            [
                float(result.baseline_top_1_hit)
                for result in results
            ]
        )

        ml_top_3 = self._mean(
            [
                result.ml_top_3_hits
                for result in results
            ]
        )

        baseline_top_3 = self._mean(
            [
                result.baseline_top_3_hits
                for result in results
            ]
        )

        ml_top_5 = self._mean(
            [
                result.ml_top_5_hits
                for result in results
            ]
        )

        baseline_top_5 = self._mean(
            [
                result.baseline_top_5_hits
                for result in results
            ]
        )

        ml_precision = self._mean(
            [
                result.ml_top_5_precision
                for result in results
            ]
        )

        baseline_precision = self._mean(
            [
                result.baseline_top_5_precision
                for result in results
            ]
        )

        ml_mines = self._mean(
            [
                result.ml_mines_in_top_5
                for result in results
            ]
        )

        baseline_mines = self._mean(
            [
                result.baseline_mines_in_top_5
                for result in results
            ]
        )

        ml_better = sum(
            result.winner == "ML"
            for result in results
        )

        baseline_better = sum(
            result.winner == "BASELINE"
            for result in results
        )

        ties = sum(
            result.winner == "TIE"
            for result in results
        )

        differences = [
            result.ml_top_5_hits
            - result.baseline_top_5_hits
            for result in results
        ]

        exact_sign_p = (
            self._exact_sign_test_p_value(
                differences
            )
        )

        permutation_p = (
            self._paired_permutation_p_value(
                differences
            )
        )

        segments = self._build_segments(
            results
        )

        positions = self._build_position_analysis(
            results=results,
            all_games=all_games,
            board_size=board_size,
            mine_count=mine_count,
        )

        return WalkForwardAnalysisSummary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,

            min_historical_games=(
                min_historical_games
            ),

            top_n=top_n,

            games_available=games_available,
            games_skipped=games_skipped,
            games_evaluated=len(results),

            ml_top_1_hit_rate=ml_top_1_rate,
            baseline_top_1_hit_rate=(
                baseline_top_1_rate
            ),

            ml_average_top_3_hits=ml_top_3,
            baseline_average_top_3_hits=(
                baseline_top_3
            ),

            ml_average_top_5_hits=ml_top_5,
            baseline_average_top_5_hits=(
                baseline_top_5
            ),

            ml_average_top_5_precision=(
                ml_precision
            ),

            baseline_average_top_5_precision=(
                baseline_precision
            ),

            ml_average_mines_top_5=ml_mines,
            baseline_average_mines_top_5=(
                baseline_mines
            ),

            ml_better_games=ml_better,
            baseline_better_games=(
                baseline_better
            ),
            tied_games=ties,

            exact_sign_test_p_value=(
                exact_sign_p
            ),

            permutation_p_value_top_5=(
                permutation_p
            ),

            segments=segments,
            positions=positions,
            games=results,
        )

    # ========================================================
    # SEGMENT ANALYSIS
    # ========================================================

    def _build_segments(
        self,
        results: list[GameAnalysis],
    ) -> list[SegmentAnalysis]:

        if not results:
            return []

        total = len(results)

        segment_size = max(
            1,
            int(np.ceil(total / 3)),
        )

        raw_segments = [
            (
                "EARLY",
                results[
                    :segment_size
                ],
            ),
            (
                "MIDDLE",
                results[
                    segment_size:
                    segment_size * 2
                ],
            ),
            (
                "LATE",
                results[
                    segment_size * 2:
                ],
            ),
        ]

        segments: list[SegmentAnalysis] = []

        for name, segment_results in raw_segments:

            if not segment_results:
                continue

            ml_top_1 = self._mean(
                [
                    float(result.ml_top_1_hit)
                    for result in segment_results
                ]
            )

            baseline_top_1 = self._mean(
                [
                    float(
                        result.baseline_top_1_hit
                    )
                    for result in segment_results
                ]
            )

            ml_top_3 = self._mean(
                [
                    result.ml_top_3_hits
                    for result in segment_results
                ]
            )

            baseline_top_3 = self._mean(
                [
                    result.baseline_top_3_hits
                    for result in segment_results
                ]
            )

            ml_top_5 = self._mean(
                [
                    result.ml_top_5_hits
                    for result in segment_results
                ]
            )

            baseline_top_5 = self._mean(
                [
                    result.baseline_top_5_hits
                    for result in segment_results
                ]
            )

            ml_mines = self._mean(
                [
                    result.ml_mines_in_top_5
                    for result in segment_results
                ]
            )

            baseline_mines = self._mean(
                [
                    result.baseline_mines_in_top_5
                    for result in segment_results
                ]
            )

            ml_precision = self._mean(
                [
                    result.ml_top_5_precision
                    for result in segment_results
                ]
            )

            baseline_precision = self._mean(
                [
                    result.baseline_top_5_precision
                    for result in segment_results
                ]
            )

            segments.append(
                SegmentAnalysis(
                    name=name,

                    first_game=(
                        segment_results[0]
                        .game_number
                    ),

                    last_game=(
                        segment_results[-1]
                        .game_number
                    ),

                    games_evaluated=len(
                        segment_results
                    ),

                    ml_top_1_hit_rate=ml_top_1,
                    baseline_top_1_hit_rate=(
                        baseline_top_1
                    ),

                    ml_average_top_3_hits=ml_top_3,
                    baseline_average_top_3_hits=(
                        baseline_top_3
                    ),

                    ml_average_top_5_hits=ml_top_5,
                    baseline_average_top_5_hits=(
                        baseline_top_5
                    ),

                    ml_average_mines_top_5=(
                        ml_mines
                    ),

                    baseline_average_mines_top_5=(
                        baseline_mines
                    ),

                    ml_top_5_precision=(
                        ml_precision
                    ),

                    baseline_top_5_precision=(
                        baseline_precision
                    ),

                    top_5_difference=(
                        ml_top_5
                        - baseline_top_5
                    ),
                )
            )

        return segments

    # ========================================================
    # POSITION ANALYSIS
    # ========================================================

    def _build_position_analysis(
        self,
        *,
        results: list[GameAnalysis],
        all_games: list[list[dict[str, Any]]],
        board_size: int,
        mine_count: int,
    ) -> list[PositionAnalysis]:

        total_cells = board_size * board_size

        selected_games = [
            result
            for result in results
        ]

        positions: list[PositionAnalysis] = []

        for position in range(
            1,
            total_cells + 1,
        ):

            historical_safe = 0
            historical_mine = 0

            for game in all_games:

                matching = [
                    record
                    for record in game
                    if int(
                        record["position"]
                    ) == position
                ]

                if not matching:
                    continue

                label = int(
                    matching[0]["label"]
                )

                if label == 1:
                    historical_safe += 1
                else:
                    historical_mine += 1

            evaluated_games = len(
                selected_games
            )

            ml_selected = sum(
                position in result.ml_positions
                for result in selected_games
            )

            baseline_selected = sum(
                position
                in result.baseline_positions
                for result in selected_games
            )

            ml_only = sum(
                position
                in result.ml_only_positions
                for result in selected_games
            )

            baseline_only = sum(
                position
                in result.baseline_only_positions
                for result in selected_games
            )

            ml_mines = sum(
                position
                in result.actual_mine_positions
                and position
                in result.ml_positions[:5]
                for result in selected_games
            )

            baseline_mines = sum(
                position
                in result.actual_mine_positions
                and position
                in result.baseline_positions[:5]
                for result in selected_games
            )

            historical_games = (
                historical_safe
                + historical_mine
            )

            historical_safe_rate = (
                historical_safe
                / historical_games
                if historical_games > 0
                else 0.0
            )

            ml_selection_rate = (
                ml_selected
                / evaluated_games
                if evaluated_games > 0
                else 0.0
            )

            baseline_selection_rate = (
                baseline_selected
                / evaluated_games
                if evaluated_games > 0
                else 0.0
            )

            ml_mine_rate = (
                ml_mines
                / ml_selected
                if ml_selected > 0
                else 0.0
            )

            baseline_mine_rate = (
                baseline_mines
                / baseline_selected
                if baseline_selected > 0
                else 0.0
            )

            positions.append(
                PositionAnalysis(
                    position=position,

                    games_evaluated=(
                        evaluated_games
                    ),

                    historical_safe_count=(
                        historical_safe
                    ),

                    historical_mine_count=(
                        historical_mine
                    ),

                    historical_safe_rate=(
                        historical_safe_rate
                    ),

                    ml_selected_count=(
                        ml_selected
                    ),

                    baseline_selected_count=(
                        baseline_selected
                    ),

                    ml_selection_rate=(
                        ml_selection_rate
                    ),

                    baseline_selection_rate=(
                        baseline_selection_rate
                    ),

                    ml_only_count=(
                        ml_only
                    ),

                    baseline_only_count=(
                        baseline_only
                    ),

                    ml_selected_mines=(
                        ml_mines
                    ),

                    baseline_selected_mines=(
                        baseline_mines
                    ),

                    ml_selected_mine_rate=(
                        ml_mine_rate
                    ),

                    baseline_selected_mine_rate=(
                        baseline_mine_rate
                    ),
                )
            )

        return positions

    # ========================================================
    # STATISTICS
    # ========================================================

    @staticmethod
    def _mean(
        values: list[float | int],
    ) -> float:

        if not values:
            return 0.0

        return float(
            sum(values) / len(values)
        )

    @staticmethod
    def _exact_sign_test_p_value(
        differences: list[int],
    ) -> float:

        non_zero = [
            difference
            for difference in differences
            if difference != 0
        ]

        n = len(non_zero)

        if n == 0:
            return 1.0

        positives = sum(
            difference > 0
            for difference in non_zero
        )

        negatives = n - positives

        smaller = min(
            positives,
            negatives,
        )

        probability = (
            0.5 ** n
        )

        cumulative = 0.0

        for k in range(
            0,
            smaller + 1,
        ):
            cumulative += (
                _combination(n, k)
                * probability
            )

        return min(
            1.0,
            2.0 * cumulative,
        )

    @staticmethod
    def _paired_permutation_p_value(
        differences: list[int],
    ) -> float:

        non_zero = [
            float(difference)
            for difference in differences
            if difference != 0
        ]

        if not non_zero:
            return 1.0

        observed = abs(
            sum(non_zero)
        )

        n = len(non_zero)

        if n > 20:
            # Exact enumeration becomes unnecessarily large.
            # Deterministic Monte Carlo fallback.
            rng = np.random.default_rng(
                RANDOM_STATE
            )

            iterations = 100_000
            exceed = 0

            values = np.asarray(
                non_zero,
                dtype=float,
            )

            for _ in range(iterations):
                signs = rng.choice(
                    [-1.0, 1.0],
                    size=n,
                )

                shuffled = (
                    values * signs
                )

                if abs(
                    shuffled.sum()
                ) >= observed:
                    exceed += 1

            return (
                exceed + 1
            ) / (
                iterations + 1
            )

        exceed = 0
        total = 0

        for signs in product(
            [-1.0, 1.0],
            repeat=n,
        ):

            total += 1

            randomized = [
                value * sign
                for value, sign in zip(
                    non_zero,
                    signs,
                )
            ]

            if abs(
                sum(randomized)
            ) >= observed:
                exceed += 1

        return (
            exceed / total
            if total > 0
            else 1.0
        )


# ============================================================
# COMBINATION
# ============================================================


def _combination(
    n: int,
    k: int,
) -> int:

    if k < 0 or k > n:
        return 0

    if k == 0 or k == n:
        return 1

    k = min(k, n - k)

    result = 1

    for index in range(1, k + 1):
        result = (
            result
            * (n - k + index)
            // index
        )

    return result
 
