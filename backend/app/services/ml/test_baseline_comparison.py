"""
Compare the chronological RandomForest ML predictor against
a chronological positional-frequency baseline.

This is an evaluation script only.

It does NOT modify:
- Pattern Engine
- MLPredictor
- trained model
- live signal generation
"""


from __future__ import annotations

from collections import Counter

from app.db.session import SessionLocal
from app.services.ml.backtester import MLBacktester
from app.services.ml.baseline_backtester import (
    PositionFrequencyBacktester,
)


BOARD_SIZE = 5
MINE_COUNT = 3
MIN_HISTORICAL_GAMES = 5
TOP_N = 5


# ============================================================
# FORMATTING
# ============================================================


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def signed(value: float) -> str:
    return f"{value:+.4f}"


def signed_percent(value: float) -> str:
    return f"{value * 100:+.2f}%"


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    print()
    print("=" * 70)
    print("MINES ML ENGINE — ML VS POSITION-FREQUENCY BASELINE")
    print("=" * 70)
    print()

    print("Configuration")
    print(f"Board size              : {BOARD_SIZE}x{BOARD_SIZE}")
    print(f"Mine count              : {MINE_COUNT}")
    print(
        f"Minimum history         : "
        f"{MIN_HISTORICAL_GAMES}"
    )
    print(f"Top N                   : {TOP_N}")
    print()

    db = SessionLocal()

    try:
        # ====================================================
        # RUN RANDOMFOREST
        # ====================================================

        print("Running RandomForest chronological backtest...")
        print(
            "Only games before each target game "
            "will be used."
        )
        print()

        ml_backtester = MLBacktester(
            db=db,
        )

        ml_summary = ml_backtester.run(
            board_size=BOARD_SIZE,
            mine_count=MINE_COUNT,
            min_historical_games=(
                MIN_HISTORICAL_GAMES
            ),
            top_n=TOP_N,
        )

        # ====================================================
        # RUN POSITION-FREQUENCY BASELINE
        # ====================================================

        print(
            "Running positional-frequency "
            "chronological baseline..."
        )
        print(
            "Only games before each target game "
            "will be used."
        )
        print()

        baseline_backtester = (
            PositionFrequencyBacktester(
                db=db,
            )
        )

        baseline_summary = (
            baseline_backtester.run(
                board_size=BOARD_SIZE,
                mine_count=MINE_COUNT,
                min_historical_games=(
                    MIN_HISTORICAL_GAMES
                ),
                top_n=TOP_N,
            )
        )

        # ====================================================
        # MODEL SUMMARY
        # ====================================================

        print("=" * 70)
        print("MODEL INFORMATION")
        print("=" * 70)

        print(
            f"RandomForest model       : "
            f"{ml_summary.model_name}"
        )

        print(
            f"RandomForest version     : "
            f"{ml_summary.model_version}"
        )

        print(
            f"RandomForest features    : "
            f"{ml_summary.feature_version}"
        )

        print(
            f"Baseline                 : "
            f"{baseline_summary.model_name}"
        )

        print(
            f"Baseline version         : "
            f"{baseline_summary.model_version}"
        )

        print()

        # ====================================================
        # PERFORMANCE COMPARISON
        # ====================================================

        print("=" * 70)
        print("PERFORMANCE COMPARISON")
        print("=" * 70)

        print()
        print(
            f"{'Metric':<32}"
            f"{'RandomForest':>16}"
            f"{'Baseline':>16}"
            f"{'ML - Base':>16}"
        )
        print("-" * 80)

        rows = [
            (
                "Average Top-1 precision",
                ml_summary.average_top_1_precision,
                baseline_summary.average_top_1_precision,
                "percent",
            ),
            (
                "Average Top-3 precision",
                ml_summary.average_top_3_precision,
                baseline_summary.average_top_3_precision,
                "percent",
            ),
            (
                "Average Top-5 precision",
                ml_summary.average_top_5_precision,
                baseline_summary.average_top_5_precision,
                "percent",
            ),
            (
                "Top-1 hit rate",
                ml_summary.top_1_hit_rate,
                baseline_summary.top_1_hit_rate,
                "percent",
            ),
            (
                "Average Top-3 safe hits",
                ml_summary.average_top_3_hits,
                baseline_summary.average_top_3_hits,
                "number",
            ),
            (
                "Average Top-5 safe hits",
                ml_summary.average_top_5_hits,
                baseline_summary.average_top_5_hits,
                "number",
            ),
            (
                "Average mines in Top-5",
                ml_summary.average_mine_hits_in_top_5,
                baseline_summary.average_mine_hits_in_top_5,
                "number",
            ),
        ]

        for (
            label,
            ml_value,
            baseline_value,
            value_type,
        ) in rows:

            if value_type == "percent":
                ml_text = percent(ml_value)
                baseline_text = percent(
                    baseline_value
                )
                delta_text = signed_percent(
                    ml_value - baseline_value
                )
            else:
                ml_text = f"{ml_value:.4f}"
                baseline_text = (
                    f"{baseline_value:.4f}"
                )
                delta_text = signed(
                    ml_value - baseline_value
                )

            print(
                f"{label:<32}"
                f"{ml_text:>16}"
                f"{baseline_text:>16}"
                f"{delta_text:>16}"
            )

        print()

        # ====================================================
        # GAMES EVALUATED
        # ====================================================

        print(
            f"Games evaluated          : "
            f"{ml_summary.games_evaluated}"
        )

        print(
            f"Baseline games evaluated : "
            f"{baseline_summary.games_evaluated}"
        )

        if (
            ml_summary.games_evaluated
            != baseline_summary.games_evaluated
        ):
            raise RuntimeError(
                "ML and baseline evaluated a different "
                "number of games."
            )

        # ====================================================
        # PER-GAME COMPARISON
        # ====================================================

        print()
        print("=" * 70)
        print("PER-GAME COMPARISON")
        print("=" * 70)
        print()

        baseline_results = {
            result.result_id: result
            for result in (
                baseline_summary.results or []
            )
        }

        ml_results = (
            ml_summary.results or []
        )

        identical_top_5 = 0
        ml_better_top_5 = 0
        baseline_better_top_5 = 0
        same_top_1 = 0

        for index, ml_result in enumerate(
            ml_results,
            start=1,
        ):
            baseline_result = (
                baseline_results.get(
                    ml_result.result_id
                )
            )

            if baseline_result is None:
                raise RuntimeError(
                    "Missing baseline result for "
                    f"{ml_result.result_id}"
                )

            ml_top_5 = (
                ml_result.predicted_safe_positions[
                    :5
                ]
            )

            baseline_top_5 = (
                baseline_result.predicted_safe_positions[
                    :5
                ]
            )

            if ml_top_5 == baseline_top_5:
                identical_top_5 += 1

            if (
                ml_result.top_3_hits
                == baseline_result.top_3_hits
            ):
                pass

            if (
                ml_result.top_5_hits
                > baseline_result.top_5_hits
            ):
                ml_better_top_5 += 1

            elif (
                ml_result.top_5_hits
                < baseline_result.top_5_hits
            ):
                baseline_better_top_5 += 1

            if (
                ml_result.top_1_hit
                == baseline_result.top_1_hit
            ):
                same_top_1 += 1

            print(
                f"Game {index:02d} | "
                f"ML Top-5: "
                f"{ml_result.predicted_safe_positions[:5]} "
                f"| Safe {ml_result.top_5_hits}/5 "
                f"| Mines "
                f"{ml_result.mine_hits_in_top_5} "
                f"|| Baseline Top-5: "
                f"{baseline_result.predicted_safe_positions[:5]} "
                f"| Safe {baseline_result.top_5_hits}/5 "
                f"| Mines "
                f"{baseline_result.mine_hits_in_top_5}"
            )

        # ====================================================
        # PREDICTION OVERLAP
        # ====================================================

        total_games = len(
            ml_results
        )

        print()
        print("=" * 70)
        print("PREDICTION OVERLAP")
        print("=" * 70)

        print(
            f"Identical Top-5 predictions : "
            f"{identical_top_5}/{total_games} "
            f"({percent(identical_top_5 / total_games)})"
        )

        print(
            f"Same Top-1 result            : "
            f"{same_top_1}/{total_games} "
            f"({percent(same_top_1 / total_games)})"
        )

        print(
            f"ML better Top-5 safe hits    : "
            f"{ml_better_top_5}"
        )

        print(
            f"Baseline better Top-5 hits  : "
            f"{baseline_better_top_5}"
        )

        # ====================================================
        # POSITION USAGE
        # ====================================================

        print()
        print("=" * 70)
        print("POSITION USAGE")
        print("=" * 70)

        ml_position_counter = Counter()
        baseline_position_counter = Counter()

        for result in ml_results:
            ml_position_counter.update(
                result.predicted_safe_positions[
                    :TOP_N
                ]
            )

        for result in (
            baseline_summary.results or []
        ):
            baseline_position_counter.update(
                result.predicted_safe_positions[
                    :TOP_N
                ]
            )

        print()
        print("RandomForest most frequently selected:")
        print(
            ml_position_counter.most_common()
        )

        print()
        print("Baseline most frequently selected:")
        print(
            baseline_position_counter.most_common()
        )

        # ====================================================
        # OVERALL HISTORICAL POSITION FREQUENCY
        #
        # This is descriptive only. It is NOT used to
        # generate the walk-forward predictions above.
        # ====================================================

        print()
        print("=" * 70)
        print("OVERALL HISTORICAL POSITION FREQUENCY")
        print("=" * 70)

        records = (
            baseline_backtester
            .dataset_builder
            .build_feature_records(
                board_size=BOARD_SIZE,
                mine_count=MINE_COUNT,
                min_historical_games=0,
            )
        )

        games = (
            baseline_backtester
            ._group_games(records)
        )

        games.sort(
            key=baseline_backtester._game_sort_key
        )

        for game in games:
            baseline_backtester._validate_complete_game(
                game,
                board_size=BOARD_SIZE,
                mine_count=MINE_COUNT,
            )

        frequencies = (
            baseline_backtester
            .calculate_position_frequencies(
                historical_games=games,
                total_cells=(
                    BOARD_SIZE * BOARD_SIZE
                ),
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

        print()
        print(
            f"{'Pos':>4}"
            f"{'Games':>8}"
            f"{'Safe':>8}"
            f"{'Mine':>8}"
            f"{'Safe %':>10}"
            f"{'Mine %':>10}"
        )
        print("-" * 52)

        for item in frequencies:
            print(
                f"{item.position:>4}"
                f"{item.historical_games:>8}"
                f"{item.safe_count:>8}"
                f"{item.mine_count:>8}"
                f"{percent(item.safe_rate):>10}"
                f"{percent(item.mine_rate):>10}"
            )

        # ====================================================
        # CONCLUSION FLAGS
        # ====================================================

        ml_top_5 = (
            ml_summary.average_top_5_precision
        )

        baseline_top_5 = (
            baseline_summary.average_top_5_precision
        )

        ml_mines = (
            ml_summary.average_mine_hits_in_top_5
        )

        baseline_mines = (
            baseline_summary.average_mine_hits_in_top_5
        )

        print()
        print("=" * 70)
        print("INTERPRETATION")
        print("=" * 70)

        if (
            ml_top_5 > baseline_top_5
            and ml_mines < baseline_mines
        ):
            print(
                "RandomForest shows evidence of adding "
                "predictive value beyond the positional "
                "frequency baseline."
            )

        elif (
            ml_top_5 == baseline_top_5
            and ml_mines == baseline_mines
        ):
            print(
                "RandomForest matches the positional "
                "frequency baseline on the reported "
                "Top-5 metrics."
            )

        else:
            print(
                "RandomForest does not clearly outperform "
                "the positional frequency baseline on "
                "the reported Top-5 metrics."
            )

        print()
        print(
            "IMPORTANT: This comparison is descriptive "
            "validation only."
        )
        print(
            "It does not modify or authorize the live "
            "prediction pipeline."
        )

        print()
        print("=" * 70)
        print("COMPARISON COMPLETE")
        print("=" * 70)
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
 
