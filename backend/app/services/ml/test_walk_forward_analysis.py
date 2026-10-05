from __future__ import annotations

from app.db.session import SessionLocal
from app.services.ml.walk_forward_analysis import (
    WalkForwardAnalyzer,
)


BOARD_SIZE = 5
MINE_COUNT = 3
MIN_HISTORICAL_GAMES = 5
TOP_N = 5


def percentage(value: float) -> str:
    return f"{value * 100:.2f}%"


def print_separator() -> None:
    print("-" * 78)


def main() -> None:

    db = SessionLocal()

    try:
        analyzer = WalkForwardAnalyzer(db)

        summary = analyzer.run(
            board_size=BOARD_SIZE,
            mine_count=MINE_COUNT,
            min_historical_games=(
                MIN_HISTORICAL_GAMES
            ),
            top_n=TOP_N,
        )

        print()
        print("=" * 78)
        print(
            "MINES AI — WALK-FORWARD STATISTICAL ANALYSIS"
        )
        print("=" * 78)

        print()
        print("CONFIGURATION")
        print_separator()

        print(
            f"Board size              : "
            f"{summary.board_size}x"
            f"{summary.board_size}"
        )

        print(
            f"Mine count              : "
            f"{summary.mine_count}"
        )

        print(
            f"Minimum history        : "
            f"{summary.min_historical_games}"
        )

        print(
            f"Top N                   : "
            f"{summary.top_n}"
        )

        print()
        print("DATASET")
        print_separator()

        print(
            f"Games available         : "
            f"{summary.games_available}"
        )

        print(
            f"Games skipped           : "
            f"{summary.games_skipped}"
        )

        print(
            f"Games evaluated         : "
            f"{summary.games_evaluated}"
        )

        # ====================================================
        # OVERALL PERFORMANCE
        # ====================================================

        print()
        print("ML VS BASELINE")
        print_separator()

        print(
            f"Top-1 hit rate          : "
            f"{percentage(summary.ml_top_1_hit_rate):>10} "
            f"vs "
            f"{percentage(summary.baseline_top_1_hit_rate)}"
        )

        top_1_difference = (
            summary.ml_top_1_hit_rate
            - summary.baseline_top_1_hit_rate
        )

        print(
            f"Top-1 difference        : "
            f"{top_1_difference * 100:+.2f} pp"
        )

        print()

        print(
            f"Average Top-3 hits      : "
            f"{summary.ml_average_top_3_hits:.4f} "
            f"vs "
            f"{summary.baseline_average_top_3_hits:.4f}"
        )

        top_3_difference = (
            summary.ml_average_top_3_hits
            - summary.baseline_average_top_3_hits
        )

        print(
            f"Top-3 difference        : "
            f"{top_3_difference:+.4f}"
        )

        print()

        print(
            f"Average Top-5 hits      : "
            f"{summary.ml_average_top_5_hits:.4f} "
            f"vs "
            f"{summary.baseline_average_top_5_hits:.4f}"
        )

        top_5_difference = (
            summary.ml_average_top_5_hits
            - summary.baseline_average_top_5_hits
        )

        print(
            f"Top-5 difference        : "
            f"{top_5_difference:+.4f}"
        )

        print()

        print(
            f"Top-5 precision         : "
            f"{percentage(summary.ml_average_top_5_precision)} "
            f"vs "
            f"{percentage(summary.baseline_average_top_5_precision)}"
        )

        print()

        print(
            f"Mines in Top-5          : "
            f"{summary.ml_average_mines_top_5:.4f} "
            f"vs "
            f"{summary.baseline_average_mines_top_5:.4f}"
        )

        mine_difference = (
            summary.ml_average_mines_top_5
            - summary.baseline_average_mines_top_5
        )

        print(
            f"Mine exposure difference: "
            f"{mine_difference:+.4f}"
        )

        # ====================================================
        # HEAD TO HEAD
        # ====================================================

        print()
        print("HEAD-TO-HEAD")
        print_separator()

        print(
            f"ML better games         : "
            f"{summary.ml_better_games}"
        )

        print(
            f"Baseline better games   : "
            f"{summary.baseline_better_games}"
        )

        print(
            f"Tied games              : "
            f"{summary.tied_games}"
        )

        # ====================================================
        # STATISTICAL CHECK
        # ====================================================

        print()
        print("STATISTICAL CHECK")
        print_separator()

        print(
            "Exact sign-test p-value : "
            f"{summary.exact_sign_test_p_value:.6f}"
        )

        print(
            "Permutation p-value     : "
            f"{summary.permutation_p_value_top_5:.6f}"
        )

        print()
        print(
            "Note: These tests describe the observed "
            "paired historical sample."
        )

        print(
            "They do not establish production-level "
            "predictive validity."
        )

        # ====================================================
        # HISTORY SEGMENTS
        # ====================================================

        print()
        print("PERFORMANCE AS HISTORY GROWS")
        print_separator()

        print(
            f"{'Segment':<10}"
            f"{'Games':>8}"
            f"{'ML Top-1':>12}"
            f"{'Base Top-1':>13}"
            f"{'ML Top-5':>12}"
            f"{'Base Top-5':>13}"
            f"{'Diff':>10}"
        )

        for segment in summary.segments:

            print(
                f"{segment.name:<10}"
                f"{segment.games_evaluated:>8}"
                f"{percentage(segment.ml_top_1_hit_rate):>12}"
                f"{percentage(segment.baseline_top_1_hit_rate):>13}"
                f"{percentage(segment.ml_top_5_precision):>12}"
                f"{percentage(segment.baseline_top_5_precision):>13}"
                f"{segment.top_5_difference * 100:+.2f} pp"
            )

        # ====================================================
        # POSITION ANALYSIS
        # ====================================================

        print()
        print("POSITION ANALYSIS")
        print_separator()

        print(
            f"{'Pos':>4}"
            f"{'Hist Safe':>11}"
            f"{'ML Sel.':>10}"
            f"{'Base Sel.':>11}"
            f"{'ML Only':>9}"
            f"{'Base Only':>11}"
            f"{'ML Mines':>10}"
            f"{'Base Mines':>12}"
        )

        for position in summary.positions:

            print(
                f"{position.position:>4}"
                f"{percentage(position.historical_safe_rate):>11}"
                f"{percentage(position.ml_selection_rate):>10}"
                f"{percentage(position.baseline_selection_rate):>11}"
                f"{position.ml_only_count:>9}"
                f"{position.baseline_only_count:>11}"
                f"{position.ml_selected_mines:>10}"
                f"{position.baseline_selected_mines:>12}"
            )

        # ====================================================
        # GAME-BY-GAME DIFFERENCES
        # ====================================================

        print()
        print("GAME-BY-GAME COMPARISON")
        print_separator()

        print(
            f"{'Game':>5}"
            f"{'Hist':>6}"
            f"{'ML T1':>7}"
            f"{'Base T1':>8}"
            f"{'ML T3':>7}"
            f"{'Base T3':>8}"
            f"{'ML T5':>7}"
            f"{'Base T5':>9}"
            f"{'ML Mines':>9}"
            f"{'Base Mines':>11}"
            f"{'Winner':>11}"
        )

        for result in summary.games:

            ml_t1 = (
                "YES"
                if result.ml_top_1_hit
                else "NO"
            )

            baseline_t1 = (
                "YES"
                if result.baseline_top_1_hit
                else "NO"
            )

            print(
                f"{result.game_number:>5}"
                f"{result.historical_games_used:>6}"
                f"{ml_t1:>7}"
                f"{baseline_t1:>8}"
                f"{result.ml_top_3_hits:>7}"
                f"{result.baseline_top_3_hits:>8}"
                f"{result.ml_top_5_hits:>7}"
                f"{result.baseline_top_5_hits:>9}"
                f"{result.ml_mines_in_top_5:>9}"
                f"{result.baseline_mines_in_top_5:>11}"
                f"{result.winner:>11}"
            )

        # ====================================================
        # DIFFERENTIATED POSITIONS
        # ====================================================

        print()
        print("ML VS BASELINE POSITION DIFFERENCES")
        print_separator()

        for result in summary.games:

            if (
                not result.ml_only_positions
                and not result.baseline_only_positions
            ):
                continue

            print(
                f"Game {result.game_number:>2} | "
                f"ML only: "
                f"{result.ml_only_positions} | "
                f"Baseline only: "
                f"{result.baseline_only_positions}"
            )

            if result.ml_avoided_baseline_mines:
                print(
                    "           ML avoided baseline mine(s): "
                    f"{result.ml_avoided_baseline_mines}"
                )

        # ====================================================
        # FINAL INTERPRETATION
        # ====================================================

        print()
        print("INTERPRETATION")
        print_separator()

        if (
            summary.ml_average_top_5_precision
            > summary.baseline_average_top_5_precision
        ):
            print(
                "ML has the higher observed average "
                "Top-5 precision in this walk-forward sample."
            )
        elif (
            summary.ml_average_top_5_precision
            < summary.baseline_average_top_5_precision
        ):
            print(
                "The baseline has the higher observed "
                "average Top-5 precision in this sample."
            )
        else:
            print(
                "ML and baseline have equal observed "
                "average Top-5 precision."
            )

        print()

        if (
            summary.ml_average_mines_top_5
            < summary.baseline_average_mines_top_5
        ):
            print(
                "ML also has lower observed mine exposure "
                "in the Top-5."
            )
        elif (
            summary.ml_average_mines_top_5
            > summary.baseline_average_mines_top_5
        ):
            print(
                "ML has higher observed mine exposure "
                "in the Top-5."
            )
        else:
            print(
                "ML and baseline have equal observed "
                "mine exposure."
            )

        print()

        print(
            "This analysis is diagnostic only."
        )

        print(
            "Pattern Engine remains unchanged."
        )

        print(
            "Production ML integration remains disabled."
        )

        print(
            "The current sample should be expanded before "
            "making production decisions."
        )

        print()
        print("=" * 78)
        print("ANALYSIS COMPLETE")
        print("=" * 78)
        print()

    finally:
        db.close()


if __name__ == "__main__":
    main()
 