from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.result import ResultStatus, SignalResult
from app.models.signal import Signal


# ============================================================
# DATASET RECORD
# ============================================================


@dataclass(frozen=True)
class DatasetRecord:
    """
    Internal representation of one board-position training row.

    MLTrainer consumes this record as a dictionary.

    The to_dict() method provides the exact dictionary contract
    expected by the existing trainer.py.
    """

    signal_id: str
    result_id: str

    board_size: int
    mine_count: int
    total_cells: int

    position: int
    row: int
    column: int

    historical_games: int
    historical_safe_count: int
    historical_mine_count: int

    recent_5_games: int
    recent_5_safe_count: int
    recent_5_mine_count: int

    recent_10_games: int
    recent_10_safe_count: int
    recent_10_mine_count: int

    safe_streak: int
    mine_streak: int

    label: int

    generated_at: datetime
    recorded_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """
        Convert this record into the dictionary format expected
        by MLTrainer and MLFeatureBuilder.
        """

        return {
            "signal_id": self.signal_id,
            "result_id": self.result_id,

            "board_size": self.board_size,
            "mine_count": self.mine_count,
            "total_cells": self.total_cells,

            "position": self.position,
            "row": self.row,
            "column": self.column,

            "historical_games": self.historical_games,
            "historical_safe_count": (
                self.historical_safe_count
            ),
            "historical_mine_count": (
                self.historical_mine_count
            ),

            "recent_5_games": self.recent_5_games,
            "recent_5_safe_count": (
                self.recent_5_safe_count
            ),
            "recent_5_mine_count": (
                self.recent_5_mine_count
            ),

            "recent_10_games": self.recent_10_games,
            "recent_10_safe_count": (
                self.recent_10_safe_count
            ),
            "recent_10_mine_count": (
                self.recent_10_mine_count
            ),

            "safe_streak": self.safe_streak,
            "mine_streak": self.mine_streak,

            "label": self.label,

            "generated_at": self.generated_at,
            "recorded_at": self.recorded_at,
        }


# ============================================================
# POSITION HISTORY
# ============================================================


@dataclass
class _PositionHistory:
    """
    Historical state for one board position.

    History is isolated by:

        board_size
        mine_count
        position

    Outcomes:

        1 = SAFE
        0 = MINE
    """

    outcomes: list[int]

    safe_count: int = 0
    mine_count: int = 0

    @property
    def games(self) -> int:
        return len(self.outcomes)

    def add(self, label: int) -> None:
        """
        Add an actual historical outcome.

        IMPORTANT:
        This is called only AFTER the current dataset row
        has been created.
        """

        self.outcomes.append(label)

        if label == 1:
            self.safe_count += 1
        else:
            self.mine_count += 1

    def recent(self, window: int) -> list[int]:
        if window <= 0:
            return []

        return self.outcomes[-window:]

    def current_safe_streak(self) -> int:
        streak = 0

        for outcome in reversed(self.outcomes):
            if outcome != 1:
                break

            streak += 1

        return streak

    def current_mine_streak(self) -> int:
        streak = 0

        for outcome in reversed(self.outcomes):
            if outcome != 0:
                break

            streak += 1

        return streak


# ============================================================
# DATASET BUILDER
# ============================================================


class MLDatasetBuilder:
    """
    Builds the chronological, leakage-safe ML dataset.

    One completed 5x5 game produces:

        25 rows

    With 24 completed games:

        24 × 25 = 600 rows

    Leakage protection:

        historical state
              ↓
        create current row
              ↓
        add current outcome to history

    Therefore the current game's actual result never appears
    in its own historical features.
    """

    def __init__(
        self,
        db: Session,
        *,
        include_failed_results: bool = False,
        board_size: int | None = None,
        mine_count: int | None = None,
    ) -> None:
        self.db = db

        self.include_failed_results = (
            include_failed_results
        )

        self.board_size = board_size
        self.mine_count = mine_count

    # ========================================================
    # PUBLIC API
    # ========================================================

    def build_dataset(
        self,
        *,
        board_size: int | None = None,
        mine_count: int | None = None,
        min_historical_games: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Build training records.

        Returns dictionaries because the existing MLTrainer
        expects dictionary-style access:

            record["result_id"]
            record["generated_at"]
            record["label"]
            etc.
        """

        effective_board_size = (
            board_size
            if board_size is not None
            else self.board_size
        )

        effective_mine_count = (
            mine_count
            if mine_count is not None
            else self.mine_count
        )

        completed_games = (
            self._load_completed_games(
                board_size=effective_board_size,
                mine_count=effective_mine_count,
            )
        )

        histories: dict[
            tuple[int, int, int],
            _PositionHistory,
        ] = {}

        rows: list[dict[str, Any]] = []

        # ====================================================
        # PROCESS GAMES CHRONOLOGICALLY
        # ====================================================

        for signal, result in completed_games:

            current_board_size = int(
                signal.board_size
            )

            current_mine_count = int(
                signal.mine_count
            )

            total_cells = (
                current_board_size
                * current_board_size
            )

            # ------------------------------------------------
            # Actual mine positions.
            # ------------------------------------------------

            actual_mines = {
                int(position)
                for position in (
                    result.actual_mine_positions
                    or []
                )
            }

            # ------------------------------------------------
            # Actual safe positions.
            # ------------------------------------------------

            actual_safe = {
                int(position)
                for position in (
                    result.actual_safe_positions
                    or []
                )
            }

            # ------------------------------------------------
            # Validate complete board.
            # ------------------------------------------------

            expected_positions = set(
                range(
                    1,
                    total_cells + 1,
                )
            )

            actual_positions = (
                actual_mines | actual_safe
            )

            missing_positions = (
                expected_positions
                - actual_positions
            )

            unknown_positions = (
                actual_positions
                - expected_positions
            )

            if missing_positions:
                raise ValueError(
                    "Incomplete result detected: "
                    f"signal={signal.signal_number}, "
                    f"missing_positions="
                    f"{sorted(missing_positions)}"
                )

            if unknown_positions:
                raise ValueError(
                    "Invalid result detected: "
                    f"signal={signal.signal_number}, "
                    f"unknown_positions="
                    f"{sorted(unknown_positions)}"
                )

            # ------------------------------------------------
            # SAFE and MINE cannot overlap.
            # ------------------------------------------------

            overlap = (
                actual_mines & actual_safe
            )

            if overlap:
                raise ValueError(
                    "Invalid result detected: "
                    f"signal={signal.signal_number}, "
                    f"positions classified as both "
                    f"SAFE and MINE: "
                    f"{sorted(overlap)}"
                )

            # =================================================
            # EVERY BOARD POSITION
            # =================================================

            for position in range(
                1,
                total_cells + 1,
            ):

                # ---------------------------------------------
                # Ground-truth label.
                #
                # SAFE = 1
                # MINE = 0
                # ---------------------------------------------

                if position in actual_mines:
                    label = 0
                elif position in actual_safe:
                    label = 1
                else:
                    raise ValueError(
                        "Unable to determine result label: "
                        f"signal={signal.signal_number}, "
                        f"position={position}"
                    )

                # ---------------------------------------------
                # Convert position to row/column.
                # ---------------------------------------------

                row_index, column_index = divmod(
                    position - 1,
                    current_board_size,
                )

                # ---------------------------------------------
                # Isolated history key.
                # ---------------------------------------------

                history_key = (
                    current_board_size,
                    current_mine_count,
                    position,
                )

                history = histories.setdefault(
                    history_key,
                    _PositionHistory(
                        outcomes=[]
                    ),
                )

                # =================================================
                # READ ONLY PREVIOUS HISTORY
                # =================================================

                historical_games = (
                    history.games
                )

                historical_safe_count = (
                    history.safe_count
                )

                historical_mine_count = (
                    history.mine_count
                )

                recent_5 = history.recent(5)
                recent_10 = history.recent(10)

                safe_streak = (
                    history.current_safe_streak()
                )

                mine_streak = (
                    history.current_mine_streak()
                )

                # =================================================
                # CREATE RECORD
                # =================================================

                if (
                    historical_games
                    >= min_historical_games
                ):
                    record = DatasetRecord(
                        signal_id=str(
                            signal.id
                        ),

                        result_id=str(
                            result.id
                        ),

                        board_size=(
                            current_board_size
                        ),

                        mine_count=(
                            current_mine_count
                        ),

                        total_cells=(
                            total_cells
                        ),

                        position=position,

                        row=row_index,

                        column=column_index,

                        historical_games=(
                            historical_games
                        ),

                        historical_safe_count=(
                            historical_safe_count
                        ),

                        historical_mine_count=(
                            historical_mine_count
                        ),

                        recent_5_games=len(
                            recent_5
                        ),

                        recent_5_safe_count=sum(
                            value == 1
                            for value in recent_5
                        ),

                        recent_5_mine_count=sum(
                            value == 0
                            for value in recent_5
                        ),

                        recent_10_games=len(
                            recent_10
                        ),

                        recent_10_safe_count=sum(
                            value == 1
                            for value in recent_10
                        ),

                        recent_10_mine_count=sum(
                            value == 0
                            for value in recent_10
                        ),

                        safe_streak=(
                            safe_streak
                        ),

                        mine_streak=(
                            mine_streak
                        ),

                        label=label,

                        generated_at=(
                            signal.generated_at
                        ),

                        recorded_at=(
                            result.recorded_at
                        ),
                    )

                    rows.append(
                        record.to_dict()
                    )

                # =================================================
                # UPDATE HISTORY ONLY AFTER CURRENT RECORD
                # =================================================

                history.add(label)

        return rows

    # ========================================================
    # TRAINER COMPATIBILITY
    # ========================================================

    def build_feature_records(
        self,
        *,
        board_size: int | None = None,
        mine_count: int | None = None,
        min_historical_games: int = 0,
    ) -> list[dict[str, Any]]:
        """
        Exact API expected by the existing MLTrainer.
        """

        return self.build_dataset(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=(
                min_historical_games
            ),
        )

    # ========================================================
    # DATABASE
    # ========================================================

    def _load_completed_games(
        self,
        *,
        board_size: int | None = None,
        mine_count: int | None = None,
    ) -> list[tuple[Signal, SignalResult]]:
        """
        Load completed Signal + SignalResult pairs
        chronologically.
        """

        statement = (
            select(
                Signal,
                SignalResult,
            )
            .join(
                SignalResult,
                SignalResult.signal_id
                == Signal.id,
            )
            .where(
                SignalResult.actual_mine_positions.is_not(
                    None
                ),
                SignalResult.actual_safe_positions.is_not(
                    None
                ),
            )
            .order_by(
                Signal.generated_at.asc(),
                SignalResult.recorded_at.asc(),
            )
        )

        # ----------------------------------------------------
        # By default, only successful results are training data.
        # ----------------------------------------------------

        if not self.include_failed_results:
            statement = statement.where(
                SignalResult.status
                == ResultStatus.SUCCESS
            )

        # ----------------------------------------------------
        # Optional board-size filter.
        # ----------------------------------------------------

        if board_size is not None:
            statement = statement.where(
                Signal.board_size == board_size
            )

        # ----------------------------------------------------
        # Optional mine-count filter.
        # ----------------------------------------------------

        if mine_count is not None:
            statement = statement.where(
                Signal.mine_count == mine_count
            )

        # ----------------------------------------------------
        # Execute.
        # ----------------------------------------------------

        result = self.db.execute(
            statement
        )

        # ----------------------------------------------------
        # Explicitly materialize and return rows.
        # ----------------------------------------------------

        return list(
            result.all()
        )
 
