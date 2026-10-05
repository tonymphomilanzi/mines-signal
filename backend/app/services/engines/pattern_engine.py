from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Iterable

from sqlalchemy.orm import Session

from app.models.model import SignalModel
from app.models.result import SignalResult
from app.models.signal import Signal


# ============================================================
# ENGINE PREDICTION
# ============================================================


@dataclass
class EnginePrediction:
    safe_positions: list[int]
    predicted_mine_positions: list[int]
    confidence: float | None


# ============================================================
# PATTERN ENGINE
# ============================================================


class PatternEngine:
    """
    Pattern-based prediction engine.

    Important:
        The engine does NOT produce a guaranteed probability
        of winning or correctness.

        The returned confidence value represents MODEL
        CONFIDENCE: how strongly the scoring system supports
        the selected positions based on historical evidence,
        score strength, separation and consistency.

    Board positions are always 1-based.

    Example for a 5x5 board:

        1   2   3   4   5
        6   7   8   9   10
        11  12  13  14  15
        16  17  18  19  20
        21  22  23  24  25
    """

    name = "pattern"
    version = "2.0.0"

    # ------------------------------------------------------------
    # SELECTION SETTINGS
    # ------------------------------------------------------------

    # We now return 5 safe positions instead of 8.
    SAFE_COUNT = 5

    # Keep a relatively small candidate pool so that the final
    # positions are concentrated around the strongest evidence.
    SAFE_CANDIDATE_POOL = 8
    MINE_CANDIDATE_POOL = 8

    MIN_SAFE_CANDIDATE_POOL = 5
    MIN_MINE_CANDIDATE_POOL = 3

    # Higher power means stronger preference for higher-scoring
    # candidates during weighted random selection.
    SAFE_RANDOM_WEIGHT_POWER = 4.0
    MINE_RANDOM_WEIGHT_POWER = 3.0

    # ------------------------------------------------------------
    # RANDOM SOURCE
    # ------------------------------------------------------------

    _random = random.SystemRandom()

    # ============================================================
    # PREDICT
    # ============================================================

    def predict(
        self,
        db: Session,
        signal: Signal,
        model: SignalModel,
        historical_results: list[SignalResult] | None = None,
    ) -> EnginePrediction:
        """
        Generate a prediction for a signal.

        Historical results are used to calculate pattern scores.

        Randomness is deliberately applied only during the final
        candidate-selection stage.

        The underlying evidence and scoring remain deterministic
        for the same historical data.
        """

        self._validate_configuration(
            board_size=signal.board_size,
            mine_count=signal.mine_count,
            model=model,
        )

        if historical_results is None:
            historical_results = self._load_historical_results(
                db=db,
                signal=signal,
            )

        # --------------------------------------------------------
        # NO HISTORY
        # --------------------------------------------------------

        if not historical_results:
            return self._fallback_prediction(
                board_size=signal.board_size,
                mine_count=signal.mine_count,
            )

        # --------------------------------------------------------
        # PATTERN STATISTICS
        # --------------------------------------------------------

        safe_position_frequency = self._position_frequency(
            historical_results,
            attribute="actual_safe_positions",
        )

        mine_position_frequency = self._position_frequency(
            historical_results,
            attribute="actual_mine_positions",
        )

        safe_pair_frequency = self._combination_frequency(
            historical_results,
            attribute="actual_safe_positions",
            combination_size=2,
        )

        mine_pair_frequency = self._combination_frequency(
            historical_results,
            attribute="actual_mine_positions",
            combination_size=2,
        )

        safe_triplet_frequency = self._combination_frequency(
            historical_results,
            attribute="actual_safe_positions",
            combination_size=3,
        )

        mine_triplet_frequency = self._combination_frequency(
            historical_results,
            attribute="actual_mine_positions",
            combination_size=3,
        )

        safe_row_frequency = self._row_pattern_frequency(
            historical_results,
            attribute="actual_safe_positions",
            board_size=signal.board_size,
        )

        mine_row_frequency = self._row_pattern_frequency(
            historical_results,
            attribute="actual_mine_positions",
            board_size=signal.board_size,
        )

        safe_column_frequency = self._column_pattern_frequency(
            historical_results,
            attribute="actual_safe_positions",
            board_size=signal.board_size,
        )

        mine_column_frequency = self._column_pattern_frequency(
            historical_results,
            attribute="actual_mine_positions",
            board_size=signal.board_size,
        )

        safe_structure_frequency = (
            self._structural_pattern_frequency(
                historical_results,
                attribute="actual_safe_positions",
                board_size=signal.board_size,
            )
        )

        mine_structure_frequency = (
            self._structural_pattern_frequency(
                historical_results,
                attribute="actual_mine_positions",
                board_size=signal.board_size,
            )
        )

        history_count = len(historical_results)

        # --------------------------------------------------------
        # SCORE EVERY POSITION
        # --------------------------------------------------------

        total_cells = (
            signal.board_size *
            signal.board_size
        )

        safe_scores: dict[int, float] = {}
        mine_scores: dict[int, float] = {}

        for position in range(
            1,
            total_cells + 1,
        ):
            safe_scores[position] = (
                self._calculate_safe_score(
                    position=position,
                    board_size=signal.board_size,
                    safe_position_frequency=safe_position_frequency,
                    mine_position_frequency=mine_position_frequency,
                    safe_pair_frequency=safe_pair_frequency,
                    safe_triplet_frequency=safe_triplet_frequency,
                    safe_row_frequency=safe_row_frequency,
                    safe_column_frequency=safe_column_frequency,
                    safe_structure_frequency=safe_structure_frequency,
                    historical_count=history_count,
                )
            )

            mine_scores[position] = (
                self._calculate_mine_score(
                    position=position,
                    board_size=signal.board_size,
                    safe_position_frequency=safe_position_frequency,
                    mine_position_frequency=mine_position_frequency,
                    mine_pair_frequency=mine_pair_frequency,
                    mine_triplet_frequency=mine_triplet_frequency,
                    mine_row_frequency=mine_row_frequency,
                    mine_column_frequency=mine_column_frequency,
                    mine_structure_frequency=mine_structure_frequency,
                    historical_count=history_count,
                )
            )

        # --------------------------------------------------------
        # SORT CANDIDATES
        # --------------------------------------------------------

        safe_ranked = sorted(
            safe_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        mine_ranked = sorted(
            mine_scores.items(),
            key=lambda item: item[1],
            reverse=True,
        )

        # --------------------------------------------------------
        # SAFE CANDIDATE POOL
        # --------------------------------------------------------

        safe_pool_size = min(
            max(
                self.SAFE_CANDIDATE_POOL,
                self.MIN_SAFE_CANDIDATE_POOL,
            ),
            len(safe_ranked),
        )

        safe_candidates = safe_ranked[
            :safe_pool_size
        ]

        safe_count = min(
            self.SAFE_COUNT,
            total_cells - signal.mine_count,
        )

        selected_safe = self._weighted_select_positions(
            candidates=safe_candidates,
            count=safe_count,
            weight_power=self.SAFE_RANDOM_WEIGHT_POWER,
        )

        # --------------------------------------------------------
        # MINE CANDIDATES
        # --------------------------------------------------------

        available_mine_candidates = [
            item
            for item in mine_ranked
            if item[0] not in selected_safe
        ]

        mine_pool_size = min(
            max(
                self.MINE_CANDIDATE_POOL,
                self.MIN_MINE_CANDIDATE_POOL,
            ),
            len(available_mine_candidates),
        )

        mine_candidates = (
            available_mine_candidates[
                :mine_pool_size
            ]
        )

        if len(mine_candidates) < signal.mine_count:
            mine_candidates = available_mine_candidates

        selected_mines = self._weighted_select_positions(
            candidates=mine_candidates,
            count=signal.mine_count,
            weight_power=self.MINE_RANDOM_WEIGHT_POWER,
        )

        # --------------------------------------------------------
        # SAFETY CHECK
        # --------------------------------------------------------

        selected_mines = [
            position
            for position in selected_mines
            if position not in selected_safe
        ]

        if len(selected_mines) < signal.mine_count:
            remaining_mines = [
                position
                for position, _score in mine_ranked
                if (
                    position not in selected_safe
                    and position not in selected_mines
                )
            ]

            selected_mines.extend(
                remaining_mines[
                    :signal.mine_count
                    - len(selected_mines)
                ]
            )

        # --------------------------------------------------------
        # FINAL ORDER
        # --------------------------------------------------------

        selected_safe = sorted(
            selected_safe
        )

        selected_mines = sorted(
            selected_mines
        )

        # --------------------------------------------------------
        # MODEL CONFIDENCE
        # --------------------------------------------------------

        selected_safe_scores = [
            safe_scores[position]
            for position in selected_safe
        ]

        selected_mine_scores = [
            mine_scores[position]
            for position in selected_mines
        ]

        all_safe_scores = list(
            safe_scores.values()
        )

        all_mine_scores = list(
            mine_scores.values()
        )

        safe_confidence = (
            self._calculate_confidence(
                selected_positions=selected_safe,
                selected_scores=selected_safe_scores,
                candidate_scores=all_safe_scores,
                position_frequency=safe_position_frequency,
                historical_count=history_count,
                board_size=signal.board_size,
                expected_attribute="safe",
            )
        )

        mine_confidence = (
            self._calculate_confidence(
                selected_positions=selected_mines,
                selected_scores=selected_mine_scores,
                candidate_scores=all_mine_scores,
                position_frequency=mine_position_frequency,
                historical_count=history_count,
                board_size=signal.board_size,
                expected_attribute="mine",
            )
        )

        # Safe predictions are the primary output of this engine,
        # therefore they receive greater influence over the final
        # model-confidence value.
        confidence = round(
            (
                (safe_confidence * 0.75)
                +
                (mine_confidence * 0.25)
            ),
            2,
        )

        return EnginePrediction(
            safe_positions=selected_safe,
            predicted_mine_positions=selected_mines,
            confidence=confidence,
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate_configuration(
        self,
        board_size: int,
        mine_count: int,
        model: SignalModel,
    ) -> None:
        if board_size <= 0:
            raise ValueError(
                "Board size must be greater than zero."
            )

        total_cells = (
            board_size *
            board_size
        )

        if mine_count <= 0:
            raise ValueError(
                "Mine count must be greater than zero."
            )

        if mine_count >= total_cells:
            raise ValueError(
                "Mine count must be smaller than the board size."
            )

        if model.board_size != board_size:
            raise ValueError(
                "The selected model does not support "
                "this signal's board size."
            )

    # ============================================================
    # HISTORICAL RESULTS
    # ============================================================

    def _load_historical_results(
        self,
        db: Session,
        signal: Signal,
    ) -> list[SignalResult]:
        """
        Load historical results matching the current board
        configuration.
        """

        from sqlalchemy import select

        statement = (
            select(SignalResult)
            .join(
                Signal,
                Signal.id == SignalResult.signal_id,
            )
            .where(
                Signal.board_size == signal.board_size,
                Signal.mine_count == signal.mine_count,
            )
            .order_by(
                SignalResult.recorded_at.asc()
            )
        )

        return list(
            db.scalars(statement).all()
        )

    # ============================================================
    # POSITION FREQUENCY
    # ============================================================

    def _position_frequency(
        self,
        results: Iterable[SignalResult],
        attribute: str,
    ) -> Counter[int]:
        counter: Counter[int] = Counter()

        for result in results:
            positions = getattr(
                result,
                attribute,
                None,
            )

            if not positions:
                continue

            for position in positions:
                counter[int(position)] += 1

        return counter

    # ============================================================
    # COMBINATION FREQUENCY
    # ============================================================

    def _combination_frequency(
        self,
        results: Iterable[SignalResult],
        attribute: str,
        combination_size: int,
    ) -> Counter[tuple[int, ...]]:
        counter: Counter[tuple[int, ...]] = Counter()

        for result in results:
            positions = getattr(
                result,
                attribute,
                None,
            )

            if not positions:
                continue

            normalized = sorted(
                {
                    int(position)
                    for position in positions
                }
            )

            if len(normalized) < combination_size:
                continue

            for combination in combinations(
                normalized,
                combination_size,
            ):
                counter[tuple(combination)] += 1

        return counter

    # ============================================================
    # ROW PATTERNS
    # ============================================================

    def _row_pattern_frequency(
        self,
        results: Iterable[SignalResult],
        attribute: str,
        board_size: int,
    ) -> Counter[int]:
        counter: Counter[int] = Counter()

        for result in results:
            positions = getattr(
                result,
                attribute,
                None,
            )

            if not positions:
                continue

            rows = {
                self._row_of_position(
                    int(position),
                    board_size,
                )
                for position in positions
            }

            for row in rows:
                counter[row] += 1

        return counter

    # ============================================================
    # COLUMN PATTERNS
    # ============================================================

    def _column_pattern_frequency(
        self,
        results: Iterable[SignalResult],
        attribute: str,
        board_size: int,
    ) -> Counter[int]:
        counter: Counter[int] = Counter()

        for result in results:
            positions = getattr(
                result,
                attribute,
                None,
            )

            if not positions:
                continue

            columns = {
                self._column_of_position(
                    int(position),
                    board_size,
                )
                for position in positions
            }

            for column in columns:
                counter[column] += 1

        return counter

    # ============================================================
    # STRUCTURAL PATTERNS
    # ============================================================

    def _structural_pattern_frequency(
        self,
        results: Iterable[SignalResult],
        attribute: str,
        board_size: int,
    ) -> Counter[str]:
        counter: Counter[str] = Counter()

        for result in results:
            positions = getattr(
                result,
                attribute,
                None,
            )

            if not positions:
                continue

            for position in positions:
                position = int(position)

                row = self._row_of_position(
                    position,
                    board_size,
                )

                column = self._column_of_position(
                    position,
                    board_size,
                )

                if row == column:
                    counter["main_diagonal"] += 1

                if row + column == board_size - 1:
                    counter["secondary_diagonal"] += 1

                if (
                    row in (
                        0,
                        board_size - 1,
                    )
                    and column in (
                        0,
                        board_size - 1,
                    )
                ):
                    counter["corner"] += 1

                if (
                    row == board_size // 2
                    and column == board_size // 2
                ):
                    counter["center"] += 1

                if (
                    row == 0
                    or row == board_size - 1
                    or column == 0
                    or column == board_size - 1
                ):
                    counter["edge"] += 1

        return counter

    # ============================================================
    # SAFE SCORE
    # ============================================================

    def _calculate_safe_score(
        self,
        position: int,
        board_size: int,
        safe_position_frequency: Counter[int],
        mine_position_frequency: Counter[int],
        safe_pair_frequency: Counter[tuple[int, ...]],
        safe_triplet_frequency: Counter[tuple[int, ...]],
        safe_row_frequency: Counter[int],
        safe_column_frequency: Counter[int],
        safe_structure_frequency: Counter[str],
        historical_count: int,
    ) -> float:
        """
        Calculate normalized safe evidence.

        Higher score means the historical evidence supports the
        position being safe more strongly.

        Components:

            +40% historical safe frequency
            -25% historical mine frequency
            +15% safe pair evidence
            +10% safe triplet evidence
            +05% row evidence
            +05% column evidence
        """

        if historical_count <= 0:
            return 0.0

        safe_frequency = (
            safe_position_frequency.get(
                position,
                0,
            )
            / historical_count
        )

        mine_frequency = (
            mine_position_frequency.get(
                position,
                0,
            )
            / historical_count
        )

        pair_score = self._normalized_position_combination_score(
            position=position,
            frequency=safe_pair_frequency,
            historical_count=historical_count,
        )

        triplet_score = (
            self._normalized_position_combination_score(
                position=position,
                frequency=safe_triplet_frequency,
                historical_count=historical_count,
            )
        )

        row_score = (
            safe_row_frequency.get(
                self._row_of_position(
                    position,
                    board_size,
                ),
                0,
            )
            / historical_count
        )

        column_score = (
            safe_column_frequency.get(
                self._column_of_position(
                    position,
                    board_size,
                ),
                0,
            )
            / historical_count
        )

        structure_score = (
            self._normalized_position_structure_score(
                position=position,
                board_size=board_size,
                frequency=safe_structure_frequency,
                historical_count=historical_count,
            )
        )

        score = (
            (safe_frequency * 0.40)
            - (mine_frequency * 0.25)
            + (pair_score * 0.15)
            + (triplet_score * 0.10)
            + (row_score * 0.05)
            + (column_score * 0.05)
            + (structure_score * 0.05)
        )

        return float(score)

    # ============================================================
    # MINE SCORE
    # ============================================================

    def _calculate_mine_score(
        self,
        position: int,
        board_size: int,
        safe_position_frequency: Counter[int],
        mine_position_frequency: Counter[int],
        mine_pair_frequency: Counter[tuple[int, ...]],
        mine_triplet_frequency: Counter[tuple[int, ...]],
        mine_row_frequency: Counter[int],
        mine_column_frequency: Counter[int],
        mine_structure_frequency: Counter[str],
        historical_count: int,
    ) -> float:
        """
        Calculate normalized mine evidence.
        """

        if historical_count <= 0:
            return 0.0

        mine_frequency = (
            mine_position_frequency.get(
                position,
                0,
            )
            / historical_count
        )

        safe_frequency = (
            safe_position_frequency.get(
                position,
                0,
            )
            / historical_count
        )

        pair_score = (
            self._normalized_position_combination_score(
                position=position,
                frequency=mine_pair_frequency,
                historical_count=historical_count,
            )
        )

        triplet_score = (
            self._normalized_position_combination_score(
                position=position,
                frequency=mine_triplet_frequency,
                historical_count=historical_count,
            )
        )

        row_score = (
            mine_row_frequency.get(
                self._row_of_position(
                    position,
                    board_size,
                ),
                0,
            )
            / historical_count
        )

        column_score = (
            mine_column_frequency.get(
                self._column_of_position(
                    position,
                    board_size,
                ),
                0,
            )
            / historical_count
        )

        structure_score = (
            self._normalized_position_structure_score(
                position=position,
                board_size=board_size,
                frequency=mine_structure_frequency,
                historical_count=historical_count,
            )
        )

        score = (
            (mine_frequency * 0.45)
            - (safe_frequency * 0.25)
            + (pair_score * 0.12)
            + (triplet_score * 0.08)
            + (row_score * 0.04)
            + (column_score * 0.04)
            + (structure_score * 0.03)
        )

        return float(score)

    # ============================================================
    # COMBINATION SCORE
    # ============================================================

    def _position_combination_score(
        self,
        position: int,
        frequency: Counter[tuple[int, ...]],
    ) -> float:
        score = 0.0

        for combination, count in frequency.items():
            if position in combination:
                score += float(count)

        return score

    # ============================================================
    # NORMALIZED COMBINATION SCORE
    # ============================================================

    def _normalized_position_combination_score(
        self,
        position: int,
        frequency: Counter[tuple[int, ...]],
        historical_count: int,
    ) -> float:
        if historical_count <= 0:
            return 0.0

        score = self._position_combination_score(
            position=position,
            frequency=frequency,
        )

        return min(
            score / historical_count,
            1.0,
        )

    # ============================================================
    # STRUCTURAL SCORE
    # ============================================================

    def _position_structure_score(
        self,
        position: int,
        board_size: int,
        frequency: Counter[str],
    ) -> float:
        row = self._row_of_position(
            position,
            board_size,
        )

        column = self._column_of_position(
            position,
            board_size,
        )

        score = 0.0

        if row == column:
            score += frequency.get(
                "main_diagonal",
                0,
            )

        if row + column == board_size - 1:
            score += frequency.get(
                "secondary_diagonal",
                0,
            )

        if (
            row in (
                0,
                board_size - 1,
            )
            and column in (
                0,
                board_size - 1,
            )
        ):
            score += frequency.get(
                "corner",
                0,
            )

        if (
            row == board_size // 2
            and column == board_size // 2
        ):
            score += frequency.get(
                "center",
                0,
            )

        if (
            row == 0
            or row == board_size - 1
            or column == 0
            or column == board_size - 1
        ):
            score += frequency.get(
                "edge",
                0,
            )

        return float(score)

    # ============================================================
    # NORMALIZED STRUCTURAL SCORE
    # ============================================================

    def _normalized_position_structure_score(
        self,
        position: int,
        board_size: int,
        frequency: Counter[str],
        historical_count: int,
    ) -> float:
        if historical_count <= 0:
            return 0.0

        score = self._position_structure_score(
            position=position,
            board_size=board_size,
            frequency=frequency,
        )

        return min(
            score / historical_count,
            1.0,
        )

    # ============================================================
    # RANDOMIZED WEIGHTED SELECTION
    # ============================================================

    def _weighted_select_positions(
        self,
        candidates: list[tuple[int, float]],
        count: int,
        weight_power: float,
    ) -> list[int]:
        """
        Select positions randomly while strongly favoring
        stronger model-scored candidates.
        """

        if count <= 0 or not candidates:
            return []

        count = min(
            count,
            len(candidates),
        )

        remaining = list(candidates)
        selected: list[int] = []

        while (
            remaining
            and len(selected) < count
        ):
            index = self._weighted_index(
                remaining,
                weight_power,
            )

            position, _score = remaining.pop(
                index
            )

            selected.append(position)

        return selected

    # ============================================================
    # WEIGHTED RANDOM INDEX
    # ============================================================

    def _weighted_index(
        self,
        candidates: list[tuple[int, float]],
        weight_power: float,
    ) -> int:
        """
        Convert candidate scores into positive selection weights.

        Scores can be negative, so they are shifted into a
        positive range.

        A small epsilon is added so weak candidates can still
        occasionally appear, but the strongest candidates receive
        substantially greater probability.
        """

        if len(candidates) == 1:
            return 0

        scores = [
            float(score)
            for _position, score in candidates
        ]

        minimum_score = min(scores)
        maximum_score = max(scores)

        score_range = (
            maximum_score -
            minimum_score
        )

        if score_range <= 0:
            return self._random.randrange(
                len(candidates)
            )

        # Normalize into approximately 0.05 -> 1.0.
        normalized_weights = []

        for score in scores:
            normalized = (
                (score - minimum_score)
                / score_range
            )

            normalized = (
                0.05 +
                (normalized * 0.95)
            )

            normalized_weights.append(
                normalized
            )

        weights = [
            max(
                weight ** weight_power,
                0.000001,
            )
            for weight in normalized_weights
        ]

        total_weight = sum(weights)

        if total_weight <= 0:
            return self._random.randrange(
                len(candidates)
            )

        target = (
            self._random.random() *
            total_weight
        )

        cumulative = 0.0

        for index, weight in enumerate(weights):
            cumulative += weight

            if target <= cumulative:
                return index

        return len(candidates) - 1

    # ============================================================
    # MODEL CONFIDENCE
    # ============================================================

    def _calculate_confidence(
        self,
        selected_positions: list[int],
        selected_scores: list[float],
        candidate_scores: list[float],
        position_frequency: Counter[int],
        historical_count: int,
        board_size: int,
        expected_attribute: str,
    ) -> float:
        """
        Calculate MODEL CONFIDENCE.

        This is NOT a probability of winning.

        The score measures how concentrated and consistent the
        model evidence is around the selected positions.

        Components:

            35% score strength
            25% separation from the board
            20% historical consistency
            10% top-candidate concentration
            10% selection stability
        """

        if not selected_scores:
            return 0.0

        if not candidate_scores:
            return 0.0

        # --------------------------------------------------------
        # SCORE STRENGTH
        # --------------------------------------------------------

        minimum_score = min(
            candidate_scores
        )

        maximum_score = max(
            candidate_scores
        )

        score_range = (
            maximum_score -
            minimum_score
        )

        if score_range <= 0:
            score_strength = 0.50

        else:
            normalized_selected = [
                (
                    score -
                    minimum_score
                )
                / score_range
                for score in selected_scores
            ]

            score_strength = (
                sum(normalized_selected)
                / len(normalized_selected)
            )

        # --------------------------------------------------------
        # SEPARATION
        # --------------------------------------------------------

        sorted_scores = sorted(
            candidate_scores,
            reverse=True,
        )

        median_score = self._median(
            sorted_scores
        )

        average_selected_score = (
            sum(selected_scores)
            / len(selected_scores)
        )

        if score_range <= 0:
            separation = 0.50

        else:
            raw_separation = (
                average_selected_score -
                median_score
            ) / score_range

            separation = (
                0.50 +
                raw_separation
            )

            separation = max(
                0.0,
                min(
                    1.0,
                    separation,
                ),
            )

        # --------------------------------------------------------
        # HISTORICAL CONSISTENCY
        # --------------------------------------------------------

        if historical_count <= 0:
            historical_consistency = 0.0

        else:
            selected_history_rates = []

            for position in selected_positions:
                frequency = (
                    position_frequency.get(
                        position,
                        0,
                    )
                    / historical_count
                )

                if expected_attribute == "safe":
                    # Safe frequency itself is the positive
                    # historical evidence.
                    rate = frequency
                else:
                    # Mine frequency is the positive evidence
                    # for predicted mine positions.
                    rate = frequency

                selected_history_rates.append(
                    rate
                )

            if selected_history_rates:
                historical_consistency = (
                    sum(selected_history_rates)
                    / len(selected_history_rates)
                )
            else:
                historical_consistency = 0.0

        # --------------------------------------------------------
        # TOP-CANDIDATE CONCENTRATION
        # --------------------------------------------------------

        top_count = min(
            len(candidate_scores),
            max(
                3,
                len(selected_scores),
            ),
        )

        top_scores = sorted_scores[
            :top_count
        ]

        if top_scores:
            top_average = (
                sum(top_scores)
                / len(top_scores)
            )

            if score_range > 0:
                top_concentration = (
                    (
                        top_average -
                        minimum_score
                    )
                    / score_range
                )
            else:
                top_concentration = 0.50
        else:
            top_concentration = 0.0

        top_concentration = max(
            0.0,
            min(
                1.0,
                top_concentration,
            ),
        )

        # --------------------------------------------------------
        # SELECTION STABILITY
        # --------------------------------------------------------
        #
        # The smaller the distance between selected candidates
        # and the strongest candidates, the more stable the
        # prediction is.

        ranked_positions = sorted(
            range(
                len(candidate_scores)
            ),
            key=lambda index:
                candidate_scores[index],
            reverse=True,
        )

        score_rank_map = {
            position_index: rank
            for rank, position_index
            in enumerate(ranked_positions)
        }

        # Reconstruct ranks from scores rather than positions.
        selected_rank_scores = []

        for selected_score in selected_scores:
            rank = 1

            for candidate_score in sorted_scores:
                if selected_score < candidate_score:
                    rank += 1

            selected_rank_scores.append(
                rank
            )

        average_rank = (
            sum(selected_rank_scores)
            / len(selected_rank_scores)
        )

        rank_limit = max(
            len(candidate_scores),
            1,
        )

        rank_quality = (
            1.0 -
            (
                (average_rank - 1)
                / rank_limit
            )
        )

        selection_stability = max(
            0.0,
            min(
                1.0,
                rank_quality,
            ),
        )

        # --------------------------------------------------------
        # HISTORY RELIABILITY
        # --------------------------------------------------------
        #
        # Very small histories should not be allowed to produce
        # extremely strong confidence.

        if historical_count < 5:
            history_reliability = 0.25

        elif historical_count < 10:
            history_reliability = 0.45

        elif historical_count < 20:
            history_reliability = 0.65

        elif historical_count < 35:
            history_reliability = 0.82

        else:
            history_reliability = 1.0

        # --------------------------------------------------------
        # COMBINE
        # --------------------------------------------------------

        raw_confidence = (
            (score_strength * 0.35)
            +
            (separation * 0.25)
            +
            (historical_consistency * 0.20)
            +
            (top_concentration * 0.10)
            +
            (selection_stability * 0.10)
        )

        # Apply reliability of the historical sample.
        #
        # We do not want 3 or 4 historical results to suddenly
        # produce an apparently authoritative 95% confidence.

        reliability_adjusted = (
            raw_confidence *
            (
                0.70 +
                (
                    history_reliability *
                    0.30
                )
            )
        )

        confidence_percentage = (
            reliability_adjusted *
            100.0
        )

        return round(
            max(
                0.0,
                min(
                    100.0,
                    confidence_percentage,
                ),
            ),
            2,
        )

    # ============================================================
    # MEDIAN
    # ============================================================

    def _median(
        self,
        values: list[float],
    ) -> float:
        if not values:
            return 0.0

        ordered = sorted(values)
        length = len(ordered)

        middle = length // 2

        if length % 2 == 0:
            return (
                ordered[middle - 1]
                +
                ordered[middle]
            ) / 2.0

        return ordered[middle]

    # ============================================================
    # FALLBACK PREDICTION
    # ============================================================

    def _fallback_prediction(
        self,
        board_size: int,
        mine_count: int,
    ) -> EnginePrediction:
        """
        Generate a randomized prediction when there are no
        historical results yet.

        The system returns five safe positions, but confidence
        remains intentionally conservative because there is no
        historical evidence yet.
        """

        total_cells = (
            board_size *
            board_size
        )

        positions = list(
            range(
                1,
                total_cells + 1,
            )
        )

        self._random.shuffle(
            positions
        )

        safe_count = min(
            self.SAFE_COUNT,
            total_cells - mine_count,
        )

        safe_positions = positions[
            :safe_count
        ]

        remaining = [
            position
            for position in positions
            if position not in safe_positions
        ]

        self._random.shuffle(
            remaining
        )

        predicted_mine_positions = remaining[
            :mine_count
        ]

        safe_positions = sorted(
            safe_positions
        )

        predicted_mine_positions = sorted(
            predicted_mine_positions
        )

        return EnginePrediction(
            safe_positions=safe_positions,
            predicted_mine_positions=(
                predicted_mine_positions
            ),
            # No historical evidence means there is no basis
            # for a high model-confidence value.
            confidence=35.0,
        )

    # ============================================================
    # BOARD HELPERS
    # ============================================================

    def _row_of_position(
        self,
        position: int,
        board_size: int,
    ) -> int:
        """
        Return zero-based row for a 1-based board position.
        """

        return (
            (position - 1)
            //
            board_size
        )

    def _column_of_position(
        self,
        position: int,
        board_size: int,
    ) -> int:
        """
        Return zero-based column for a 1-based board position.
        """

        return (
            (position - 1)
            %
            board_size
        )
 
