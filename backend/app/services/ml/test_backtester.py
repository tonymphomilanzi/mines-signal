
from __future__ import annotations

from dataclasses import asdict, is_dataclass

from app.db.session import SessionLocal
from app.services.ml.backtester import MLBacktester


# ============================================================
# HELPERS
# ============================================================


def _format_value(value: object) -> str:
    """
    Convert a value into clean terminal-friendly text.
    """
    if value is None:
        return "N/A"

    return str(value)


def _print_result_fields(result: object) -> None:
    """
    Print GameBacktestResult safely without assuming
    specific field names.

    This keeps the test runner compatible if the result
    dataclass changes slightly in the future.
    """
    if is_dataclass(result):
        data = asdict(result)
    elif hasattr(result, "__dict__"):
        data = vars(result)
    else:
        print(
            f"Result                   : "
            f"{_format_value(result)}"
        )
        return

    # Keep the output in a useful order when these fields exist.
    preferred_order = [
        "result_id",
        "signal_id",
        "safe_positions",
        "mine_positions",
        "predicted_positions",
        "top_1_position",
        "top_1_hit",
        "top_3_hits",
        "top_5_hits",
        "correct_safe_predictions",
        "incorrect_safe_predictions",
        "precision_at_5",
        "safe_recall",
        "mine_avoidance_rate",
    ]

    printed = set()

    for field_name in preferred_order:
        if field_name not in data:
            continue

        value = data[field_name]

        label = field_name.replace("_", " ").title()

        print(
            f"{label:<28}: "
            f"{_format_value(value)}"
        )

        printed.add(field_name)

    # Print any additional fields that may exist.
    for field_name, value in data.items():
        if field_name in printed:
            continue

        label = field_name.replace("_", " ").title()

        print(
            f"{label:<28}: "
            f"{_format_value(value)}"
        )


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    print()
    print("=" * 72)
    print("MINES ML ENGINE — BACKTESTING RUN")
    print("=" * 72)

    db = SessionLocal()

    try:
        # --------------------------------------------------------
        # CONFIGURATION
        # --------------------------------------------------------

        board_size = 5
        mine_count = 3
        min_historical_games = 5
        top_n = 5

        print()
        print("Configuration")
        print("-" * 72)

        print(
            f"Board size              : "
            f"{board_size}x{board_size}"
        )

        print(
            f"Mine count              : "
            f"{mine_count}"
        )

        print(
            f"Minimum history         : "
            f"{min_historical_games}"
        )

        print(
            f"Top N                   : "
            f"{top_n}"
        )

        # --------------------------------------------------------
        # CREATE BACKTESTER
        # --------------------------------------------------------

        backtester = MLBacktester(
            db=db,
        )

        # --------------------------------------------------------
        # MODEL INFORMATION
        # --------------------------------------------------------

        print()
        print("Model")
        print("-" * 72)

        predictor = backtester.predictor

        model_name = getattr(
            predictor,
            "MODEL_NAME",
            None,
        )

        model_version = (
            predictor.metadata.get("model_version")
            if isinstance(
                getattr(predictor, "metadata", None),
                dict,
            )
            else None
        )

        if not model_version:
            model_version = getattr(
                predictor,
                "DEFAULT_MODEL_VERSION",
                None,
            )

        feature_builder = getattr(
            predictor,
            "feature_builder",
            None,
        )

        feature_version = getattr(
            feature_builder,
            "VERSION",
            None,
        )

        model_path = getattr(
            predictor,
            "model_path",
            None,
        )

        print(
            f"Model                   : "
            f"{model_name or 'N/A'}"
        )

        print(
            f"Model version           : "
            f"{model_version or 'N/A'}"
        )

        print(
            f"Feature version         : "
            f"{feature_version or 'N/A'}"
        )

        print(
            f"Model path              : "
            f"{model_path or 'N/A'}"
        )

        # --------------------------------------------------------
        # RUN BACKTEST
        # --------------------------------------------------------

        print()
        print("Running chronological backtest...")
        print(
            "Only games before each target game "
            "will be used."
        )
        print()

        report = backtester.run(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=min_historical_games,
            top_n=top_n,
        )

        # --------------------------------------------------------
        # SUMMARY
        # --------------------------------------------------------

        print()
        print("=" * 72)
        print("BACKTEST SUMMARY")
        print("=" * 72)

        print(
            f"Model                   : "
            f"{report.model_name or 'N/A'}"
        )

        print(
            f"Model version           : "
            f"{report.model_version or 'N/A'}"
        )

        print(
            f"Feature version         : "
            f"{report.feature_version or 'N/A'}"
        )

        print(
            f"Board size              : "
            f"{report.board_size}x"
            f"{report.board_size}"
        )

        print(
            f"Mine count              : "
            f"{report.mine_count}"
        )

        print(
            f"Total cells             : "
            f"{report.total_cells}"
        )

        print(
            f"Games evaluated         : "
            f"{report.games_evaluated}"
        )

        # --------------------------------------------------------
        # PREDICTION PERFORMANCE
        # --------------------------------------------------------

        print()
        print("Prediction performance")
        print("-" * 72)

        print(
            f"Average Top-1 precision : "
            f"{report.average_top_1_precision:.4f} "
            f"({report.average_top_1_precision * 100:.2f}%)"
        )

        print(
            f"Average Top-3 precision : "
            f"{report.average_top_3_precision:.4f} "
            f"({report.average_top_3_precision * 100:.2f}%)"
        )

        print(
            f"Average Top-5 precision : "
            f"{report.average_top_5_precision:.4f} "
            f"({report.average_top_5_precision * 100:.2f}%)"
        )

        print(
            f"Top-1 hit rate           : "
            f"{report.top_1_hit_rate:.4f} "
            f"({report.top_1_hit_rate * 100:.2f}%)"
        )

        print(
            f"Average Top-3 hits       : "
            f"{report.average_top_3_hits:.4f}"
        )

        print(
            f"Average Top-5 hits       : "
            f"{report.average_top_5_hits:.4f}"
        )

        print(
            f"Average mine hits Top-5  : "
            f"{report.average_mine_hits_in_top_5:.4f}"
        )

        # --------------------------------------------------------
        # INTERPRETATION
        # --------------------------------------------------------

        print()
        print("Backtest interpretation")
        print("-" * 72)

        print(
            "Top-1 hit rate represents the percentage of evaluated "
            "games where the highest-ranked SAFE position was "
            "actually safe."
        )

        print(
            "Average Top-3/Top-5 hits represent the average number "
            "of actual SAFE positions found within those ranked "
            "prediction sets."
        )

        print(
            "Average mine hits Top-5 represents how many actual "
            "mine positions appeared among the five predicted "
            "SAFE positions on average."
        )

        # --------------------------------------------------------
        # PER-GAME RESULTS
        # --------------------------------------------------------

        print()
        print("=" * 72)
        print("PER-GAME RESULTS")
        print("=" * 72)

        results = report.results or []

        if not results:
            print()
            print("No game results were produced.")
        else:
            for index, result in enumerate(
                results,
                start=1,
            ):
                print()
                print(
                    f"Game {index} / "
                    f"{report.games_evaluated}"
                )

                print("-" * 72)

                _print_result_fields(result)

        # --------------------------------------------------------
        # COMPLETION
        # --------------------------------------------------------

        print()
        print("=" * 72)
        print("BACKTEST COMPLETE")
        print("=" * 72)

        print()
        print(
            f"Successfully evaluated "
            f"{report.games_evaluated} historical games."
        )

        print()

    except Exception as exc:
        print()
        print("=" * 72)
        print("BACKTEST FAILED")
        print("=" * 72)
        print()

        print(
            f"{type(exc).__name__}: {exc}"
        )

        print()

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
 
