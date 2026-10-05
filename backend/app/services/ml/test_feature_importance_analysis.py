"""
Mines AI — Feature Importance Analysis Runner

Run:

    python -m app.services.ml.test_feature_importance_analysis
"""

from __future__ import annotations

from app.db.session import SessionLocal
from app.services.ml.feature_importance_analysis import (
    FeatureImportanceAnalyzer,
)


def print_features(
    title: str,
    features,
) -> None:

    print()
    print(title)
    print("-" * 78)

    for index, feature in enumerate(
        features,
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{feature.feature_name:<32} "
            f"{feature.percentage:>8.3f}%"
        )


def print_groups(
    title: str,
    groups,
) -> None:

    print()
    print(title)
    print("-" * 78)

    for index, group in enumerate(
        groups,
        start=1,
    ):
        print(
            f"{index:>2}. "
            f"{group.group_name:<24} "
            f"{group.percentage:>8.3f}%"
        )


def main() -> None:

    print("=" * 78)
    print("MINES AI — FEATURE IMPORTANCE ANALYSIS")
    print("=" * 78)

    db = SessionLocal()

    try:
        analyzer = FeatureImportanceAnalyzer(db)

        summary = analyzer.run(
            board_size=5,
            mine_count=3,
            min_historical_games=5,
            top_n=10,
        )

        print()
        print("CONFIGURATION")
        print("-" * 78)
        print("Board size              : 5x5")
        print("Mine count              : 3")
        print("Minimum history        : 5")
        print("Top features           : 10")

        print()
        print("DATASET")
        print("-" * 78)
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

        print_features(
            "OVERALL FEATURE IMPORTANCE",
            summary.overall_features,
        )

        print_groups(
            "OVERALL FEATURE GROUP IMPORTANCE",
            summary.overall_groups,
        )

        print_features(
            "EARLY HISTORY — FEATURE IMPORTANCE",
            summary.early_features,
        )

        print_groups(
            "EARLY HISTORY — GROUP IMPORTANCE",
            summary.early_groups,
        )

        print_features(
            "MIDDLE HISTORY — FEATURE IMPORTANCE",
            summary.middle_features,
        )

        print_groups(
            "MIDDLE HISTORY — GROUP IMPORTANCE",
            summary.middle_groups,
        )

        print_features(
            "LATE HISTORY — FEATURE IMPORTANCE",
            summary.late_features,
        )

        print_groups(
            "LATE HISTORY — GROUP IMPORTANCE",
            summary.late_groups,
        )

        print()
        print("PER-GAME TOP FEATURES")
        print("-" * 78)

        for game in summary.per_game:

            top_three = ", ".join(
                feature.feature_name
                for feature in game.top_features[:3]
            )

            print(
                f"Game {game.game_number:>2} | "
                f"History {game.historical_games:>2} | "
                f"Rows {game.training_rows:>4} | "
                f"Top: {top_three}"
            )

        print()
        print("TRAINING CLASS BALANCE")
        print("-" * 78)

        for game in summary.per_game:
            print(
                f"Game {game.game_number:>2} | "
                f"History {game.historical_games:>2} | "
                f"SAFE {game.training_safe_rows:>4} | "
                f"MINE {game.training_mine_rows:>3}"
            )

        print()
        print("=" * 78)
        print("ANALYSIS COMPLETE")
        print("=" * 78)

    finally:
        db.close()


if __name__ == "__main__":
    main()
 
