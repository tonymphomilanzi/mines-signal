from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sqlalchemy.orm import Session

from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.feature_builder import MLFeatureBuilder


# ============================================================
# FIXED WALK-FORWARD MODEL CONFIGURATION
# ============================================================
#
# IMPORTANT:
# These values intentionally match the current production
# RandomForest configuration.
#
# This evaluator does NOT tune the model.
# It only answers:
#
# "How does the current model configuration perform when
# retrained using only information available before each
# target game?"
#
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
# WALK-FORWARD GAME RESULT
# ============================================================


@dataclass
class WalkForwardGameResult:
    """
    Evaluation result for one unseen historical target game.

    The model used for this game was trained exclusively on
    games that occurred BEFORE this target game.
    """

    game_number: int

    result_id: str
    signal_id: str

    board_size: int
    mine_count: int
    total_cells: int

    historical_games_used: int

    training_rows: int
    training_safe_rows: int
    training_mine_rows: int

    actual_safe_positions: list[int]
    actual_mine_positions: list[int]

    predicted_safe_positions: list[int]

    top_1_hit: bool

    top_3_hits: int
    top_5_hits: int

    safe_precision_at_1: float
    safe_precision_at_3: float
    safe_precision_at_5: float

    mine_hits_in_top_5: int

    generated_at: datetime | None = None
    recorded_at: datetime | None = None


# ============================================================
# WALK-FORWARD SUMMARY
# ============================================================


@dataclass
class WalkForwardSummary:
    """
    Aggregate statistics from the complete walk-forward run.
    """

    board_size: int
    mine_count: int
    total_cells: int

    games_available: int
    games_evaluated: int
    games_skipped: int

    min_historical_games: int
    top_n: int

    average_top_1_precision: float
    average_top_3_precision: float
    average_top_5_precision: float

    top_1_hit_rate: float

    average_top_3_hits: float
    average_top_5_hits: float

    average_mine_hits_in_top_5: float

    model_name: str
    model_version: str
    feature_version: str

    results: list[WalkForwardGameResult]


# ============================================================
# WALK-FORWARD BACKTESTER
# ============================================================


class WalkForwardBacktester:
    """
    True chronological walk-forward RandomForest evaluator.

    For every target game:

        1. Select ONLY games before the target.
        2. Train a completely NEW RandomForest in memory.
        3. Build target features using ONLY historical games.
        4. Predict the target game.
        5. Evaluate against the target's actual result.
        6. Discard the temporary model.
        7. Continue to the next target.

    IMPORTANT:

    This class does NOT:

        - load the production model
        - save a model
        - overwrite .pkl files
        - overwrite .json metadata
        - modify Pattern Engine
        - modify live prediction services
        - modify Signal lifecycle

    Dataset labels:

        label = 1 -> SAFE
        label = 0 -> MINE
    """

    def __init__(
        self,
        db: Session,
    ) -> None:
        self.db = db

        self.dataset_builder = MLDatasetBuilder(
            db
        )

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
    ) -> WalkForwardSummary:
        """
        Run true chronological walk-forward evaluation.

        Parameters
        ----------
        board_size:
            Board width/height.

        mine_count:
            Number of mines on each board.

        min_historical_games:
            Minimum number of completed games required before
            evaluating a target game.

        top_n:
            Number of SAFE positions to predict.
        """

        self._validate_parameters(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=(
                min_historical_games
            ),
            top_n=top_n,
        )

        total_cells = (
            board_size * board_size
        )

        # ----------------------------------------------------
        # Build complete chronological dataset.
        #
        # We request min_historical_games=0 here because we
        # need ALL games available so that this evaluator can
        # construct its own walk-forward windows.
        # ----------------------------------------------------

        records = (
            self.dataset_builder.build_feature_records(
                board_size=board_size,
                mine_count=mine_count,
                min_historical_games=0,
            )
        )

        if not records:
            raise ValueError(
                "No historical ML dataset records "
                "were found."
            )

        # ----------------------------------------------------
        # Group records into complete games.
        # ----------------------------------------------------

        games = self._group_games(
            records
        )

        if not games:
            raise ValueError(
                "No historical games were found."
            )

        # ----------------------------------------------------
        # Sort games chronologically.
        # ----------------------------------------------------

        games.sort(
            key=self._game_sort_key
        )

        results: list[
            WalkForwardGameResult
        ] = []

        games_skipped = 0

        # ====================================================
        # WALK-FORWARD LOOP
        # ====================================================

        for game_index, target_game in enumerate(
            games
        ):

            # ------------------------------------------------
            # Require enough history.
            # ------------------------------------------------

            if (
                game_index
                < min_historical_games
            ):
                games_skipped += 1
                continue

            # ------------------------------------------------
            # Historical games are STRICTLY before target.
            # ------------------------------------------------

            historical_games = games[
                :game_index
            ]

            if (
                len(historical_games)
                < min_historical_games
            ):
                games_skipped += 1
                continue

            # ------------------------------------------------
            # Validate target game.
            # ------------------------------------------------

            self._validate_complete_game(
                target_game,
                board_size=board_size,
                mine_count=mine_count,
            )

            # ------------------------------------------------
            # Validate all historical games.
            # ------------------------------------------------

            for historical_game in (
                historical_games
            ):
                self._validate_complete_game(
                    historical_game,
                    board_size=board_size,
                    mine_count=mine_count,
                )

            # ------------------------------------------------
            # Train a NEW model.
            #
            # Nothing from the target game is included.
            # ------------------------------------------------

            (
                model,
                training_rows,
                training_safe_rows,
                training_mine_rows,
            ) = self._train_model(
                historical_games=(
                    historical_games
                )
            )

            # ------------------------------------------------
            # Flatten historical records.
            # ------------------------------------------------

            historical_records: list[
                dict[str, Any]
            ] = []

            for historical_game in (
                historical_games
            ):
                historical_records.extend(
                    historical_game
                )

            # ------------------------------------------------
            # Build prediction features.
            #
            # IMPORTANT:
            # Target labels are NOT included.
            # ------------------------------------------------

            prediction_records = (
                self._build_prediction_records(
                    board_size=board_size,
                    mine_count=mine_count,
                    historical_records=(
                        historical_records
                    ),
                )
            )

            # ------------------------------------------------
            # Predict target.
            # ------------------------------------------------

            predicted_positions = (
                self._predict_positions(
                    model=model,
                    prediction_records=(
                        prediction_records
                    ),
                    board_size=board_size,
                    top_n=top_n,
                )
            )

            # ------------------------------------------------
            # Evaluate target AFTER prediction.
            # ------------------------------------------------

            result = self._evaluate_game(
                game_number=game_index + 1,
                target_game=target_game,
                predicted_positions=(
                    predicted_positions
                ),
                historical_games_used=(
                    len(historical_games)
                ),
                training_rows=training_rows,
                training_safe_rows=(
                    training_safe_rows
                ),
                training_mine_rows=(
                    training_mine_rows
                ),
            )

            results.append(result)

            # ------------------------------------------------
            # The temporary model goes out of scope here.
            #
            # It is never persisted.
            # ------------------------------------------------

            del model

        if not results:
            raise ValueError(
                "No games were eligible for "
                "walk-forward evaluation. "
                "Try reducing "
                "min_historical_games."
            )

        return self._build_summary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,
            games_available=len(games),
            games_skipped=games_skipped,
            min_historical_games=(
                min_historical_games
            ),
            top_n=top_n,
            results=results,
        )

    # ========================================================
    # PARAMETER VALIDATION
    # ========================================================

    @staticmethod
    def _validate_parameters(
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

        if mine_count <= 0:
            raise ValueError(
                "mine_count must be greater than zero."
            )

        total_cells = (
            board_size * board_size
        )

        if mine_count >= total_cells:
            raise ValueError(
                "mine_count must be smaller than "
                "the total number of cells."
            )

        if min_historical_games < 1:
            raise ValueError(
                "min_historical_games must be "
                "at least 1."
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
        records: list[
            dict[str, Any]
        ],
    ) -> list[
        list[dict[str, Any]]
    ]:
        """
        Group 25 position records into games
        using result_id.
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
                    "'result_id'."
                )

            key = str(
                result_id
            )

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

    @staticmethod
    def _game_sort_key(
        game_records: list[
            dict[str, Any]
        ],
    ) -> datetime:

        if not game_records:
            return datetime.min

        first_record = (
            game_records[0]
        )

        recorded_at = (
            first_record.get(
                "recorded_at"
            )
        )

        if isinstance(
            recorded_at,
            datetime,
        ):
            return recorded_at

        generated_at = (
            first_record.get(
                "generated_at"
            )
        )

        if isinstance(
            generated_at,
            datetime,
        ):
            return generated_at

        return datetime.min

    # ========================================================
    # COMPLETE GAME VALIDATION
    # ========================================================

    @staticmethod
    def _validate_complete_game(
        game_records: list[
            dict[str, Any]
        ],
        *,
        board_size: int,
        mine_count: int,
    ) -> None:

        total_cells = (
            board_size * board_size
        )

        positions: set[int] = set()
        safe_positions: set[int] = set()
        mine_positions: set[int] = set()

        for record in game_records:

            if "position" not in record:
                raise ValueError(
                    "Dataset record is missing "
                    "'position'."
                )

            position = int(
                record["position"]
            )

            if (
                position < 1
                or position > total_cells
            ):
                raise ValueError(
                    f"Invalid board position "
                    f"{position}. Expected "
                    f"1-{total_cells}."
                )

            if position in positions:
                raise ValueError(
                    f"Duplicate board position "
                    f"{position} found."
                )

            positions.add(
                position
            )

            if "label" not in record:
                raise ValueError(
                    f"Position {position} is "
                    "missing 'label'."
                )

            label = int(
                record["label"]
            )

            if label == 1:

                safe_positions.add(
                    position
                )

            elif label == 0:

                mine_positions.add(
                    position
                )

            else:
                raise ValueError(
                    f"Invalid label {label} "
                    f"for position {position}. "
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
                expected_positions
                - positions
            )

            extra = sorted(
                positions
                - expected_positions
            )

            raise ValueError(
                "Historical game does not contain "
                "the complete board. "
                f"Missing={missing}, "
                f"Extra={extra}"
            )

        if (
            len(mine_positions)
            != mine_count
        ):
            result_id = str(
                game_records[0].get(
                    "result_id"
                )
            )

            raise ValueError(
                f"Historical game {result_id} "
                f"has {len(mine_positions)} "
                f"mines, expected {mine_count}."
            )

        expected_safe_count = (
            total_cells - mine_count
        )

        if (
            len(safe_positions)
            != expected_safe_count
        ):
            raise ValueError(
                "Historical game has "
                f"{len(safe_positions)} safe "
                "positions, expected "
                f"{expected_safe_count}."
            )

    # ========================================================
    # TRAIN MODEL
    # ========================================================

    def _train_model(
        self,
        *,
        historical_games: list[
            list[dict[str, Any]]
        ],
    ) -> tuple[
        RandomForestClassifier,
        int,
        int,
        int,
    ]:
        """
        Train one fresh RandomForest.

        Returns
        -------
        (
            model,
            training_rows,
            training_safe_rows,
            training_mine_rows,
        )

        IMPORTANT:
        Only historical games supplied by the caller are
        included in training.
        """

        training_records: list[
            dict[str, Any]
        ] = []

        for game in historical_games:
            training_records.extend(
                game
            )

        if not training_records:
            raise ValueError(
                "Cannot train model without "
                "historical records."
            )

        # ----------------------------------------------------
        # Build training feature matrix.
        # ----------------------------------------------------

        X = np.asarray(
            [
                self.feature_builder.build_feature_row(
                    record
                )
                for record in training_records
            ],
            dtype=float,
        )

        # ----------------------------------------------------
        # Build labels.
        # ----------------------------------------------------

        y = np.asarray(
            [
                int(
                    record["label"]
                )
                for record in training_records
            ],
            dtype=int,
        )

        # ----------------------------------------------------
        # Validate feature matrix.
        # ----------------------------------------------------

        expected_feature_count = len(
            self.feature_builder.feature_names()
        )

        if X.shape != (
            len(training_records),
            expected_feature_count,
        ):
            raise RuntimeError(
                "Unexpected training feature "
                f"matrix shape: {X.shape}. "
                "Expected "
                f"({len(training_records)}, "
                f"{expected_feature_count})."
            )

        # ----------------------------------------------------
        # Count classes from ACTUAL training data.
        # ----------------------------------------------------

        training_safe_rows = int(
            np.sum(
                y == 1
            )
        )

        training_mine_rows = int(
            np.sum(
                y == 0
            )
        )

        training_rows = len(
            training_records
        )

        # ----------------------------------------------------
        # Both classes are required.
        # ----------------------------------------------------

        if training_safe_rows == 0:
            raise RuntimeError(
                "Walk-forward training failed: "
                "training set contains no SAFE "
                "rows."
            )

        if training_mine_rows == 0:
            raise RuntimeError(
                "Walk-forward training failed: "
                "training set contains no MINE "
                "rows."
            )

        # ----------------------------------------------------
        # Create fresh model.
        #
        # No production model is loaded.
        # ----------------------------------------------------

        model = RandomForestClassifier(
            n_estimators=N_ESTIMATORS,
            max_depth=MAX_DEPTH,
            min_samples_split=(
                MIN_SAMPLES_SPLIT
            ),
            min_samples_leaf=(
                MIN_SAMPLES_LEAF
            ),
            class_weight=CLASS_WEIGHT,
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )

        # ----------------------------------------------------
        # Train ONLY on historical records.
        # ----------------------------------------------------

        model.fit(
            X,
            y,
        )

        return (
            model,
            training_rows,
            training_safe_rows,
            training_mine_rows,
        )

    # ========================================================
    # BUILD TARGET PREDICTION RECORDS
    # ========================================================

    def _build_prediction_records(
        self,
        *,
        board_size: int,
        mine_count: int,
        historical_records: list[
            dict[str, Any]
        ],
    ) -> list[
        dict[str, Any]
    ]:
        """
        Build one feature record per board position.

        Historical statistics are calculated exclusively from
        records supplied by the caller.

        No target-game label is used.
        """

        total_cells = (
            board_size * board_size
        )

        records: list[
            dict[str, Any]
        ] = []

        for position in range(
            1,
            total_cells + 1,
        ):

            row, column = divmod(
                position - 1,
                board_size,
            )

            position_history = [
                record
                for record in historical_records
                if int(
                    record["position"]
                ) == position
            ]

            history = (
                self._calculate_position_history(
                    position_history
                )
            )

            records.append(
                {
                    "signal_id": (
                        "walk_forward_prediction"
                    ),
                    "result_id": (
                        "walk_forward_prediction"
                    ),
                    "board_size": board_size,
                    "mine_count": mine_count,
                    "total_cells": total_cells,
                    "position": position,
                    "row": row,
                    "column": column,
                    "historical_games": (
                        history[
                            "historical_games"
                        ]
                    ),
                    "historical_safe_count": (
                        history[
                            "historical_safe_count"
                        ]
                    ),
                    "historical_mine_count": (
                        history[
                            "historical_mine_count"
                        ]
                    ),
                    "recent_5_games": (
                        history[
                            "recent_5_games"
                        ]
                    ),
                    "recent_5_safe_count": (
                        history[
                            "recent_5_safe_count"
                        ]
                    ),
                    "recent_5_mine_count": (
                        history[
                            "recent_5_mine_count"
                        ]
                    ),
                    "recent_10_games": (
                        history[
                            "recent_10_games"
                        ]
                    ),
                    "recent_10_safe_count": (
                        history[
                            "recent_10_safe_count"
                        ]
                    ),
                    "recent_10_mine_count": (
                        history[
                            "recent_10_mine_count"
                        ]
                    ),
                    "safe_streak": (
                        history[
                            "safe_streak"
                        ]
                    ),
                    "mine_streak": (
                        history[
                            "mine_streak"
                        ]
                    ),

                    # ------------------------------------------------
                    # Label is intentionally absent from the feature
                    # vector conceptually. The feature builder does
                    # not use labels as model features.
                    #
                    # We provide a placeholder because the existing
                    # dataset record structure expects one.
                    # ------------------------------------------------
                    "label": 1,

                    "generated_at": (
                        self._latest_datetime(
                            position_history
                        )
                    ),

                    "recorded_at": (
                        self._latest_datetime(
                            position_history
                        )
                    ),
                }
            )

        return records

    # ========================================================
    # POSITION HISTORY
    # ========================================================

    @staticmethod
    def _calculate_position_history(
        position_records: list[
            dict[str, Any]
        ],
    ) -> dict[str, int]:
        """
        Calculate historical features for one board position.

        Records are already chronological because they originate
        from the chronological dataset builder.
        """

        labels = [
            int(
                record["label"]
            )
            for record in position_records
        ]

        historical_games = len(
            labels
        )

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

        recent_5_safe_count = sum(
            label == 1
            for label in recent_5
        )

        recent_5_mine_count = sum(
            label == 0
            for label in recent_5
        )

        recent_10_safe_count = sum(
            label == 1
            for label in recent_10
        )

        recent_10_mine_count = sum(
            label == 0
            for label in recent_10
        )

        # ----------------------------------------------------
        # Calculate current SAFE streak.
        # ----------------------------------------------------

        safe_streak = 0

        for label in reversed(
            labels
        ):
            if label != 1:
                break

            safe_streak += 1

        # ----------------------------------------------------
        # Calculate current MINE streak.
        # ----------------------------------------------------

        mine_streak = 0

        for label in reversed(
            labels
        ):
            if label != 0:
                break

            mine_streak += 1

        return {
            "historical_games": (
                historical_games
            ),
            "historical_safe_count": (
                historical_safe_count
            ),
            "historical_mine_count": (
                historical_mine_count
            ),
            "recent_5_games": len(
                recent_5
            ),
            "recent_5_safe_count": (
                recent_5_safe_count
            ),
            "recent_5_mine_count": (
                recent_5_mine_count
            ),
            "recent_10_games": len(
                recent_10
            ),
            "recent_10_safe_count": (
                recent_10_safe_count
            ),
            "recent_10_mine_count": (
                recent_10_mine_count
            ),
            "safe_streak": safe_streak,
            "mine_streak": mine_streak,
        }

    # ========================================================
    # PREDICT
    # ========================================================

    def _predict_positions(
        self,
        *,
        model: RandomForestClassifier,
        prediction_records: list[
            dict[str, Any]
        ],
        board_size: int,
        top_n: int,
    ) -> list[int]:
        """
        Predict SAFE probabilities for every board position
        and return the highest-ranked positions.
        """

        X = np.asarray(
            [
                self.feature_builder.build_feature_row(
                    record
                )
                for record in prediction_records
            ],
            dtype=float,
        )

        expected_feature_count = len(
            self.feature_builder.feature_names()
        )

        total_cells = (
            board_size * board_size
        )

        if X.shape != (
            total_cells,
            expected_feature_count,
        ):
            raise RuntimeError(
                "Unexpected prediction feature "
                f"matrix shape: {X.shape}. "
                "Expected "
                f"({total_cells}, "
                f"{expected_feature_count})."
            )

        # ----------------------------------------------------
        # Predict probabilities.
        # ----------------------------------------------------

        probabilities = (
            model.predict_proba(X)
        )

        classes = [
            int(value)
            for value in model.classes_
        ]

        if 1 not in classes:
            raise RuntimeError(
                "Walk-forward model does not "
                "contain SAFE class 1."
            )

        safe_class_index = (
            classes.index(1)
        )

        safe_probabilities = [
            float(
                row[safe_class_index]
            )
            for row in probabilities
        ]

        # ----------------------------------------------------
        # Highest SAFE probability first.
        #
        # Position number is the deterministic tie-breaker.
        # ----------------------------------------------------

        ranked_indices = sorted(
            range(total_cells),
            key=lambda index: (
                -safe_probabilities[
                    index
                ],
                index + 1,
            ),
        )

        return [
            index + 1
            for index in ranked_indices[
                :top_n
            ]
        ]

    # ========================================================
    # EVALUATE ONE TARGET GAME
    # ========================================================

    def _evaluate_game(
        self,
        *,
        game_number: int,
        target_game: list[
            dict[str, Any]
        ],
        predicted_positions: list[int],
        historical_games_used: int,
        training_rows: int,
        training_safe_rows: int,
        training_mine_rows: int,
    ) -> WalkForwardGameResult:
        """
        Evaluate the target game AFTER prediction.

        This is the first point where target labels are used.
        """

        if not target_game:
            raise ValueError(
                "Cannot evaluate an empty "
                "target game."
            )

        first_record = (
            target_game[0]
        )

        # ----------------------------------------------------
        # Actual SAFE positions.
        # ----------------------------------------------------

        actual_safe_positions = sorted(
            int(
                record["position"]
            )
            for record in target_game
            if int(
                record["label"]
            ) == 1
        )

        # ----------------------------------------------------
        # Actual MINE positions.
        # ----------------------------------------------------

        actual_mine_positions = sorted(
            int(
                record["position"]
            )
            for record in target_game
            if int(
                record["label"]
            ) == 0
        )

        actual_safe_set = set(
            actual_safe_positions
        )

        actual_mine_set = set(
            actual_mine_positions
        )

        # ----------------------------------------------------
        # Top-N subsets.
        # ----------------------------------------------------

        top_1 = predicted_positions[:1]
        top_3 = predicted_positions[:3]
        top_5 = predicted_positions[:5]

        # ----------------------------------------------------
        # SAFE hits.
        # ----------------------------------------------------

        top_1_hits = sum(
            position in actual_safe_set
            for position in top_1
        )

        top_3_hits = sum(
            position in actual_safe_set
            for position in top_3
        )

        top_5_hits = sum(
            position in actual_safe_set
            for position in top_5
        )

        # ----------------------------------------------------
        # Precision.
        # ----------------------------------------------------

        safe_precision_at_1 = (
            top_1_hits / len(top_1)
            if top_1
            else 0.0
        )

        safe_precision_at_3 = (
            top_3_hits / len(top_3)
            if top_3
            else 0.0
        )

        safe_precision_at_5 = (
            top_5_hits / len(top_5)
            if top_5
            else 0.0
        )

        # ----------------------------------------------------
        # Mine contamination.
        # ----------------------------------------------------

        mine_hits_in_top_5 = sum(
            position in actual_mine_set
            for position in top_5
        )

        return WalkForwardGameResult(
            game_number=game_number,

            result_id=str(
                first_record[
                    "result_id"
                ]
            ),

            signal_id=str(
                first_record[
                    "signal_id"
                ]
            ),

            board_size=int(
                first_record[
                    "board_size"
                ]
            ),

            mine_count=int(
                first_record[
                    "mine_count"
                ]
            ),

            total_cells=int(
                first_record[
                    "total_cells"
                ]
            ),

            historical_games_used=(
                historical_games_used
            ),

            training_rows=training_rows,

            training_safe_rows=(
                training_safe_rows
            ),

            training_mine_rows=(
                training_mine_rows
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

            top_1_hit=(
                bool(top_1)
                and top_1[0]
                in actual_safe_set
            ),

            top_3_hits=top_3_hits,

            top_5_hits=top_5_hits,

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

            generated_at=(
                first_record.get(
                    "generated_at"
                )
            ),

            recorded_at=(
                first_record.get(
                    "recorded_at"
                )
            ),
        )

    # ========================================================
    # BUILD SUMMARY
    # ========================================================

    @staticmethod
    def _build_summary(
        *,
        board_size: int,
        mine_count: int,
        total_cells: int,
        games_available: int,
        games_skipped: int,
        min_historical_games: int,
        top_n: int,
        results: list[
            WalkForwardGameResult
        ],
    ) -> WalkForwardSummary:

        games_evaluated = len(
            results
        )

        if games_evaluated == 0:
            raise ValueError(
                "Cannot build walk-forward "
                "summary without results."
            )

        # ----------------------------------------------------
        # Average Top-1 precision.
        # ----------------------------------------------------

        average_top_1_precision = (
            sum(
                result.safe_precision_at_1
                for result in results
            )
            / games_evaluated
        )

        # ----------------------------------------------------
        # Average Top-3 precision.
        # ----------------------------------------------------

        average_top_3_precision = (
            sum(
                result.safe_precision_at_3
                for result in results
            )
            / games_evaluated
        )

        # ----------------------------------------------------
        # Average Top-5 precision.
        # ----------------------------------------------------

        average_top_5_precision = (
            sum(
                result.safe_precision_at_5
                for result in results
            )
            / games_evaluated
        )

        # ----------------------------------------------------
        # Top-1 hit rate.
        # ----------------------------------------------------

        top_1_hit_rate = (
            sum(
                1
                for result in results
                if result.top_1_hit
            )
            / games_evaluated
        )

        # ----------------------------------------------------
        # Average Top-3 safe hits.
        # ----------------------------------------------------

        average_top_3_hits = (
            sum(
                result.top_3_hits
                for result in results
            )
            / games_evaluated
        )

        # ----------------------------------------------------
        # Average Top-5 safe hits.
        # ----------------------------------------------------

        average_top_5_hits = (
            sum(
                result.top_5_hits
                for result in results
            )
            / games_evaluated
        )

        # ----------------------------------------------------
        # Average mines appearing in Top-5.
        # ----------------------------------------------------

        average_mine_hits_in_top_5 = (
            sum(
                result.mine_hits_in_top_5
                for result in results
            )
            / games_evaluated
        )

        return WalkForwardSummary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,

            games_available=(
                games_available
            ),

            games_evaluated=(
                games_evaluated
            ),

            games_skipped=(
                games_skipped
            ),

            min_historical_games=(
                min_historical_games
            ),

            top_n=top_n,

            average_top_1_precision=(
                average_top_1_precision
            ),

            average_top_3_precision=(
                average_top_3_precision
            ),

            average_top_5_precision=(
                average_top_5_precision
            ),

            top_1_hit_rate=(
                top_1_hit_rate
            ),

            average_top_3_hits=(
                average_top_3_hits
            ),

            average_top_5_hits=(
                average_top_5_hits
            ),

            average_mine_hits_in_top_5=(
                average_mine_hits_in_top_5
            ),

            model_name=MODEL_NAME,

            model_version=MODEL_VERSION,

            feature_version=FEATURE_VERSION,

            results=results,
        )

    # ========================================================
    # DATETIME HELPER
    # ========================================================

    @staticmethod
    def _latest_datetime(
        records: list[
            dict[str, Any]
        ],
    ) -> datetime | None:

        if not records:
            return None

        # Records are chronological, so check from the end.
        for record in reversed(
            records
        ):

            recorded_at = (
                record.get(
                    "recorded_at"
                )
            )

            if isinstance(
                recorded_at,
                datetime,
            ):
                return recorded_at

            generated_at = (
                record.get(
                    "generated_at"
                )
            )

            if isinstance(
                generated_at,
                datetime,
            ):
                return generated_at

        return None
 
