from __future__ import annotations

import json
import math
import pickle
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.feature_builder import MLFeatureBuilder


# ============================================================
# TRAINING RESULT
# ============================================================


@dataclass
class TrainingMetrics:
    """
    Metrics produced by one chronological ML training run.
    """

    total_rows: int

    training_rows: int
    validation_rows: int

    training_games: int
    validation_games: int

    safe_rows: int
    mine_rows: int

    accuracy: float
    balanced_accuracy: float

    precision: float
    recall: float

    roc_auc: float | None
    log_loss: float | None

    true_safe: int
    false_mine: int
    false_safe: int
    true_mine: int

    trained_at: str


@dataclass
class TrainingResult:
    """
    Complete result returned after training.
    """

    model_path: str
    metadata_path: str

    feature_names: list[str]

    metrics: TrainingMetrics

    model_parameters: dict[str, Any]


# ============================================================
# ML TRAINER
# ============================================================


class MLTrainer:
    """
    Trains and saves the first Mines ML classifier.

    Model:
        RandomForestClassifier

    Training strategy:
        Chronological split.

    Earlier historical games are used for training.
    Later historical games are reserved for validation.

    This is intentionally separate from PatternEngine.
    """

    MODEL_NAME = "mines_random_forest"

    MODEL_VERSION = "1.0.0"

    DEFAULT_VALIDATION_RATIO = 0.20

    DEFAULT_MIN_TRAINING_GAMES = 5

    DEFAULT_RANDOM_STATE = 42

    def __init__(
        self,
        db,
        *,
        model_directory: str | Path | None = None,
        validation_ratio: float = DEFAULT_VALIDATION_RATIO,
        min_training_games: int = DEFAULT_MIN_TRAINING_GAMES,
        random_state: int = DEFAULT_RANDOM_STATE,
    ) -> None:
        self.db = db

        self.validation_ratio = validation_ratio
        self.min_training_games = min_training_games
        self.random_state = random_state

        if not 0.05 <= validation_ratio <= 0.50:
            raise ValueError(
                "validation_ratio must be between "
                "0.05 and 0.50."
            )

        if min_training_games < 2:
            raise ValueError(
                "min_training_games must be at least 2."
            )

        if model_directory is None:
            model_directory = (
                Path(__file__).resolve().parent
                / "models"
            )

        self.model_directory = Path(
            model_directory
        )

        self.model_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.dataset_builder = MLDatasetBuilder(
            db,
        )

        self.feature_builder = MLFeatureBuilder()

    # ========================================================
    # TRAIN
    # ========================================================

    def train(
        self,
        *,
        board_size: int | None = None,
        mine_count: int | None = None,
    ) -> TrainingResult:
        """
        Build the historical dataset, split it chronologically,
        train the classifier, validate it, and save it.
        """

        records = (
            self.dataset_builder
            .build_feature_records(
                board_size=board_size,
                mine_count=mine_count,
                min_historical_games=0,
            )
        )

        if not records:
            raise ValueError(
                "No historical training data is available."
            )

        records = self._sort_records(
            records,
        )

        games = self._get_ordered_game_ids(
            records,
        )

        if len(games) < self.min_training_games + 2:
            raise ValueError(
                "Not enough historical games to train and "
                "validate the ML model. "
                f"Found {len(games)} games, but at least "
                f"{self.min_training_games + 2} are required."
            )

        training_games, validation_games = (
            self._chronological_split_games(
                games,
            )
        )

        training_game_set = set(
            training_games,
        )

        validation_game_set = set(
            validation_games,
        )

        training_records = [
            record
            for record in records
            if record["result_id"] in training_game_set
        ]

        validation_records = [
            record
            for record in records
            if record["result_id"] in validation_game_set
        ]

        if not training_records:
            raise ValueError(
                "Chronological split produced no training rows."
            )

        if not validation_records:
            raise ValueError(
                "Chronological split produced no validation rows."
            )

        X_train, y_train = (
            self.feature_builder
            .build_training_data(
                training_records,
            )
        )

        X_validation, y_validation = (
            self.feature_builder
            .build_training_data(
                validation_records,
            )
        )

        self._validate_training_labels(
            y_train,
            y_validation,
        )

        model = self._create_model()

        model.fit(
            X_train,
            y_train,
        )

        metrics = self._evaluate(
            model=model,
            X_train=X_train,
            y_train=y_train,
            X_validation=X_validation,
            y_validation=y_validation,
            training_records=training_records,
            validation_records=validation_records,
        )

        model_path = self._model_path(
            board_size=board_size,
            mine_count=mine_count,
        )

        metadata_path = self._metadata_path(
            board_size=board_size,
            mine_count=mine_count,
        )

        self._save_model(
            model=model,
            path=model_path,
        )

        model_parameters = (
            model.get_params()
        )

        metadata = {
            "model_name": self.MODEL_NAME,
            "model_version": self.MODEL_VERSION,
            "board_size": board_size,
            "mine_count": mine_count,
            "feature_names": (
                self.feature_builder
                .feature_names()
            ),
            "model_parameters": (
                self._json_safe(
                    model_parameters,
                )
            ),
            "metrics": asdict(metrics),
            "training_games": training_games,
            "validation_games": validation_games,
            "trained_at": metrics.trained_at,
        }

        self._save_metadata(
            metadata=metadata,
            path=metadata_path,
        )

        return TrainingResult(
            model_path=str(model_path),
            metadata_path=str(metadata_path),
            feature_names=(
                self.feature_builder
                .feature_names()
            ),
            metrics=metrics,
            model_parameters=(
                self._json_safe(
                    model_parameters,
                )
            ),
        )

    # ========================================================
    # MODEL
    # ========================================================

    def _create_model(
        self,
    ) -> RandomForestClassifier:
        """
        Create the initial baseline classifier.

        These parameters are intentionally conservative.
        We can tune them after establishing a reliable baseline.
        """

        return RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_split=8,
            min_samples_leaf=4,
            class_weight="balanced",
            random_state=self.random_state,
            n_jobs=-1,
        )

    # ========================================================
    # SPLIT
    # ========================================================

    def _chronological_split_games(
        self,
        games: list[str],
    ) -> tuple[list[str], list[str]]:
        """
        Split games chronologically.

        Example:

            Games 1-80  -> training
            Games 81-100 -> validation

        No future game is used to train the validation period.
        """

        total_games = len(games)

        validation_count = max(
            1,
            math.ceil(
                total_games
                * self.validation_ratio
            ),
        )

        training_count = (
            total_games
            - validation_count
        )

        if training_count < self.min_training_games:
            raise ValueError(
                "Not enough games remain for the "
                "training period."
            )

        training_games = games[
            :training_count
        ]

        validation_games = games[
            training_count:
        ]

        return (
            training_games,
            validation_games,
        )

    # ========================================================
    # EVALUATION
    # ========================================================

    def _evaluate(
        self,
        *,
        model: RandomForestClassifier,
        X_train: list[list[float]],
        y_train: list[int],
        X_validation: list[list[float]],
        y_validation: list[int],
        training_records: list[dict[str, Any]],
        validation_records: list[dict[str, Any]],
    ) -> TrainingMetrics:
        """
        Evaluate the model against the unseen chronological
        validation period.
        """

        train_predictions = (
            model.predict(X_train)
        )

        validation_predictions = (
            model.predict(X_validation)
        )

        validation_probabilities = (
            model.predict_proba(
                X_validation,
            )
        )

        validation_safe_probabilities = (
            self._safe_probabilities(
                model=model,
                probabilities=validation_probabilities,
            )
        )

        accuracy = accuracy_score(
            y_validation,
            validation_predictions,
        )

        balanced_accuracy = (
            balanced_accuracy_score(
                y_validation,
                validation_predictions,
            )
        )

        precision = precision_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        )

        recall = recall_score(
            y_validation,
            validation_predictions,
            zero_division=0,
        )

        roc_auc = self._safe_roc_auc(
            y_validation,
            validation_safe_probabilities,
        )

        logloss = self._safe_log_loss(
            y_validation,
            validation_probabilities,
        )

        matrix = confusion_matrix(
            y_validation,
            validation_predictions,
            labels=[1, 0],
        )

        true_safe = int(matrix[0][0])
        false_mine = int(matrix[0][1])

        false_safe = int(matrix[1][0])
        true_mine = int(matrix[1][1])

        return TrainingMetrics(
            total_rows=(
                len(training_records)
                + len(validation_records)
            ),
            training_rows=len(
                training_records,
            ),
            validation_rows=len(
                validation_records,
            ),
            training_games=len(
                {
                    record["result_id"]
                    for record in training_records
                }
            ),
            validation_games=len(
                {
                    record["result_id"]
                    for record in validation_records
                }
            ),
            safe_rows=sum(
                1
                for value in (
                    y_validation
                )
                if value == 1
            ),
            mine_rows=sum(
                1
                for value in (
                    y_validation
                )
                if value == 0
            ),
            accuracy=float(accuracy),
            balanced_accuracy=float(
                balanced_accuracy
            ),
            precision=float(precision),
            recall=float(recall),
            roc_auc=roc_auc,
            log_loss=logloss,
            true_safe=true_safe,
            false_mine=false_mine,
            false_safe=false_safe,
            true_mine=true_mine,
            trained_at=(
                datetime.now(
                    timezone.utc,
                ).isoformat()
            ),
        )

    # ========================================================
    # METRIC HELPERS
    # ========================================================

    @staticmethod
    def _safe_probabilities(
        *,
        model: RandomForestClassifier,
        probabilities: Any,
    ) -> list[float]:
        """
        Extract probability of SAFE (label 1).
        """

        classes = list(
            model.classes_
        )

        if 1 not in classes:
            return [
                0.0
                for _ in probabilities
            ]

        safe_index = classes.index(1)

        return [
            float(row[safe_index])
            for row in probabilities
        ]

    @staticmethod
    def _safe_roc_auc(
        y_true: list[int],
        probabilities: list[float],
    ) -> float | None:
        try:
            if len(set(y_true)) < 2:
                return None

            return float(
                roc_auc_score(
                    y_true,
                    probabilities,
                )
            )
        except ValueError:
            return None

    @staticmethod
    def _safe_log_loss(
        y_true: list[int],
        probabilities: Any,
    ) -> float | None:
        try:
            if len(set(y_true)) < 2:
                return None

            return float(
                log_loss(
                    y_true,
                    probabilities,
                    labels=[0, 1],
                )
            )
        except ValueError:
            return None

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_training_labels(
        y_train: list[int],
        y_validation: list[int],
    ) -> None:
        train_classes = set(y_train)
        validation_classes = set(
            y_validation,
        )

        if train_classes != {0, 1}:
            raise ValueError(
                "Training data must contain both SAFE (1) "
                "and MINE (0) labels."
            )

        if validation_classes != {0, 1}:
            raise ValueError(
                "Validation data must contain both SAFE (1) "
                "and MINE (0) labels."
            )

    # ========================================================
    # RECORD HELPERS
    # ========================================================

    @staticmethod
    def _sort_records(
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Ensure records are ordered chronologically.
        """

        return sorted(
            records,
            key=lambda record: (
                record["generated_at"],
                record["recorded_at"],
                record["result_id"],
                record["position"],
            ),
        )

    @staticmethod
    def _get_ordered_game_ids(
        records: list[dict[str, Any]],
    ) -> list[str]:
        """
        Return one result/game ID per historical board,
        preserving chronological order.
        """

        game_ids: list[str] = []
        seen: set[str] = set()

        for record in records:
            result_id = record["result_id"]

            if result_id in seen:
                continue

            seen.add(result_id)
            game_ids.append(result_id)

        return game_ids

    # ========================================================
    # STORAGE
    # ========================================================

    def _model_path(
        self,
        *,
        board_size: int | None,
        mine_count: int | None,
    ) -> Path:
        suffix = self._model_suffix(
            board_size=board_size,
            mine_count=mine_count,
        )

        return (
            self.model_directory
            / f"{self.MODEL_NAME}{suffix}.pkl"
        )

    def _metadata_path(
        self,
        *,
        board_size: int | None,
        mine_count: int | None,
    ) -> Path:
        suffix = self._model_suffix(
            board_size=board_size,
            mine_count=mine_count,
        )

        return (
            self.model_directory
            / f"{self.MODEL_NAME}{suffix}.json"
        )

    @staticmethod
    def _model_suffix(
        *,
        board_size: int | None,
        mine_count: int | None,
    ) -> str:
        if (
            board_size is not None
            and mine_count is not None
        ):
            return (
                f"_{board_size}x{board_size}"
                f"_{mine_count}mines"
            )

        if board_size is not None:
            return f"_{board_size}x{board_size}"

        if mine_count is not None:
            return f"_{mine_count}mines"

        return "_general"

    @staticmethod
    def _save_model(
        *,
        model: RandomForestClassifier,
        path: Path,
    ) -> None:
        with path.open(
            "wb",
        ) as file:
            pickle.dump(
                model,
                file,
            )

    @staticmethod
    def _save_metadata(
        *,
        metadata: dict[str, Any],
        path: Path,
    ) -> None:
        with path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                metadata,
                file,
                indent=2,
                default=str,
            )

    # ========================================================
    # JSON SAFETY
    # ========================================================

    @staticmethod
    def _json_safe(
        value: Any,
    ) -> Any:
        """
        Convert sklearn/numpy values into JSON-compatible
        Python values.
        """

        if value is None:
            return None

        if isinstance(
            value,
            (
                str,
                int,
                float,
                bool,
            ),
        ):
            return value

        if isinstance(value, dict):
            return {
                str(key): MLTrainer._json_safe(
                    item,
                )
                for key, item in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [
                MLTrainer._json_safe(
                    item,
                )
                for item in value
            ]

        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass

        return str(value)
 
