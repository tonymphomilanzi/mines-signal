from __future__ import annotations

import sys
from pathlib import Path


# ============================================================
# PROJECT PATH
# ============================================================
#
# Allows this file to be executed directly from:
#
# backend/app/services/ml/train_model.py
#
# without changing the application structure.
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[3]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


# ============================================================
# APPLICATION IMPORTS
# ============================================================

from app.db.session import SessionLocal
from app.services.ml.trainer import MLTrainer


# ============================================================
# CONFIGURATION
# ============================================================

# Set these to None to train one general model across all
# available board configurations.
#
# Example:
#
# BOARD_SIZE = 5
# MINE_COUNT = 3
#
# would train only on 5x5 boards with 3 mines.

BOARD_SIZE: int | None = None
MINE_COUNT: int | None = None


# Percentage of chronological historical games reserved
# for validation.
VALIDATION_RATIO = 0.20

# Minimum number of historical games required for training.
MIN_TRAINING_GAMES = 5


# ============================================================
# DISPLAY HELPERS
# ============================================================

def print_header(title: str) -> None:
    print()
    print("=" * 64)
    print(title)
    print("=" * 64)


def print_metric(
    name: str,
    value: object,
) -> None:
    print(
        f"{name:<30} {value}"
    )


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    print_header(
        "MINES ML ENGINE — TRAINING RUN"
    )

    print(
        "Loading historical Signal + SignalResult data..."
    )

    db = SessionLocal()

    try:
        trainer = MLTrainer(
            db=db,
            validation_ratio=VALIDATION_RATIO,
            min_training_games=MIN_TRAINING_GAMES,
        )

        # ----------------------------------------------------
        # TRAIN
        # ----------------------------------------------------

        result = trainer.train(
            board_size=BOARD_SIZE,
            mine_count=MINE_COUNT,
        )

        metrics = result.metrics

        # ----------------------------------------------------
        # DATASET SUMMARY
        # ----------------------------------------------------

        print_header(
            "DATASET SUMMARY"
        )

        total_games = (
            metrics.training_games
            + metrics.validation_games
        )

        print_metric(
            "Historical games",
            total_games,
        )

        print_metric(
            "Training games",
            metrics.training_games,
        )

        print_metric(
            "Validation games",
            metrics.validation_games,
        )

        print_metric(
            "Total dataset rows",
            metrics.total_rows,
        )

        print_metric(
            "Training rows",
            metrics.training_rows,
        )

        print_metric(
            "Validation rows",
            metrics.validation_rows,
        )

        # ----------------------------------------------------
        # LABEL DISTRIBUTION
        # ----------------------------------------------------

        print_header(
            "VALIDATION LABEL DISTRIBUTION"
        )

        print_metric(
            "SAFE rows",
            metrics.safe_rows,
        )

        print_metric(
            "MINE rows",
            metrics.mine_rows,
        )

        validation_total = (
            metrics.safe_rows
            + metrics.mine_rows
        )

        if validation_total > 0:
            safe_percentage = (
                metrics.safe_rows
                / validation_total
                * 100
            )

            mine_percentage = (
                metrics.mine_rows
                / validation_total
                * 100
            )
        else:
            safe_percentage = 0.0
            mine_percentage = 0.0

        print_metric(
            "SAFE percentage",
            f"{safe_percentage:.2f}%",
        )

        print_metric(
            "MINE percentage",
            f"{mine_percentage:.2f}%",
        )

        # ----------------------------------------------------
        # MODEL METRICS
        # ----------------------------------------------------

        print_header(
            "MODEL VALIDATION METRICS"
        )

        print_metric(
            "Accuracy",
            f"{metrics.accuracy:.4f}",
        )

        print_metric(
            "Balanced accuracy",
            f"{metrics.balanced_accuracy:.4f}",
        )

        print_metric(
            "Precision",
            f"{metrics.precision:.4f}",
        )

        print_metric(
            "Recall",
            f"{metrics.recall:.4f}",
        )

        if metrics.roc_auc is None:
            roc_auc = "N/A"
        else:
            roc_auc = f"{metrics.roc_auc:.4f}"

        print_metric(
            "ROC-AUC",
            roc_auc,
        )

        if metrics.log_loss is None:
            log_loss = "N/A"
        else:
            log_loss = f"{metrics.log_loss:.4f}"

        print_metric(
            "Log loss",
            log_loss,
        )

        # ----------------------------------------------------
        # CONFUSION MATRIX
        # ----------------------------------------------------

        print_header(
            "CONFUSION MATRIX"
        )

        print(
            "                    Predicted"
        )

        print(
            "                    SAFE      MINE"
        )

        print(
            f"Actual SAFE         "
            f"{metrics.true_safe:<9}"
            f"{metrics.false_mine}"
        )

        print(
            f"Actual MINE         "
            f"{metrics.false_safe:<9}"
            f"{metrics.true_mine}"
        )

        # ----------------------------------------------------
        # FEATURES
        # ----------------------------------------------------

        print_header(
            "FEATURES"
        )

        for index, name in enumerate(
            result.feature_names,
            start=1,
        ):
            print(
                f"{index:>2}. {name}"
            )

        # ----------------------------------------------------
        # MODEL PARAMETERS
        # ----------------------------------------------------

        print_header(
            "MODEL"
        )

        print_metric(
            "Model",
            trainer.MODEL_NAME,
        )

        print_metric(
            "Version",
            trainer.MODEL_VERSION,
        )

        print_metric(
            "Validation ratio",
            f"{trainer.validation_ratio:.0%}",
        )

        print_metric(
            "Random state",
            trainer.random_state,
        )

        # ----------------------------------------------------
        # SAVED FILES
        # ----------------------------------------------------

        print_header(
            "SAVED MODEL"
        )

        print_metric(
            "Model file",
            result.model_path,
        )

        print_metric(
            "Metadata file",
            result.metadata_path,
        )

        # ----------------------------------------------------
        # COMPLETE
        # ----------------------------------------------------

        print_header(
            "TRAINING COMPLETE"
        )

        print(
            "The ML model was trained and validated successfully."
        )

        print(
            "The live prediction pipeline has NOT been modified."
        )

    except Exception as exc:
        print_header(
            "ML TRAINING FAILED"
        )

        print(
            f"Error: {exc}"
        )

        raise

    finally:
        db.close()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
 
