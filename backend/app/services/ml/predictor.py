from __future__ import annotations

import json
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.services.ml.feature_builder import MLFeatureBuilder


# ============================================================
# PREDICTION RESULT
# ============================================================


@dataclass(frozen=True)
class PositionPrediction:
    """
    ML prediction for one board position.

    safe_probability:
        Probability assigned by the model to SAFE (label 1).

    mine_probability:
        Probability assigned by the model to MINE (label 0).

    rank:
        Position ranking based on SAFE probability.
    """

    position: int

    row: int

    column: int

    safe_probability: float

    mine_probability: float

    rank: int


@dataclass(frozen=True)
class PredictionResult:
    """
    Complete prediction for one board.
    """

    board_size: int

    mine_count: int

    total_cells: int

    model_name: str

    model_version: str

    feature_version: str

    predictions: list[PositionPrediction]

    top_positions: list[int]


# ============================================================
# ML PREDICTOR
# ============================================================


class MLPredictor:
    """
    Loads a trained Random Forest model and ranks all board
    positions by probability of being SAFE.

    IMPORTANT:

    This class does NOT modify:

        PatternEngine
        Signal
        Signal lifecycle
        live prediction services

    It is an isolated ML prediction component.
    """

    MODEL_NAME = "mines_random_forest"

    DEFAULT_MODEL_VERSION = "1.0.0"

    def __init__(
        self,
        *,
        model_path: str | Path | None = None,
        metadata_path: str | Path | None = None,
    ) -> None:

        default_directory = (
            Path(__file__).resolve().parent
            / "models"
        )

        if model_path is None:
            model_path = (
                default_directory
                / "mines_random_forest_general.pkl"
            )

        if metadata_path is None:
            metadata_path = (
                default_directory
                / "mines_random_forest_general.json"
            )

        self.model_path = Path(
            model_path
        )

        self.metadata_path = Path(
            metadata_path
        )

        self.feature_builder = (
            MLFeatureBuilder()
        )

        self.model: RandomForestClassifier | None = None

        self.metadata: dict[str, Any] = {}

        self._load()

    # ========================================================
    # LOAD
    # ========================================================

    def _load(self) -> None:
        """
        Load the trained model and metadata.
        """

        if not self.model_path.exists():
            raise FileNotFoundError(
                "ML model file was not found: "
                f"{self.model_path}"
            )

        if not self.metadata_path.exists():
            raise FileNotFoundError(
                "ML model metadata file was not found: "
                f"{self.metadata_path}"
            )

        with self.model_path.open(
            "rb"
        ) as file:
            model = pickle.load(file)

        if not isinstance(
            model,
            RandomForestClassifier,
        ):
            raise TypeError(
                "Saved ML model is not a "
                "RandomForestClassifier."
            )

        with self.metadata_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            metadata = json.load(file)

        self._validate_metadata(
            metadata
        )

        self.model = model

        self.metadata = metadata

    # ========================================================
    # METADATA VALIDATION
    # ========================================================

    def _validate_metadata(
        self,
        metadata: dict[str, Any],
    ) -> None:
        """
        Verify that the saved model was trained with the
        feature configuration currently used by the predictor.
        """

        saved_feature_names = metadata.get(
            "feature_names"
        )

        if not isinstance(
            saved_feature_names,
            list,
        ):
            raise ValueError(
                "ML model metadata does not contain "
                "a valid feature_names list."
            )

        current_feature_names = (
            self.feature_builder.feature_names()
        )

        if saved_feature_names != current_feature_names:
            raise ValueError(
                "ML feature mismatch detected.\n"
                f"Saved features: "
                f"{saved_feature_names}\n"
                f"Current features: "
                f"{current_feature_names}"
            )

        model_name = metadata.get(
            "model_name"
        )

        if model_name != self.MODEL_NAME:
            raise ValueError(
                "Unexpected ML model name: "
                f"{model_name}"
            )

    # ========================================================
    # PREDICT
    # ========================================================

    def predict_board(
        self,
        *,
        board_size: int,
        mine_count: int,
        historical_records: list[
            dict[str, Any]
        ],
        top_n: int = 5,
    ) -> PredictionResult:
        """
        Predict SAFE probability for every position on
        the board.

        historical_records must contain the same dictionary
        records produced by MLDatasetBuilder.

        Only historical information available before the
        current prediction should be supplied.

        The current/future result must NOT be included.
        """

        if board_size < 2:
            raise ValueError(
                "board_size must be at least 2."
            )

        if mine_count < 1:
            raise ValueError(
                "mine_count must be at least 1."
            )

        total_cells = (
            board_size * board_size
        )

        if mine_count >= total_cells:
            raise ValueError(
                "mine_count must be smaller "
                "than the total number of cells."
            )

        if top_n < 1:
            raise ValueError(
                "top_n must be at least 1."
            )

        top_n = min(
            top_n,
            total_cells,
        )

        if self.model is None:
            raise RuntimeError(
                "ML model has not been loaded."
            )

        records = (
            self._build_prediction_records(
                board_size=board_size,
                mine_count=mine_count,
                historical_records=(
                    historical_records
                ),
            )
        )

        X = np.asarray(
            [
                self.feature_builder
                .build_feature_row(record)
                for record in records
            ],
            dtype=float,
        )

        expected_feature_count = (
            len(
                self.feature_builder
                .feature_names()
            )
        )

        if X.shape != (
            total_cells,
            expected_feature_count,
        ):
            raise RuntimeError(
                "Unexpected prediction feature "
                f"matrix shape: {X.shape}. "
                f"Expected "
                f"({total_cells}, "
                f"{expected_feature_count})."
            )

        probabilities = (
            self.model.predict_proba(X)
        )

        safe_probabilities = (
            self._extract_safe_probabilities(
                probabilities
            )
        )

        predictions: list[
            PositionPrediction
        ] = []

        for index, safe_probability in enumerate(
            safe_probabilities
        ):

            position = index + 1

            row, column = divmod(
                index,
                board_size,
            )

            mine_probability = (
                1.0 - safe_probability
            )

            predictions.append(
                PositionPrediction(
                    position=position,
                    row=row,
                    column=column,
                    safe_probability=(
                        safe_probability
                    ),
                    mine_probability=(
                        mine_probability
                    ),
                    rank=0,
                )
            )

        # ----------------------------------------------------
        # Rank highest SAFE probability first.
        # ----------------------------------------------------

        predictions.sort(
            key=lambda prediction: (
                -prediction.safe_probability,
                prediction.position,
            )
        )

        ranked_predictions = [
            PositionPrediction(
                position=prediction.position,
                row=prediction.row,
                column=prediction.column,
                safe_probability=(
                    prediction.safe_probability
                ),
                mine_probability=(
                    prediction.mine_probability
                ),
                rank=index + 1,
            )
            for index, prediction in enumerate(
                predictions
            )
        ]

        top_predictions = (
            ranked_predictions[:top_n]
        )

        return PredictionResult(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,
            model_name=(
                self.metadata.get(
                    "model_name",
                    self.MODEL_NAME,
                )
            ),
            model_version=(
                self.metadata.get(
                    "model_version",
                    self.DEFAULT_MODEL_VERSION,
                )
            ),
            feature_version=(
                self.feature_builder.VERSION
            ),
            predictions=ranked_predictions,
            top_positions=[
                prediction.position
                for prediction in top_predictions
            ],
        )

    # ========================================================
    # BUILD PREDICTION RECORDS
    # ========================================================

    def _build_prediction_records(
        self,
        *,
        board_size: int,
        mine_count: int,
        historical_records: list[
            dict[str, Any]
        ],
    ) -> list[dict[str, Any]]:
        """
        Build one feature record for every board position.

        Historical statistics are calculated from records
        supplied by the caller.

        No current/future result is used.
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

            position_records = [
                record
                for record in historical_records
                if (
                    int(
                        record["board_size"]
                    )
                    == board_size
                    and int(
                        record["mine_count"]
                    )
                    == mine_count
                    and int(
                        record["position"]
                    )
                    == position
                )
            ]

            # ------------------------------------------------
            # Sort chronologically.
            # ------------------------------------------------

            position_records.sort(
                key=lambda record: (
                    record["generated_at"],
                    record["recorded_at"],
                    record["result_id"],
                )
            )

            labels = [
                int(record["label"])
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

            safe_streak = (
                self._safe_streak(labels)
            )

            mine_streak = (
                self._mine_streak(labels)
            )

            records.append(
                {
                    "board_size": board_size,
                    "mine_count": mine_count,
                    "total_cells": total_cells,

                    "position": position,
                    "row": row,
                    "column": column,

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

                    "recent_5_safe_count": sum(
                        label == 1
                        for label in recent_5
                    ),

                    "recent_5_mine_count": sum(
                        label == 0
                        for label in recent_5
                    ),

                    "recent_10_games": len(
                        recent_10
                    ),

                    "recent_10_safe_count": sum(
                        label == 1
                        for label in recent_10
                    ),

                    "recent_10_mine_count": sum(
                        label == 0
                        for label in recent_10
                    ),

                    "safe_streak": safe_streak,

                    "mine_streak": mine_streak,

                    # Dummy label.
                    #
                    # It is required by the common record
                    # structure, but feature_builder.py
                    # deliberately does NOT use it.
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

                    "signal_id": "",
                    "result_id": (
                        "prediction"
                    ),
                }
            )

        return records

    # ========================================================
    # PROBABILITY
    # ========================================================

    def _extract_safe_probabilities(
        self,
        probabilities: Any,
    ) -> list[float]:
        """
        Extract P(SAFE) where SAFE = label 1.
        """

        if self.model is None:
            raise RuntimeError(
                "ML model has not been loaded."
            )

        classes = list(
            self.model.classes_
        )

        if 1 not in classes:
            return [
                0.0
                for _ in probabilities
            ]

        safe_index = classes.index(
            1
        )

        return [
            float(row[safe_index])
            for row in probabilities
        ]

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

    # ========================================================
    # DATETIME
    # ========================================================

    @staticmethod
    def _latest_datetime(
        records: list[
            dict[str, Any]
        ],
    ) -> Any:
        """
        Return the latest known timestamp.

        Prediction records do not depend on this value as
        a feature, but the common dataset structure expects
        these fields.
        """

        if not records:
            return None

        latest = records[-1]

        return latest.get(
            "recorded_at"
        ) or latest.get(
            "generated_at"
        )
 
