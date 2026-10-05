"""
Walk-forward ML backtest runner.

Runs true chronological walk-forward training and evaluation.

Usage:
    python -m app.services.ml.test_walk_forward
"""

from __future__ import annotations

from app.db.session import SessionLocal
from app.services.ml.walk_forward_backtester import (
    WalkForwardBacktester,
)


def main() -> None:
    db = SessionLocal()

    try:
        board_size = 5
        mine_count = 3
        min_historical_games = 5
        top_n = 5

        print("=" * 90)
        print("MINES AI — WALK-FORWARD BACKTEST")
        print("=" * 90)

        print()
        print("CONFIGURATION")
        print("-" * 90)
        print(f"Board size            : {board_size}x{board_size}")
        print(f"Mine count            : {mine_count}")
        print(f"Minimum history      : {min_historical_games}")
        print(f"Top N                 : {top_n}")

        backtester = WalkForwardBacktester(db)

        summary = backtester.run(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=min_historical_games,
            top_n=top_n,
        )

        print()
        print("MODEL")
        print("-" * 90)
        print(f"Model                 : {summary.model_name}")
        print(f"Model version         : {summary.model_version}")
        print(f"Feature version       : {summary.feature_version}")

        print()
        print("DATASET")
        print("-" * 90)
        print(f"Games available       : {summary.games_available}")
        print(f"Games skipped         : {summary.games_skipped}")
        print(f"Games evaluated       : {summary.games_evaluated}")

        if not summary.results:
            print()
            print("No games were available for walk-forward evaluation.")
            return

        print()
        print("=" * 90)
        print("WALK-FORWARD GAME RESULTS")
        print("=" * 90)

        for index, result in enumerate(summary.results, start=1):
            print()
            print(f"GAME {index:02d}")
            print("-" * 90)

            print(f"Result ID             : {result.result_id}")
            print(f"Signal ID             : {result.signal_id}")

            print()
            print("Training")
            print(f"  Historical games    : {result.historical_games_used}")
            print(f"  Training rows       : {result.training_rows}")
            print(f"  SAFE rows           : {result.training_safe_rows}")
            print(f"  MINE rows           : {result.training_mine_rows}")

            print()
            print("Prediction")
            print(
                "  Predicted SAFE      : "
                f"{result.predicted_safe_positions}"
            )

            print(
                "  Actual SAFE         : "
                f"{result.actual_safe_positions}"
            )

            print(
                "  Actual MINE         : "
                f"{result.actual_mine_positions}"
            )

            print()
            print("Evaluation")
            print(
                f"  Top-1 hit           : "
                f"{'YES' if result.top_1_hit else 'NO'}"
            )

            print(
                f"  Top-3 safe hits     : "
                f"{result.top_3_hits}"
            )

            print(
                f"  Top-5 safe hits     : "
                f"{result.top_5_hits}"
            )

            print(
                f"  Top-1 precision     : "
                f"{result.safe_precision_at_1:.2%}"
            )

            print(
                f"  Top-3 precision     : "
                f"{result.safe_precision_at_3:.2%}"
            )

            print(
                f"  Top-5 precision     : "
                f"{result.safe_precision_at_5:.2%}"
            )

            print(
                f"  Mines in Top-5      : "
                f"{result.mine_hits_in_top_5}"
            )

        # --------------------------------------------------------
        # AGGREGATE METRICS
        # --------------------------------------------------------

        print()
        print("=" * 90)
        print("FINAL AGGREGATE METRICS")
        print("=" * 90)

        print(
            f"Games evaluated       : "
            f"{summary.games_evaluated}"
        )

        print(
            f"Average Top-1        : "
            f"{summary.average_top_1_precision:.2%}"
        )

        print(
            f"Average Top-3        : "
            f"{summary.average_top_3_precision:.2%}"
        )

        print(
            f"Average Top-5        : "
            f"{summary.average_top_5_precision:.2%}"
        )

        print(
            f"Top-1 hit rate        : "
            f"{summary.top_1_hit_rate:.2%}"
        )

        print(
            f"Average Top-3 hits    : "
            f"{summary.average_top_3_hits:.4f}"
        )

        print(
            f"Average Top-5 hits    : "
            f"{summary.average_top_5_hits:.4f}"
        )

        print(
            f"Average mines Top-5   : "
            f"{summary.average_mine_hits_in_top_5:.4f}"
        )

        print()
        print("=" * 90)
        print("WALK-FORWARD EVALUATION COMPLETE")
        print("=" * 90)

    finally:
        db.close()


if __name__ == "__main__":
    main()
 
