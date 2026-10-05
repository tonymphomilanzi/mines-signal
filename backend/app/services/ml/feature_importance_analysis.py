"""
Mines AI — Walk-Forward Feature Importance Analysis

Diagnostic-only analysis for the RandomForest ML model.

IMPORTANT:
- Does NOT modify Pattern Engine.
- Does NOT modify production prediction logic.
- Does NOT load or overwrite the production model.
- Trains a fresh RandomForest for each target game.
- Uses only games that occurred before the target game.
- Uses the authoritative MLFeatureBuilder.
- Uses the same model configuration as the walk-forward backtester.

The purpose is to understand which of the ML features
are driving the model's predictions.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sqlalchemy.orm import Session

from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.feature_builder import MLFeatureBuilder


# ---------------------------------------------------------------------------
# MODEL CONFIGURATION
# ---------------------------------------------------------------------------

MODEL_NAME = "mines_random_forest"
MODEL_VERSION = "1.0.0"
FEATURE_VERSION = "2.0.0"

N_ESTIMATORS = 300
MAX_DEPTH = 8
MIN_SAMPLES_SPLIT = 8
MIN_SAMPLES_LEAF = 4
CLASS_WEIGHT = "balanced"
RANDOM_STATE = 42


# ---------------------------------------------------------------------------
# DATA CLASSES
# ---------------------------------------------------------------------------

@dataclass
class FeatureImportance:
    feature_name: str
    importance: float
    percentage: float


@dataclass
class FeatureGroupImportance:
    group_name: str
    importance: float
    percentage: float


@dataclass
class GameFeatureImportance:
    game_number: int
    historical_games: int
    training_rows: int
    training_safe_rows: int
    training_mine_rows: int
    top_features: list[FeatureImportance]
    group_importances: list[FeatureGroupImportance]


@dataclass
class FeatureImportanceSummary:
    games_available: int
    games_skipped: int
    games_evaluated: int

    overall_features: list[FeatureImportance]
    overall_groups: list[FeatureGroupImportance]

    early_features: list[FeatureImportance]
    middle_features: list[FeatureImportance]
    late_features: list[FeatureImportance]

    early_groups: list[FeatureGroupImportance]
    middle_groups: list[FeatureGroupImportance]
    late_groups: list[FeatureGroupImportance]

    per_game: list[GameFeatureImportance]


# ---------------------------------------------------------------------------
# FEATURE GROUPS
# ---------------------------------------------------------------------------

def feature_group(feature_name: str) -> str:
    """
    Assign every known feature to its logical diagnostic group.

    This function ONLY affects reporting.

    It does not alter:
    - feature values
    - feature ordering
    - model training
    - prediction
    - production ML
    """

    # ------------------------------------------------------------
    # BOARD GEOMETRY / POSITION
    # ------------------------------------------------------------

    board_geometry_features = {
        "position",
        "position_normalized",

        "row",
        "row_normalized",

        "column",
        "column_normalized",

        "distance_from_center",
        "distance_from_center_normalized",

        "distance_from_top",
        "distance_from_top_normalized",

        "distance_from_bottom",
        "distance_from_bottom_normalized",
    }

    if feature_name in board_geometry_features:
        return "BOARD_GEOMETRY"

    # ------------------------------------------------------------
    # HISTORICAL
    # ------------------------------------------------------------

    historical_features = {
        "historical_games",
        "historical_safe_count",
        "historical_mine_count",
        "historical_safe_frequency",
        "historical_mine_frequency",
        "historical_balance",
    }

    if feature_name in historical_features:
        return "HISTORICAL"

    # ------------------------------------------------------------
    # RECENT 5
    # ------------------------------------------------------------

    recent_5_features = {
        "recent_5_games",
        "recent_5_safe_count",
        "recent_5_mine_count",
        "recent_5_safe_frequency",
        "recent_5_mine_frequency",
        "recent_5_balance",
    }

    if feature_name in recent_5_features:
        return "RECENT_5"

    # ------------------------------------------------------------
    # RECENT 10
    # ------------------------------------------------------------

    recent_10_features = {
        "recent_10_games",
        "recent_10_safe_count",
        "recent_10_mine_count",
        "recent_10_safe_frequency",
        "recent_10_mine_frequency",
        "recent_10_balance",
    }

    if feature_name in recent_10_features:
        return "RECENT_10"

    # ------------------------------------------------------------
    # STREAK
    # ------------------------------------------------------------

    streak_features = {
        "safe_streak",
        "mine_streak",
    }

    if feature_name in streak_features:
        return "STREAK"

    # ------------------------------------------------------------
    # GAME CONFIGURATION
    # ------------------------------------------------------------

    configuration_features = {
        "board_size",
        "mine_count",
        "total_cells",
    }

    if feature_name in configuration_features:
        return "GAME_CONFIGURATION"

    # ------------------------------------------------------------
    # UNKNOWN
    # ------------------------------------------------------------

    return "OTHER"


# ---------------------------------------------------------------------------
# ANALYZER
# ---------------------------------------------------------------------------

class FeatureImportanceAnalyzer:
    """
    Walk-forward diagnostic analyzer for RandomForest feature importance.

    Each target game receives a brand-new RandomForest trained exclusively
    on games before that target.

    Nothing is saved to disk.
    """

    def __init__(self, db: Session) -> None:
        self.db = db

        self.dataset_builder = MLDatasetBuilder(db)
        self.feature_builder = MLFeatureBuilder()

    # -----------------------------------------------------------------------
    # PUBLIC API
    # -----------------------------------------------------------------------

    def run(
        self,
        *,
        board_size: int = 5,
        mine_count: int = 3,
        min_historical_games: int = 5,
        top_n: int = 10,
    ) -> FeatureImportanceSummary:

        records = self.dataset_builder.build_feature_records(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=0,
        )

        games = self._group_games(records)

        games_available = len(games)

        evaluated: list[GameFeatureImportance] = []

        for game_index in range(len(games)):
            historical_games = games[:game_index]

            if len(historical_games) < min_historical_games:
                continue

            result = self._analyze_game(
                game_number=game_index + 1,
                historical_games=historical_games,
                top_n=top_n,
            )

            evaluated.append(result)

        games_evaluated = len(evaluated)

        games_skipped = games_available - games_evaluated

        overall_features = self._aggregate_features(
            evaluated,
            attribute="top_features",
        )

        overall_groups = self._aggregate_groups(
            evaluated,
        )

        early, middle, late = self._split_segments(
            evaluated,
        )

        early_features = self._aggregate_features(
            early,
            attribute="top_features",
        )

        middle_features = self._aggregate_features(
            middle,
            attribute="top_features",
        )

        late_features = self._aggregate_features(
            late,
            attribute="top_features",
        )

        early_groups = self._aggregate_groups(early)
        middle_groups = self._aggregate_groups(middle)
        late_groups = self._aggregate_groups(late)

        return FeatureImportanceSummary(
            games_available=games_available,
            games_skipped=games_skipped,
            games_evaluated=games_evaluated,
            overall_features=overall_features,
            overall_groups=overall_groups,
            early_features=early_features,
            middle_features=middle_features,
            late_features=late_features,
            early_groups=early_groups,
            middle_groups=middle_groups,
            late_groups=late_groups,
            per_game=evaluated,
        )

    # -----------------------------------------------------------------------
    # GAME GROUPING
    # -----------------------------------------------------------------------

    def _group_games(
        self,
        records: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for record in records:
            grouped[str(record["result_id"])].append(record)

        games = list(grouped.values())

        def game_sort_key(
            game: list[dict[str, Any]],
        ) -> tuple[datetime, datetime]:

            recorded_values = [
                record["recorded_at"]
                for record in game
                if record.get("recorded_at") is not None
            ]

            generated_values = [
                record["generated_at"]
                for record in game
                if record.get("generated_at") is not None
            ]

            recorded_at = (
                min(recorded_values)
                if recorded_values
                else datetime.min
            )

            generated_at = (
                min(generated_values)
                if generated_values
                else datetime.min
            )

            return recorded_at, generated_at

        games.sort(key=game_sort_key)

        return games

    # -----------------------------------------------------------------------
    # SINGLE GAME ANALYSIS
    # -----------------------------------------------------------------------

    def _analyze_game(
        self,
        *,
        game_number: int,
        historical_games: list[list[dict[str, Any]]],
        top_n: int,
    ) -> GameFeatureImportance:

        training_records = [
            record
            for game in historical_games
            for record in game
        ]

        X, y, feature_names = self._build_training_matrix(
            training_records,
        )

        model = self._train_model(X, y)

        importances = np.asarray(
            model.feature_importances_,
            dtype=float,
        )

        if len(importances) != len(feature_names):
            raise RuntimeError(
                "Feature importance length does not match "
                "feature-name length."
            )

        features = [
            FeatureImportance(
                feature_name=feature_name,
                importance=float(importance),
                percentage=float(importance * 100.0),
            )
            for feature_name, importance in zip(
                feature_names,
                importances,
            )
        ]

        features.sort(
            key=lambda item: (
                -item.importance,
                item.feature_name,
            )
        )

        groups = self._build_group_importances(
            features,
        )

        return GameFeatureImportance(
            game_number=game_number,
            historical_games=len(historical_games),
            training_rows=len(training_records),
            training_safe_rows=int(np.sum(y == 1)),
            training_mine_rows=int(np.sum(y == 0)),
            top_features=features[:top_n],
            group_importances=groups,
        )

    # -----------------------------------------------------------------------
    # TRAINING MATRIX
    # -----------------------------------------------------------------------

    def _build_training_matrix(
        self,
        records: list[dict[str, Any]],
    ) -> tuple[np.ndarray, np.ndarray, list[str]]:

        if not records:
            raise ValueError(
                "Cannot build training matrix from empty records."
            )

        feature_rows: list[list[float]] = []
        labels: list[int] = []

        for record in records:
            row = self.feature_builder.build_feature_row(
                record,
            )

            feature_rows.append(row)

            labels.append(
                int(record["label"]),
            )

        X = np.asarray(
            feature_rows,
            dtype=float,
        )

        y = np.asarray(
            labels,
            dtype=int,
        )

        feature_names = list(
            self.feature_builder.feature_names(),
        )

        expected_count = len(feature_names)

        if X.shape[1] != expected_count:
            raise RuntimeError(
                "Feature matrix width does not match "
                f"feature count: {X.shape[1]} != {expected_count}"
            )

        return X, y, feature_names

    # -----------------------------------------------------------------------
    # MODEL
    # -----------------------------------------------------------------------

    def _train_model(
        self,
        X: np.ndarray,
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

        model.fit(X, y)

        return model

    # -----------------------------------------------------------------------
    # GROUP IMPORTANCE
    # -----------------------------------------------------------------------

    def _build_group_importances(
        self,
        features: list[FeatureImportance],
    ) -> list[FeatureGroupImportance]:

        grouped: dict[str, float] = defaultdict(float)

        total = sum(
            feature.importance
            for feature in features
        )

        for feature in features:
            grouped[
                feature_group(feature.feature_name)
            ] += feature.importance

        result = [
            FeatureGroupImportance(
                group_name=group_name,
                importance=importance,
                percentage=(
                    (importance / total) * 100.0
                    if total > 0
                    else 0.0
                ),
            )
            for group_name, importance in grouped.items()
        ]

        result.sort(
            key=lambda item: (
                -item.importance,
                item.group_name,
            )
        )

        return result

    # -----------------------------------------------------------------------
    # AGGREGATION
    # -----------------------------------------------------------------------

    def _aggregate_features(
        self,
        games: list[GameFeatureImportance],
        *,
        attribute: str,
    ) -> list[FeatureImportance]:

        totals: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)

        for game in games:
            features = getattr(game, attribute)

            for feature in features:
                totals[feature.feature_name] += feature.importance
                counts[feature.feature_name] += 1

        result: list[FeatureImportance] = []

        for feature_name, total in totals.items():
            count = counts[feature_name]

            average = total / count

            result.append(
                FeatureImportance(
                    feature_name=feature_name,
                    importance=average,
                    percentage=average * 100.0,
                )
            )

        result.sort(
            key=lambda item: (
                -item.importance,
                item.feature_name,
            )
        )

        return result

    def _aggregate_groups(
        self,
        games: list[GameFeatureImportance],
    ) -> list[FeatureGroupImportance]:

        totals: dict[str, float] = defaultdict(float)
        counts: dict[str, int] = defaultdict(int)

        for game in games:
            for group in game.group_importances:
                totals[group.group_name] += group.importance
                counts[group.group_name] += 1

        result: list[FeatureGroupImportance] = []

        total_average = 0.0

        for group_name, total in totals.items():
            count = counts[group_name]

            average = total / count

            total_average += average

            result.append(
                FeatureGroupImportance(
                    group_name=group_name,
                    importance=average,
                    percentage=0.0,
                )
            )

        if total_average > 0:
            result = [
                FeatureGroupImportance(
                    group_name=item.group_name,
                    importance=item.importance,
                    percentage=(
                        item.importance
                        / total_average
                        * 100.0
                    ),
                )
                for item in result
            ]

        result.sort(
            key=lambda item: (
                -item.importance,
                item.group_name,
            )
        )

        return result

    # -----------------------------------------------------------------------
    # SEGMENTS
    # -----------------------------------------------------------------------

    def _split_segments(
        self,
        games: list[GameFeatureImportance],
    ) -> tuple[
        list[GameFeatureImportance],
        list[GameFeatureImportance],
        list[GameFeatureImportance],
    ]:

        count = len(games)

        if count == 0:
            return [], [], []

        segment_size = count // 3

        if segment_size == 0:
            return games, [], []

        early_end = segment_size
        middle_end = segment_size * 2

        early = games[:early_end]
        middle = games[early_end:middle_end]
        late = games[middle_end:]

        return early, middle, late
 
