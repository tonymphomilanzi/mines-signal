from __future__ import annotations

from collections import Counter
from itertools import combinations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.result import ResultStatus, SignalResult
from app.models.signal import Signal


class PatternDiagnosticsService:
    """
    Explainable diagnostics for PatternEngine.

    IMPORTANT:

    The scoring formulas in this service intentionally mirror
    PatternEngine exactly.

    This service does not modify:
        - signals
        - predictions
        - models
        - results

    It only analyzes historical completed results and exposes
    the individual components used by PatternEngine.
    """

    # ============================================================
    # HISTORICAL RESULTS
    # ============================================================

    def get_historical_results(
        self,
        db: Session,
        board_size: int,
        mine_count: int,
    ) -> list[SignalResult]:

        statement = (
            select(SignalResult)
            .join(
                Signal,
                Signal.id == SignalResult.signal_id,
            )
            .where(
                Signal.board_size == board_size,
                Signal.mine_count == mine_count,
                SignalResult.status.in_(
                    [
                        ResultStatus.SUCCESS,
                        ResultStatus.FAILED,
                    ]
                ),
            )
            .order_by(
                SignalResult.recorded_at.asc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    # ============================================================
    # POSITION HELPERS
    # ============================================================

    def get_row(
        self,
        position: int,
        board_size: int,
    ) -> int:

        return (
            (position - 1)
            // board_size
        ) + 1

    def get_column(
        self,
        position: int,
        board_size: int,
    ) -> int:

        return (
            (position - 1)
            % board_size
        ) + 1

    def get_structure(
        self,
        position: int,
        board_size: int,
    ) -> str:

        row = self.get_row(
            position,
            board_size,
        )

        column = self.get_column(
            position,
            board_size,
        )

        last = board_size

        is_corner = (
            row in (1, last)
            and column in (1, last)
        )

        if is_corner:
            return "corner"

        is_edge = (
            row == 1
            or row == last
            or column == 1
            or column == last
        )

        if is_edge:
            return "edge"

        return "center"

    # ============================================================
    # POSITION FREQUENCIES
    # ============================================================

    def build_position_counters(
        self,
        historical_results: list[SignalResult],
    ) -> tuple[
        Counter[int],
        Counter[int],
    ]:

        mine_counter: Counter[int] = Counter()
        safe_counter: Counter[int] = Counter()

        for result in historical_results:

            actual_mines = set(
                result.actual_mine_positions
                or []
            )

            actual_safe = set(
                result.actual_safe_positions
                or []
            )

            mine_counter.update(
                actual_mines
            )

            safe_counter.update(
                actual_safe
            )

        return (
            mine_counter,
            safe_counter,
        )

    def calculate_position_mine_frequency(
        self,
        mine_counter: Counter[int],
        total_results: int,
    ) -> dict[int, float]:

        if total_results <= 0:
            return {}

        return {
            position: count / total_results
            for position, count
            in mine_counter.items()
        }

    def calculate_position_safe_frequency(
        self,
        safe_counter: Counter[int],
        total_results: int,
    ) -> dict[int, float]:

        if total_results <= 0:
            return {}

        return {
            position: count / total_results
            for position, count
            in safe_counter.items()
        }

    # ============================================================
    # PAIRS
    # ============================================================

    def build_pair_counter(
        self,
        historical_results: list[SignalResult],
    ) -> Counter[tuple[int, int]]:

        counter: Counter[
            tuple[int, int]
        ] = Counter()

        for result in historical_results:

            mines = sorted(
                set(
                    result.actual_mine_positions
                    or []
                )
            )

            for pair in combinations(
                mines,
                2,
            ):
                counter[pair] += 1

        return counter

    def calculate_pair_frequency(
        self,
        pair_counter: Counter[
            tuple[int, int]
        ],
        total_results: int,
    ) -> dict[
        tuple[int, int],
        float,
    ]:

        if total_results <= 0:
            return {}

        return {
            pair: count / total_results
            for pair, count
            in pair_counter.items()
        }

    # ============================================================
    # TRIPLETS
    # ============================================================

    def build_triplet_counter(
        self,
        historical_results: list[SignalResult],
    ) -> Counter[
        tuple[int, int, int]
    ]:

        counter: Counter[
            tuple[int, int, int]
        ] = Counter()

        for result in historical_results:

            mines = sorted(
                set(
                    result.actual_mine_positions
                    or []
                )
            )

            for triplet in combinations(
                mines,
                3,
            ):
                counter[triplet] += 1

        return counter

    def calculate_triplet_frequency(
        self,
        triplet_counter: Counter[
            tuple[int, int, int]
        ],
        total_results: int,
    ) -> dict[
        tuple[int, int, int],
        float,
    ]:

        if total_results <= 0:
            return {}

        return {
            triplet: count / total_results
            for triplet, count
            in triplet_counter.items()
        }

    # ============================================================
    # ROW / COLUMN FREQUENCY
    #
    # IMPORTANT:
    # These intentionally match PatternEngine.
    #
    # They are proportions of ALL historical mine
    # occurrences, not percentages of cells in the row.
    # ============================================================

    def build_row_column_counters(
        self,
        historical_results: list[SignalResult],
        board_size: int,
    ) -> tuple[
        Counter[int],
        Counter[int],
        Counter[int],
        Counter[int],
    ]:

        row_mines: Counter[int] = Counter()
        row_safe: Counter[int] = Counter()

        column_mines: Counter[int] = Counter()
        column_safe: Counter[int] = Counter()

        for result in historical_results:

            mines = set(
                result.actual_mine_positions
                or []
            )

            safe = set(
                result.actual_safe_positions
                or []
            )

            for position in mines:

                row = self.get_row(
                    position,
                    board_size,
                )

                column = self.get_column(
                    position,
                    board_size,
                )

                row_mines[row] += 1
                column_mines[column] += 1

            for position in safe:

                row = self.get_row(
                    position,
                    board_size,
                )

                column = self.get_column(
                    position,
                    board_size,
                )

                row_safe[row] += 1
                column_safe[column] += 1

        return (
            row_mines,
            row_safe,
            column_mines,
            column_safe,
        )

    def calculate_row_frequency(
        self,
        historical_results: list[SignalResult],
        board_size: int,
    ) -> dict[int, float]:

        row_counts: Counter[int] = Counter()

        total_mines = 0

        for result in historical_results:

            for position in (
                result.actual_mine_positions
                or []
            ):

                row = self.get_row(
                    position,
                    board_size,
                )

                row_counts[row] += 1
                total_mines += 1

        if total_mines == 0:
            return {}

        return {
            row: count / total_mines
            for row, count
            in row_counts.items()
        }

    def calculate_column_frequency(
        self,
        historical_results: list[SignalResult],
        board_size: int,
    ) -> dict[int, float]:

        column_counts: Counter[int] = Counter()

        total_mines = 0

        for result in historical_results:

            for position in (
                result.actual_mine_positions
                or []
            ):

                column = self.get_column(
                    position,
                    board_size,
                )

                column_counts[column] += 1
                total_mines += 1

        if total_mines == 0:
            return {}

        return {
            column: count / total_mines
            for column, count
            in column_counts.items()
        }

    # ============================================================
    # STRUCTURE FREQUENCY
    # ============================================================

    def calculate_structural_frequency(
        self,
        historical_results: list[SignalResult],
        board_size: int,
    ) -> dict[str, float]:

        structure_counts: Counter[str] = (
            Counter()
        )

        total_mines = 0

        for result in historical_results:

            for position in (
                result.actual_mine_positions
                or []
            ):

                structure = self.get_structure(
                    position,
                    board_size,
                )

                structure_counts[
                    structure
                ] += 1

                total_mines += 1

        if total_mines == 0:
            return {}

        return {
            structure: count / total_mines
            for structure, count
            in structure_counts.items()
        }

    # ============================================================
    # BEST PAIR
    #
    # EXACT COPY OF PatternEngine LOGIC
    # ============================================================

    def best_pair_score(
        self,
        position: int,
        pair_frequency: dict[
            tuple[int, int],
            float,
        ],
    ) -> float:

        matching_scores = [
            frequency
            for pair, frequency
            in pair_frequency.items()
            if position in pair
        ]

        if not matching_scores:
            return 0.0

        return max(
            matching_scores
        )

    # ============================================================
    # BEST TRIPLET
    #
    # EXACT COPY OF PatternEngine LOGIC
    # ============================================================

    def best_triplet_score(
        self,
        position: int,
        triplet_frequency: dict[
            tuple[int, int, int],
            float,
        ],
    ) -> float:

        matching_scores = [
            frequency
            for triplet, frequency
            in triplet_frequency.items()
            if position in triplet
        ]

        if not matching_scores:
            return 0.0

        return max(
            matching_scores
        )

    # ============================================================
    # EXACT SAFE SCORE
    #
    # Mirrors PatternEngine._calculate_safe_score()
    # ============================================================

    def calculate_safe_score(
        self,
        position: int,
        board_size: int,
        position_safe_frequency: dict[
            int,
            float,
        ],
        position_mine_frequency: dict[
            int,
            float,
        ],
        row_frequency: dict[int, float],
        column_frequency: dict[int, float],
        structural_frequency: dict[
            str,
            float,
        ],
    ) -> dict:

        safe_frequency = (
            position_safe_frequency.get(
                position,
                0.0,
            )
        )

        mine_frequency = (
            position_mine_frequency.get(
                position,
                0.0,
            )
        )

        row = self.get_row(
            position,
            board_size,
        )

        column = self.get_column(
            position,
            board_size,
        )

        structure = self.get_structure(
            position,
            board_size,
        )

        row_mine_frequency = (
            row_frequency.get(
                row,
                0.0,
            )
        )

        column_mine_frequency = (
            column_frequency.get(
                column,
                0.0,
            )
        )

        structural_mine_frequency = (
            structural_frequency.get(
                structure,
                0.0,
            )
        )

        # Exact PatternEngine components

        safe_position_component = (
            safe_frequency * 0.45
        )

        safe_mine_penalty_component = (
            mine_frequency * 0.30
        )

        safe_row_penalty_component = (
            row_mine_frequency * 0.10
        )

        safe_column_penalty_component = (
            column_mine_frequency * 0.10
        )

        safe_structure_penalty_component = (
            structural_mine_frequency * 0.05
        )

        score = (
            safe_position_component
            - safe_mine_penalty_component
            - safe_row_penalty_component
            - safe_column_penalty_component
            - safe_structure_penalty_component
        )

        return {
            "safe_position_component":
                safe_position_component,

            "safe_mine_penalty_component":
                safe_mine_penalty_component,

            "safe_row_penalty_component":
                safe_row_penalty_component,

            "safe_column_penalty_component":
                safe_column_penalty_component,

            "safe_structure_penalty_component":
                safe_structure_penalty_component,

            "safe_score":
                score,
        }

    # ============================================================
    # EXACT MINE SCORE
    #
    # Mirrors PatternEngine._calculate_mine_score()
    # ============================================================

    def calculate_mine_score(
        self,
        position: int,
        board_size: int,
        position_mine_frequency: dict[
            int,
            float,
        ],
        position_safe_frequency: dict[
            int,
            float,
        ],
        pair_frequency: dict[
            tuple[int, int],
            float,
        ],
        triplet_frequency: dict[
            tuple[int, int, int],
            float,
        ],
        row_frequency: dict[int, float],
        column_frequency: dict[int, float],
        structural_frequency: dict[
            str,
            float,
        ],
    ) -> dict:

        mine_frequency = (
            position_mine_frequency.get(
                position,
                0.0,
            )
        )

        safe_frequency = (
            position_safe_frequency.get(
                position,
                0.0,
            )
        )

        row = self.get_row(
            position,
            board_size,
        )

        column = self.get_column(
            position,
            board_size,
        )

        structure = self.get_structure(
            position,
            board_size,
        )

        row_frequency_score = (
            row_frequency.get(
                row,
                0.0,
            )
        )

        column_frequency_score = (
            column_frequency.get(
                column,
                0.0,
            )
        )

        structural_frequency_score = (
            structural_frequency.get(
                structure,
                0.0,
            )
        )

        best_pair_frequency = (
            self.best_pair_score(
                position=position,
                pair_frequency=pair_frequency,
            )
        )

        best_triplet_frequency = (
            self.best_triplet_score(
                position=position,
                triplet_frequency=triplet_frequency,
            )
        )

        # Exact PatternEngine components

        mine_position_component = (
            mine_frequency * 0.45
        )

        mine_safe_penalty_component = (
            safe_frequency * 0.20
        )

        mine_pair_component = (
            best_pair_frequency * 0.15
        )

        mine_triplet_component = (
            best_triplet_frequency * 0.10
        )

        mine_row_component = (
            row_frequency_score * 0.04
        )

        mine_column_component = (
            column_frequency_score * 0.04
        )

        mine_structure_component = (
            structural_frequency_score * 0.02
        )

        score = (
            mine_position_component
            - mine_safe_penalty_component
            + mine_pair_component
            + mine_triplet_component
            + mine_row_component
            + mine_column_component
            + mine_structure_component
        )

        return {
            "mine_position_component":
                mine_position_component,

            "mine_safe_penalty_component":
                mine_safe_penalty_component,

            "mine_pair_component":
                mine_pair_component,

            "mine_triplet_component":
                mine_triplet_component,

            "mine_row_component":
                mine_row_component,

            "mine_column_component":
                mine_column_component,

            "mine_structure_component":
                mine_structure_component,

            "best_pair_frequency":
                best_pair_frequency,

            "best_triplet_frequency":
                best_triplet_frequency,

            "mine_score":
                score,
        }

    # ============================================================
    # MAIN DIAGNOSTIC METHOD
    # ============================================================

    def diagnose(
        self,
        db: Session,
        board_size: int,
        mine_count: int,
    ) -> dict:

        historical_results = (
            self.get_historical_results(
                db=db,
                board_size=board_size,
                mine_count=mine_count,
            )
        )

        total_results = len(
            historical_results
        )

        if total_results == 0:
            return {
                "historical_results": [],
                "position_diagnostics": [],
                "repeated_pairs": [],
                "repeated_triplets": [],
                "row_patterns": [],
                "column_patterns": [],
                "structural_patterns": [],
            }

        # --------------------------------------------------------
        # HISTORICAL DATA
        # --------------------------------------------------------

        (
            mine_counter,
            safe_counter,
        ) = self.build_position_counters(
            historical_results
        )

        position_mine_frequency = (
            self.calculate_position_mine_frequency(
                mine_counter,
                total_results,
            )
        )

        position_safe_frequency = (
            self.calculate_position_safe_frequency(
                safe_counter,
                total_results,
            )
        )

        pair_counter = (
            self.build_pair_counter(
                historical_results
            )
        )

        pair_frequency = (
            self.calculate_pair_frequency(
                pair_counter,
                total_results,
            )
        )

        triplet_counter = (
            self.build_triplet_counter(
                historical_results
            )
        )

        triplet_frequency = (
            self.calculate_triplet_frequency(
                triplet_counter,
                total_results,
            )
        )

        row_frequency = (
            self.calculate_row_frequency(
                historical_results,
                board_size,
            )
        )

        column_frequency = (
            self.calculate_column_frequency(
                historical_results,
                board_size,
            )
        )

        structural_frequency = (
            self.calculate_structural_frequency(
                historical_results,
                board_size,
            )
        )

        # --------------------------------------------------------
        # POSITION DIAGNOSTICS
        # --------------------------------------------------------

        total_positions = (
            board_size * board_size
        )

        position_diagnostics = []

        for position in range(
            1,
            total_positions + 1,
        ):

            mine_frequency = (
                position_mine_frequency.get(
                    position,
                    0.0,
                )
            )

            safe_frequency = (
                position_safe_frequency.get(
                    position,
                    0.0,
                )
            )

            mine_count_for_position = (
                mine_counter[position]
            )

            safe_count_for_position = (
                safe_counter[position]
            )

            row = self.get_row(
                position,
                board_size,
            )

            column = self.get_column(
                position,
                board_size,
            )

            structure = self.get_structure(
                position,
                board_size,
            )

            safe_components = (
                self.calculate_safe_score(
                    position=position,
                    board_size=board_size,
                    position_safe_frequency=(
                        position_safe_frequency
                    ),
                    position_mine_frequency=(
                        position_mine_frequency
                    ),
                    row_frequency=row_frequency,
                    column_frequency=column_frequency,
                    structural_frequency=(
                        structural_frequency
                    ),
                )
            )

            mine_components = (
                self.calculate_mine_score(
                    position=position,
                    board_size=board_size,
                    position_mine_frequency=(
                        position_mine_frequency
                    ),
                    position_safe_frequency=(
                        position_safe_frequency
                    ),
                    pair_frequency=pair_frequency,
                    triplet_frequency=(
                        triplet_frequency
                    ),
                    row_frequency=row_frequency,
                    column_frequency=column_frequency,
                    structural_frequency=(
                        structural_frequency
                    ),
                )
            )

            safe_score = (
                safe_components[
                    "safe_score"
                ]
            )

            mine_score = (
                mine_components[
                    "mine_score"
                ]
            )

            # ----------------------------------------------------
            # Diagnostic decision
            #
            # This is descriptive only.
            # Production PatternEngine selects the top
            # ranked mine scores and top ranked safe scores.
            # ----------------------------------------------------

            if mine_score > safe_score:
                decision = "MINE"
            elif safe_score > mine_score:
                decision = "SAFE"
            else:
                decision = "NEUTRAL"

            position_diagnostics.append(
                {
                    "position": position,

                    "mine_frequency": round(
                        mine_frequency * 100,
                        2,
                    ),

                    "safe_frequency": round(
                        safe_frequency * 100,
                        2,
                    ),

                    "mine_count":
                        mine_count_for_position,

                    "safe_count":
                        safe_count_for_position,

                    "row": row,
                    "column": column,
                    "structure": structure,

                    "row_frequency": round(
                        row_frequency.get(
                            row,
                            0.0,
                        )
                        * 100,
                        2,
                    ),

                    "column_frequency": round(
                        column_frequency.get(
                            column,
                            0.0,
                        )
                        * 100,
                        2,
                    ),

                    "structure_frequency": round(
                        structural_frequency.get(
                            structure,
                            0.0,
                        )
                        * 100,
                        2,
                    ),

                    "best_pair_frequency": round(
                        mine_components[
                            "best_pair_frequency"
                        ]
                        * 100,
                        2,
                    ),

                    "best_triplet_frequency":
                        round(
                            mine_components[
                                "best_triplet_frequency"
                            ]
                            * 100,
                            2,
                        ),

                    # ------------------------------------------------
                    # SAFE COMPONENTS
                    # ------------------------------------------------

                    "safe_position_component":
                        round(
                            safe_components[
                                "safe_position_component"
                            ],
                            6,
                        ),

                    "safe_mine_penalty_component":
                        round(
                            safe_components[
                                "safe_mine_penalty_component"
                            ],
                            6,
                        ),

                    "safe_row_penalty_component":
                        round(
                            safe_components[
                                "safe_row_penalty_component"
                            ],
                            6,
                        ),

                    "safe_column_penalty_component":
                        round(
                            safe_components[
                                "safe_column_penalty_component"
                            ],
                            6,
                        ),

                    "safe_structure_penalty_component":
                        round(
                            safe_components[
                                "safe_structure_penalty_component"
                            ],
                            6,
                        ),

                    "safe_score": round(
                        safe_score,
                        6,
                    ),

                    # ------------------------------------------------
                    # MINE COMPONENTS
                    # ------------------------------------------------

                    "mine_position_component":
                        round(
                            mine_components[
                                "mine_position_component"
                            ],
                            6,
                        ),

                    "mine_safe_penalty_component":
                        round(
                            mine_components[
                                "mine_safe_penalty_component"
                            ],
                            6,
                        ),

                    "mine_pair_component":
                        round(
                            mine_components[
                                "mine_pair_component"
                            ],
                            6,
                        ),

                    "mine_triplet_component":
                        round(
                            mine_components[
                                "mine_triplet_component"
                            ],
                            6,
                        ),

                    "mine_row_component":
                        round(
                            mine_components[
                                "mine_row_component"
                            ],
                            6,
                        ),

                    "mine_column_component":
                        round(
                            mine_components[
                                "mine_column_component"
                            ],
                            6,
                        ),

                    "mine_structure_component":
                        round(
                            mine_components[
                                "mine_structure_component"
                            ],
                            6,
                        ),

                    "mine_score": round(
                        mine_score,
                        6,
                    ),

                    "decision": decision,
                }
            )

        # --------------------------------------------------------
        # REPEATED PAIRS
        # --------------------------------------------------------

        repeated_pairs = []

        for pair, count in (
            pair_counter.most_common()
        ):

            repeated_pairs.append(
                {
                    "positions": list(pair),

                    "occurrences": count,

                    "frequency": round(
                        (
                            count
                            / total_results
                        )
                        * 100,
                        2,
                    ),
                }
            )

        # --------------------------------------------------------
        # REPEATED TRIPLETS
        # --------------------------------------------------------

        repeated_triplets = []

        for triplet, count in (
            triplet_counter.most_common()
        ):

            repeated_triplets.append(
                {
                    "positions": list(
                        triplet
                    ),

                    "occurrences": count,

                    "frequency": round(
                        (
                            count
                            / total_results
                        )
                        * 100,
                        2,
                    ),
                }
            )

        # --------------------------------------------------------
        # ROW PATTERNS
        #
        # These exactly represent PatternEngine's
        # row_frequency calculation.
        # --------------------------------------------------------

        (
            row_mines,
            row_safe,
            column_mines,
            column_safe,
        ) = self.build_row_column_counters(
            historical_results,
            board_size,
        )

        row_patterns = []

        for row in range(
            1,
            board_size + 1,
        ):

            row_mine_frequency = (
                row_frequency.get(
                    row,
                    0.0,
                )
            )

            # Safe frequency here is retained as a
            # descriptive historical metric.
            #
            # It is NOT used by PatternEngine's
            # row scoring.

            total_safe = sum(
                row_safe.values()
            )

            row_safe_frequency = (
                row_safe[row]
                / total_safe
                if total_safe > 0
                else 0.0
            )

            row_patterns.append(
                {
                    "index": row,

                    "mine_frequency": round(
                        row_mine_frequency
                        * 100,
                        2,
                    ),

                    "safe_frequency": round(
                        row_safe_frequency
                        * 100,
                        2,
                    ),

                    "mine_count":
                        row_mines[row],

                    "safe_count":
                        row_safe[row],
                }
            )

        # --------------------------------------------------------
        # COLUMN PATTERNS
        # --------------------------------------------------------

        column_patterns = []

        for column in range(
            1,
            board_size + 1,
        ):

            column_mine_frequency = (
                column_frequency.get(
                    column,
                    0.0,
                )
            )

            total_safe = sum(
                column_safe.values()
            )

            column_safe_frequency = (
                column_safe[column]
                / total_safe
                if total_safe > 0
                else 0.0
            )

            column_patterns.append(
                {
                    "index": column,

                    "mine_frequency": round(
                        column_mine_frequency
                        * 100,
                        2,
                    ),

                    "safe_frequency": round(
                        column_safe_frequency
                        * 100,
                        2,
                    ),

                    "mine_count":
                        column_mines[column],

                    "safe_count":
                        column_safe[column],
                }
            )

        # --------------------------------------------------------
        # STRUCTURE PATTERNS
        # --------------------------------------------------------

        (
            structure_mines,
            structure_safe,
        ) = self.build_structure_counters(
            historical_results,
            board_size,
        )

        structural_patterns = []

        total_structure_mines = sum(
            structure_mines.values()
        )

        total_structure_safe = sum(
            structure_safe.values()
        )

        for structure in (
            "corner",
            "edge",
            "center",
        ):

            mine_frequency = (
                structure_mines[
                    structure
                ]
                / total_structure_mines
                if total_structure_mines > 0
                else 0.0
            )

            safe_frequency = (
                structure_safe[
                    structure
                ]
                / total_structure_safe
                if total_structure_safe > 0
                else 0.0
            )

            structural_patterns.append(
                {
                    "structure": structure,

                    "mine_frequency": round(
                        mine_frequency * 100,
                        2,
                    ),

                    "safe_frequency": round(
                        safe_frequency * 100,
                        2,
                    ),

                    "mine_count":
                        structure_mines[
                            structure
                        ],

                    "safe_count":
                        structure_safe[
                            structure
                        ],
                }
            )

        # --------------------------------------------------------
        # FINAL RESPONSE
        # --------------------------------------------------------

        return {
            "historical_results":
                historical_results,

            "position_diagnostics":
                position_diagnostics,

            "repeated_pairs":
                repeated_pairs,

            "repeated_triplets":
                repeated_triplets,

            "row_patterns":
                row_patterns,

            "column_patterns":
                column_patterns,

            "structural_patterns":
                structural_patterns,
        }


    # ============================================================
    # STRUCTURE COUNTERS
    # ============================================================

    def build_structure_counters(
        self,
        historical_results: list[SignalResult],
        board_size: int,
    ) -> tuple[
        Counter[str],
        Counter[str],
    ]:

        mine_counter: Counter[str] = Counter()
        safe_counter: Counter[str] = Counter()

        for result in historical_results:

            mines = set(
                result.actual_mine_positions
                or []
            )

            safe = set(
                result.actual_safe_positions
                or []
            )

            for position in mines:

                structure = self.get_structure(
                    position,
                    board_size,
                )

                mine_counter[
                    structure
                ] += 1

            for position in safe:

                structure = self.get_structure(
                    position,
                    board_size,
                )

                safe_counter[
                    structure
                ] += 1

        return (
            mine_counter,
            safe_counter,
        )


pattern_diagnostics_service = (
    PatternDiagnosticsService()
) 
