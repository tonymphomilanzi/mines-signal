from __future__ import annotations

from app.db.session import SessionLocal
from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.predictor import MLPredictor


def main() -> None:
    print()
    print("=" * 64)
    print("MINES ML ENGINE — PREDICTOR TEST")
    print("=" * 64)

    db = SessionLocal()

    try:
        # ====================================================
        # LOAD HISTORICAL DATA
        # ====================================================

        print()
        print("Loading historical records...")

        historical_records = (
            MLDatasetBuilder(
                db
            ).build_feature_records(
                min_historical_games=0,
            )
        )

        print(
            "Historical dataset rows     ",
            len(historical_records),
        )

        # ====================================================
        # LOAD MODEL
        # ====================================================

        print()
        print("Loading trained ML model...")

        predictor = MLPredictor()

        print(
            "Model                       ",
            predictor.metadata.get(
                "model_name"
            ),
        )

        print(
            "Model version               ",
            predictor.metadata.get(
                "model_version"
            ),
        )

        print(
            "Feature version             ",
            predictor.feature_builder.VERSION,
        )

        # ====================================================
        # PREDICT
        # ====================================================

        print()
        print("Generating 5x5 prediction...")
        print()

        result = predictor.predict_board(
            board_size=5,
            mine_count=3,
            historical_records=(
                historical_records
            ),
            top_n=5,
        )

        # ====================================================
        # RESULT
        # ====================================================

        print("=" * 64)
        print("PREDICTION RESULT")
        print("=" * 64)

        print(
            "Board size                  ",
            result.board_size,
        )

        print(
            "Mine count                  ",
            result.mine_count,
        )

        print(
            "Total cells                 ",
            result.total_cells,
        )

        print(
            "Model                       ",
            result.model_name,
        )

        print(
            "Model version               ",
            result.model_version,
        )

        print(
            "Feature version             ",
            result.feature_version,
        )

        print()
        print("TOP 5 SAFE POSITIONS")
        print("-" * 64)

        for prediction in result.predictions[
            :5
        ]:
            print(
                f"Rank {prediction.rank:>2} | "
                f"Position {prediction.position:>2} | "
                f"Row {prediction.row} | "
                f"Column {prediction.column} | "
                f"SAFE "
                f"{prediction.safe_probability:.4f} | "
                f"MINE "
                f"{prediction.mine_probability:.4f}"
            )

        print()
        print(
            "Top positions              ",
            result.top_positions,
        )

        print()
        print("=" * 64)
        print("PREDICTOR TEST COMPLETE")
        print("=" * 64)

    finally:
        db.close()


if __name__ == "__main__":
    main()
 
