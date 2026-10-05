from __future__ import annotations

from math import sqrt
from typing import Any, Mapping, Sequence

import numpy as np


# ============================================================
# FEATURE BUILDER
# ============================================================


class MLFeatureBuilder:
    """
    Feature Engineering 2.0.

    Accepts dictionary records produced by MLDatasetBuilder.

    Produces 38 numerical features.

    The current result label is NEVER used as an input feature.
    """

    VERSION = "2.0.0"

    FEATURE_NAMES = (
        # -----------------------------------------------------
        # Board/configuration
        # -----------------------------------------------------

        "board_size",
        "mine_count",
        "total_cells",
        "position",
        "row",
        "column",

        "position_normalized",
        "row_normalized",
        "column_normalized",

        # -----------------------------------------------------
        # Basic geometry
        # -----------------------------------------------------

        "is_corner",
        "is_edge",
        "is_center",

        # -----------------------------------------------------
        # Distance geometry
        # -----------------------------------------------------

        "distance_from_center",
        "distance_from_top",
        "distance_from_bottom",
        "distance_from_left",
        "distance_from_right",

        "distance_from_center_normalized",
        "distance_from_top_normalized",
        "distance_from_bottom_normalized",
        "distance_from_left_normalized",
        "distance_from_right_normalized",

        # -----------------------------------------------------
        # Neighborhood geometry
        # -----------------------------------------------------

        "number_of_neighbors",
        "number_of_diagonal_neighbors",
        "number_of_horizontal_neighbors",
        "number_of_vertical_neighbors",

        # -----------------------------------------------------
        # Historical statistics
        # -----------------------------------------------------

        "historical_games",
        "historical_safe_frequency",
        "historical_mine_frequency",
        "historical_balance",

        # -----------------------------------------------------
        # Recent 5
        # -----------------------------------------------------

        "recent_5_safe_frequency",
        "recent_5_mine_frequency",
        "recent_5_balance",

        # -----------------------------------------------------
        # Recent 10
        # -----------------------------------------------------

        "recent_10_safe_frequency",
        "recent_10_mine_frequency",
        "recent_10_balance",

        # -----------------------------------------------------
        # Streaks
        # -----------------------------------------------------

        "safe_streak",
        "mine_streak",
    )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def feature_names(self) -> list[str]:
        """
        Return feature names in exact matrix order.
        """

        return list(
            self.FEATURE_NAMES
        )

    def build_training_data(
        self,
        records: Sequence[
            Mapping[str, Any]
        ],
    ) -> tuple[np.ndarray, np.ndarray]:
        """
        Convert dictionary records into:

            X = feature matrix
            y = target labels

        Labels:

            1 = SAFE
            0 = MINE
        """

        if not records:
            raise ValueError(
                "No dataset records were provided."
            )

        X = np.asarray(
            [
                self.build_feature_row(
                    record
                )
                for record in records
            ],
            dtype=float,
        )

        y = np.asarray(
            [
                int(record["label"])
                for record in records
            ],
            dtype=int,
        )

        if X.ndim != 2:
            raise RuntimeError(
                "Feature matrix must be two-dimensional."
            )

        if X.shape[1] != len(
            self.FEATURE_NAMES
        ):
            raise RuntimeError(
                "Feature count mismatch: "
                f"X has {X.shape[1]} columns, "
                f"but FEATURE_NAMES contains "
                f"{len(self.FEATURE_NAMES)} features."
            )

        return X, y

    def build_feature_row(
        self,
        record: Mapping[str, Any],
    ) -> list[float]:
        """
        Build one 38-feature vector.

        IMPORTANT:
        record["label"] is deliberately not used here.
        """

        board_size = int(
            record["board_size"]
        )

        total_cells = int(
            record["total_cells"]
        )

        position = int(
            record["position"]
        )

        row = int(
            record["row"]
        )

        column = int(
            record["column"]
        )

        # ----------------------------------------------------
        # Geometry
        # ----------------------------------------------------

        geometry = self._build_geometry(
            row=row,
            column=column,
            board_size=board_size,
        )

        # ----------------------------------------------------
        # Historical frequencies
        # ----------------------------------------------------

        historical_games = int(
            record["historical_games"]
        )

        historical_safe_count = int(
            record["historical_safe_count"]
        )

        historical_mine_count = int(
            record["historical_mine_count"]
        )

        historical_safe_frequency = (
            self._frequency(
                historical_safe_count,
                historical_games,
            )
        )

        historical_mine_frequency = (
            self._frequency(
                historical_mine_count,
                historical_games,
            )
        )

        historical_balance = (
            historical_safe_frequency
            - historical_mine_frequency
        )

        # ----------------------------------------------------
        # Recent 5
        # ----------------------------------------------------

        recent_5_games = int(
            record["recent_5_games"]
        )

        recent_5_safe_count = int(
            record["recent_5_safe_count"]
        )

        recent_5_mine_count = int(
            record["recent_5_mine_count"]
        )

        recent_5_safe_frequency = (
            self._frequency(
                recent_5_safe_count,
                recent_5_games,
            )
        )

        recent_5_mine_frequency = (
            self._frequency(
                recent_5_mine_count,
                recent_5_games,
            )
        )

        recent_5_balance = (
            recent_5_safe_frequency
            - recent_5_mine_frequency
        )

        # ----------------------------------------------------
        # Recent 10
        # ----------------------------------------------------

        recent_10_games = int(
            record["recent_10_games"]
        )

        recent_10_safe_count = int(
            record["recent_10_safe_count"]
        )

        recent_10_mine_count = int(
            record["recent_10_mine_count"]
        )

        recent_10_safe_frequency = (
            self._frequency(
                recent_10_safe_count,
                recent_10_games,
            )
        )

        recent_10_mine_frequency = (
            self._frequency(
                recent_10_mine_count,
                recent_10_games,
            )
        )

        recent_10_balance = (
            recent_10_safe_frequency
            - recent_10_mine_frequency
        )

        # ----------------------------------------------------
        # Position normalization
        # ----------------------------------------------------

        max_position = max(
            total_cells - 1,
            1,
        )

        max_row_column = max(
            board_size - 1,
            1,
        )

        position_normalized = (
            float(position - 1)
            / max_position
        )

        row_normalized = (
            float(row)
            / max_row_column
        )

        column_normalized = (
            float(column)
            / max_row_column
        )

        # ====================================================
        # FINAL 38 FEATURES
        # ====================================================

        return [
            # 1-9
            float(board_size),
            float(record["mine_count"]),
            float(total_cells),
            float(position),
            float(row),
            float(column),
            position_normalized,
            row_normalized,
            column_normalized,

            # 10-12
            geometry["is_corner"],
            geometry["is_edge"],
            geometry["is_center"],

            # 13-17
            geometry["distance_from_center"],
            geometry["distance_from_top"],
            geometry["distance_from_bottom"],
            geometry["distance_from_left"],
            geometry["distance_from_right"],

            # 18-22
            geometry[
                "distance_from_center_normalized"
            ],
            geometry[
                "distance_from_top_normalized"
            ],
            geometry[
                "distance_from_bottom_normalized"
            ],
            geometry[
                "distance_from_left_normalized"
            ],
            geometry[
                "distance_from_right_normalized"
            ],

            # 23-26
            geometry["number_of_neighbors"],
            geometry[
                "number_of_diagonal_neighbors"
            ],
            geometry[
                "number_of_horizontal_neighbors"
            ],
            geometry[
                "number_of_vertical_neighbors"
            ],

            # 27-30
            float(historical_games),
            historical_safe_frequency,
            historical_mine_frequency,
            historical_balance,

            # 31-33
            recent_5_safe_frequency,
            recent_5_mine_frequency,
            recent_5_balance,

            # 34-36
            recent_10_safe_frequency,
            recent_10_mine_frequency,
            recent_10_balance,

            # 37-38
            float(record["safe_streak"]),
            float(record["mine_streak"]),
        ]

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _frequency(
        count: int,
        games: int,
    ) -> float:
        if games <= 0:
            return 0.0

        return float(count) / float(games)

    @staticmethod
    def _normalize(
        value: float,
        maximum: float,
    ) -> float:
        if maximum <= 0:
            return 0.0

        return value / maximum

    # ========================================================
    # GEOMETRY
    # ========================================================

    def _build_geometry(
        self,
        *,
        row: int,
        column: int,
        board_size: int,
    ) -> dict[str, float]:

        last = board_size - 1

        center = last / 2.0

        # ----------------------------------------------------
        # Center distance
        # ----------------------------------------------------

        distance_from_center = sqrt(
            ((row - center) ** 2)
            + ((column - center) ** 2)
        )

        max_center_distance = sqrt(
            2 * (center**2)
        )

        # ----------------------------------------------------
        # Edge distances
        # ----------------------------------------------------

        distance_from_top = float(row)

        distance_from_bottom = float(
            last - row
        )

        distance_from_left = float(
            column
        )

        distance_from_right = float(
            last - column
        )

        max_edge_distance = float(last)

        # ----------------------------------------------------
        # Basic geometry
        # ----------------------------------------------------

        is_corner = (
            row in (0, last)
            and column in (0, last)
        )

        is_edge = (
            row == 0
            or row == last
            or column == 0
            or column == last
        )

        is_center = (
            row == center
            and column == center
        )

        # ----------------------------------------------------
        # Neighbor counts
        # ----------------------------------------------------

        number_of_neighbors = 0

        number_of_diagonal_neighbors = 0

        number_of_horizontal_neighbors = 0

        number_of_vertical_neighbors = 0

        for delta_row in (-1, 0, 1):

            for delta_column in (-1, 0, 1):

                if (
                    delta_row == 0
                    and delta_column == 0
                ):
                    continue

                neighbor_row = (
                    row + delta_row
                )

                neighbor_column = (
                    column + delta_column
                )

                if not (
                    0 <= neighbor_row < board_size
                    and 0 <= neighbor_column < board_size
                ):
                    continue

                number_of_neighbors += 1

                # Diagonal.
                if (
                    delta_row != 0
                    and delta_column != 0
                ):
                    number_of_diagonal_neighbors += 1

                # Horizontal.
                elif delta_row == 0:
                    number_of_horizontal_neighbors += 1

                # Vertical.
                elif delta_column == 0:
                    number_of_vertical_neighbors += 1

        return {
            "is_corner": float(is_corner),
            "is_edge": float(is_edge),
            "is_center": float(is_center),

            "distance_from_center": (
                distance_from_center
            ),

            "distance_from_top": (
                distance_from_top
            ),

            "distance_from_bottom": (
                distance_from_bottom
            ),

            "distance_from_left": (
                distance_from_left
            ),

            "distance_from_right": (
                distance_from_right
            ),

            "distance_from_center_normalized": (
                self._normalize(
                    distance_from_center,
                    max_center_distance,
                )
            ),

            "distance_from_top_normalized": (
                self._normalize(
                    distance_from_top,
                    max_edge_distance,
                )
            ),

            "distance_from_bottom_normalized": (
                self._normalize(
                    distance_from_bottom,
                    max_edge_distance,
                )
            ),

            "distance_from_left_normalized": (
                self._normalize(
                    distance_from_left,
                    max_edge_distance,
                )
            ),

            "distance_from_right_normalized": (
                self._normalize(
                    distance_from_right,
                    max_edge_distance,
                )
            ),

            "number_of_neighbors": float(
                number_of_neighbors
            ),

            "number_of_diagonal_neighbors": float(
                number_of_diagonal_neighbors
            ),

            "number_of_horizontal_neighbors": float(
                number_of_horizontal_neighbors
            ),

            "number_of_vertical_neighbors": float(
                number_of_vertical_neighbors
            ),
        }


# ============================================================
# MODULE-LEVEL COMPATIBILITY
# ============================================================


FEATURE_NAMES = (
    MLFeatureBuilder.FEATURE_NAMES
)
 
