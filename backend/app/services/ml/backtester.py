from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.services.ml.dataset_builder import MLDatasetBuilder
from app.services.ml.predictor import MLPredictor


# ============================================================
# DATA CLASSES
# ============================================================


@dataclass
class GameBacktestResult:
    """
    Result of evaluating one historical game.
    """

    result_id: str
    signal_id: str

    board_size: int
    mine_count: int
    total_cells: int

    historical_games_used: int

    actual_safe_positions: list[int]
    actual_mine_positions: list[int]

    predicted_safe_positions: list[int]

    top_1_hit: bool
    top_3_hits: int
    top_5_hits: int

    safe_precision_at_1: float
    safe_precision_at_3: float
    safe_precision_at_5: float

    mine_hits_in_top_5: int

    generated_at: datetime | None = None
    recorded_at: datetime | None = None


@dataclass
class BacktestSummary:
    """
    Aggregate backtest statistics.
    """

    board_size: int
    mine_count: int
    total_cells: int

    games_evaluated: int

    average_top_1_precision: float
    average_top_3_precision: float
    average_top_5_precision: float

    top_1_hit_rate: float
    average_top_3_hits: float
    average_top_5_hits: float

    average_mine_hits_in_top_5: float

    model_name: str | None = None
    model_version: str | None = None
    feature_version: str | None = None
    model_path: str | None = None

    results: list[GameBacktestResult] | None = None


# ============================================================
# BACKTESTER
# ============================================================


class MLBacktester:
    """
    Chronological, leakage-safe ML backtester.

    For every target historical game:

        1. Only games before the target are used as history.
        2. The ML predictor ranks all board positions.
        3. Top SAFE positions are selected.
        4. The target game's actual labels are used only AFTER
           prediction to evaluate the result.

    Dataset labels:

        label = 1 -> SAFE
        label = 0 -> MINE
    """

    def __init__(
        self,
        db: Session,
        predictor: MLPredictor | None = None,
    ) -> None:
        self.db = db

        self.dataset_builder = MLDatasetBuilder(db)

        self.predictor = predictor or MLPredictor()

    # ========================================================
    # PUBLIC API
    # ========================================================

    def run(
        self,
        board_size: int = 5,
        mine_count: int = 3,
        min_historical_games: int = 5,
        top_n: int = 5,
    ) -> BacktestSummary:
        """
        Run chronological backtesting.

        Parameters
        ----------
        board_size:
            Board width/height.

        mine_count:
            Number of mines expected on the board.

        min_historical_games:
            Minimum number of previous completed games required
            before evaluating a target game.

        top_n:
            Number of SAFE positions to predict.

        Returns
        -------
        BacktestSummary
        """

        if board_size <= 0:
            raise ValueError(
                "board_size must be greater than zero."
            )

        if mine_count <= 0:
            raise ValueError(
                "mine_count must be greater than zero."
            )

        total_cells = board_size * board_size

        if mine_count >= total_cells:
            raise ValueError(
                "mine_count must be smaller than "
                "the total number of cells."
            )

        if min_historical_games < 0:
            raise ValueError(
                "min_historical_games cannot be negative."
            )

        if top_n <= 0:
            raise ValueError(
                "top_n must be greater than zero."
            )

        if top_n > total_cells:
            top_n = total_cells

        # ----------------------------------------------------
        # Build the complete chronological dataset.
        #
        # The dataset builder produces one record per board
        # position per historical game.
        # ----------------------------------------------------

        records = self.dataset_builder.build_feature_records(
            board_size=board_size,
            mine_count=mine_count,
            min_historical_games=0,
        )

        if not records:
            raise ValueError(
                "No historical ML dataset records were found."
            )

        # ----------------------------------------------------
        # Group records by historical game/result.
        # ----------------------------------------------------

        games = self._group_games(records)

        if not games:
            raise ValueError(
                "No complete historical games were found."
            )

        # ----------------------------------------------------
        # Sort games chronologically.
        # ----------------------------------------------------

        games.sort(
            key=self._game_sort_key,
        )

        backtest_results: list[GameBacktestResult] = []

        # ====================================================
        # CHRONOLOGICAL BACKTEST LOOP
        # ====================================================

        for game_index, game_records in enumerate(games):

            # -----------------------------------------------
            # We need enough previous games before this target.
            # -----------------------------------------------

            if game_index < min_historical_games:
                continue

            # -----------------------------------------------
            # Validate target game.
            # -----------------------------------------------

            self._validate_complete_game(
                game_records,
                board_size=board_size,
                mine_count=mine_count,
            )

            # -----------------------------------------------
            # Historical games are strictly BEFORE target.
            #
            # This is the key leakage-prevention rule.
            # -----------------------------------------------

            historical_games = games[:game_index]

            if len(historical_games) < min_historical_games:
                continue

            # -----------------------------------------------
            # Flatten previous games into historical records.
            # -----------------------------------------------

            historical_records: list[dict[str, Any]] = []

            for historical_game in historical_games:
                historical_records.extend(
                    historical_game
                )

            # -----------------------------------------------
            # Predict.
            #
            # IMPORTANT:
            #
            # MLPredictor.predict_board() expects the complete
            # historical records and builds the 25 prediction
            # records internally.
            #
            # The current target game's records are NOT passed
            # to the predictor.
            # -----------------------------------------------

            prediction = self.predictor.predict_board(
                board_size=board_size,
                mine_count=mine_count,
                historical_records=historical_records,
                top_n=top_n,
            )

            predicted_positions = (
                self._extract_prediction_positions(
                    prediction
                )
            )

            predicted_positions = predicted_positions[:top_n]

            # -----------------------------------------------
            # Evaluate target game against actual labels.
            #
            # This happens ONLY after prediction.
            # -----------------------------------------------

            result = self._evaluate_game(
                game_records=game_records,
                predicted_positions=predicted_positions,
                historical_games_used=len(
                    historical_games
                ),
            )

            backtest_results.append(result)

        if not backtest_results:
            raise ValueError(
                "No games were eligible for backtesting. "
                "Try reducing min_historical_games."
            )

        return self._build_summary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,
            results=backtest_results,
        )

    # ========================================================
    # GROUP GAMES
    # ========================================================

    def _group_games(
        self,
        records: list[dict[str, Any]],
    ) -> list[list[dict[str, Any]]]:
        """
        Group position records by result_id.

        Each complete game should contain exactly 25 records
        for a 5x5 board.
        """

        grouped: dict[str, list[dict[str, Any]]] = {}

        for record in records:

            result_id = record.get("result_id")

            if result_id is None:
                raise ValueError(
                    "Dataset record is missing result_id."
                )

            result_key = str(result_id)

            grouped.setdefault(
                result_key,
                [],
            ).append(record)

        return list(grouped.values())

    # ========================================================
    # GAME SORTING
    # ========================================================

    def _game_sort_key(
        self,
        game_records: list[dict[str, Any]],
    ) -> datetime:
        """
        Determine chronological order using recorded_at first,
        then generated_at.
        """

        first_record = game_records[0]

        recorded_at = first_record.get(
            "recorded_at"
        )

        if isinstance(recorded_at, datetime):
            return recorded_at

        generated_at = first_record.get(
            "generated_at"
        )

        if isinstance(generated_at, datetime):
            return generated_at

        # Fallback for unexpected/missing timestamps.
        return datetime.min

    # ========================================================
    # VALIDATE COMPLETE GAME
    # ========================================================

    def _validate_complete_game(
        self,
        game_records: list[dict[str, Any]],
        board_size: int,
        mine_count: int,
    ) -> None:
        """
        Validate that a historical game contains the complete
        board and the expected SAFE/MINE label distribution.

        Dataset label semantics:

            label = 1 -> SAFE
            label = 0 -> MINE
        """

        total_cells = board_size * board_size

        if len(game_records) != total_cells:
            result_id = game_records[0].get(
                "result_id"
            )

            raise ValueError(
                f"Historical game {result_id} has "
                f"{len(game_records)} records, expected "
                f"{total_cells}."
            )

        positions: set[int] = set()

        safe_positions: set[int] = set()
        mine_positions: set[int] = set()

        for record in game_records:

            # -----------------------------------------------
            # Validate position.
            # -----------------------------------------------

            if "position" not in record:
                raise ValueError(
                    "Historical dataset record is missing "
                    "'position'."
                )

            position = int(
                record["position"]
            )

            if position < 1 or position > total_cells:
                raise ValueError(
                    f"Invalid board position {position}. "
                    f"Expected 1-{total_cells}."
                )

            if position in positions:
                raise ValueError(
                    f"Duplicate board position {position} "
                    f"found in historical game."
                )

            positions.add(position)

            # -----------------------------------------------
            # Dataset semantics:
            #
            # label = 1 -> SAFE
            # label = 0 -> MINE
            # -----------------------------------------------

            if "label" not in record:
                raise ValueError(
                    f"Historical dataset record for position "
                    f"{position} is missing 'label'."
                )

            label = int(
                record["label"]
            )

            if label == 1:
                safe_positions.add(position)

            elif label == 0:
                mine_positions.add(position)

            else:
                raise ValueError(
                    f"Invalid label {label} for position "
                    f"{position}. Expected 0 or 1."
                )

        # ----------------------------------------------------
        # Validate complete board.
        # ----------------------------------------------------

        expected_positions = set(
            range(
                1,
                total_cells + 1,
            )
        )

        if positions != expected_positions:

            missing = sorted(
                expected_positions - positions
            )

            extra = sorted(
                positions - expected_positions
            )

            raise ValueError(
                "Historical game does not contain the complete "
                f"board. Missing={missing}, Extra={extra}"
            )

        # ----------------------------------------------------
        # Validate mine count.
        # ----------------------------------------------------

        if len(mine_positions) != mine_count:

            result_id = game_records[0].get(
                "result_id"
            )

            raise ValueError(
                f"Historical game {result_id} has "
                f"{len(mine_positions)} mines, expected "
                f"{mine_count}."
            )

        # ----------------------------------------------------
        # Validate SAFE count.
        # ----------------------------------------------------

        expected_safe_count = (
            total_cells - mine_count
        )

        if len(safe_positions) != expected_safe_count:

            result_id = game_records[0].get(
                "result_id"
            )

            raise ValueError(
                f"Historical game {result_id} has "
                f"{len(safe_positions)} safe positions, "
                f"expected {expected_safe_count}."
            )

    # ========================================================
    # EXTRACT PREDICTION POSITIONS
    # ========================================================

    def _extract_prediction_positions(
        self,
        prediction: Any,
    ) -> list[int]:
        """
        Extract ranked SAFE positions from MLPredictor.

        The current predictor exposes `top_positions`.
        """

        positions = getattr(
            prediction,
            "top_positions",
            None,
        )

        if positions is None:
            raise ValueError(
                "MLPredictor prediction does not expose "
                "'top_positions'."
            )

        return [
            int(position)
            for position in positions
        ]

    # ========================================================
    # EVALUATE GAME
    # ========================================================

    def _evaluate_game(
        self,
        game_records: list[dict[str, Any]],
        predicted_positions: list[int],
        historical_games_used: int,
    ) -> GameBacktestResult:
        """
        Evaluate ML predictions against the target game's
        actual labels.

        IMPORTANT:

        This method is called only AFTER prediction has already
        been generated.
        """

        first_record = game_records[0]

        result_id = str(
            first_record["result_id"]
        )

        signal_id = str(
            first_record["signal_id"]
        )

        actual_safe_positions = sorted(
            int(record["position"])
            for record in game_records
            if int(record["label"]) == 1
        )

        actual_mine_positions = sorted(
            int(record["position"])
            for record in game_records
            if int(record["label"]) == 0
        )

        actual_safe_set = set(
            actual_safe_positions
        )

        actual_mine_set = set(
            actual_mine_positions
        )

        # ----------------------------------------------------
        # Top-N predictions.
        # ----------------------------------------------------

        top_1 = predicted_positions[:1]
        top_3 = predicted_positions[:3]
        top_5 = predicted_positions[:5]

        # ----------------------------------------------------
        # SAFE hits.
        # ----------------------------------------------------

        top_1_safe_hits = sum(
            1
            for position in top_1
            if position in actual_safe_set
        )

        top_3_safe_hits = sum(
            1
            for position in top_3
            if position in actual_safe_set
        )

        top_5_safe_hits = sum(
            1
            for position in top_5
            if position in actual_safe_set
        )

        # ----------------------------------------------------
        # SAFE precision.
        # ----------------------------------------------------

        safe_precision_at_1 = (
            top_1_safe_hits / len(top_1)
            if top_1
            else 0.0
        )

        safe_precision_at_3 = (
            top_3_safe_hits / len(top_3)
            if top_3
            else 0.0
        )

        safe_precision_at_5 = (
            top_5_safe_hits / len(top_5)
            if top_5
            else 0.0
        )

        # ----------------------------------------------------
        # Top-1 hit.
        # ----------------------------------------------------

        top_1_hit = (
            bool(top_1)
            and top_1[0] in actual_safe_set
        )

        # ----------------------------------------------------
        # Mine hits inside predicted SAFE positions.
        #
        # Lower is better.
        # ----------------------------------------------------

        mine_hits_in_top_5 = sum(
            1
            for position in top_5
            if position in actual_mine_set
        )

        return GameBacktestResult(
            result_id=result_id,
            signal_id=signal_id,

            board_size=int(
                first_record["board_size"]
            ),

            mine_count=int(
                first_record["mine_count"]
            ),

            total_cells=int(
                first_record["total_cells"]
            ),

            historical_games_used=(
                historical_games_used
            ),

            actual_safe_positions=(
                actual_safe_positions
            ),

            actual_mine_positions=(
                actual_mine_positions
            ),

            predicted_safe_positions=(
                predicted_positions
            ),

            top_1_hit=top_1_hit,

            top_3_hits=top_3_safe_hits,

            top_5_hits=top_5_safe_hits,

            safe_precision_at_1=(
                safe_precision_at_1
            ),

            safe_precision_at_3=(
                safe_precision_at_3
            ),

            safe_precision_at_5=(
                safe_precision_at_5
            ),

            mine_hits_in_top_5=(
                mine_hits_in_top_5
            ),

            generated_at=first_record.get(
                "generated_at"
            ),

            recorded_at=first_record.get(
                "recorded_at"
            ),
        )

    # ========================================================
    # BUILD SUMMARY
    # ========================================================

    def _build_summary(
        self,
        board_size: int,
        mine_count: int,
        total_cells: int,
        results: list[GameBacktestResult],
    ) -> BacktestSummary:
        """
        Build aggregate backtest metrics.
        """

        games_evaluated = len(results)

        average_top_1_precision = self._average(
            result.safe_precision_at_1
            for result in results
        )

        average_top_3_precision = self._average(
            result.safe_precision_at_3
            for result in results
        )

        average_top_5_precision = self._average(
            result.safe_precision_at_5
            for result in results
        )

        top_1_hit_rate = self._average(
            1.0 if result.top_1_hit else 0.0
            for result in results
        )

        average_top_3_hits = self._average(
            result.top_3_hits
            for result in results
        )

        average_top_5_hits = self._average(
            result.top_5_hits
            for result in results
        )

        average_mine_hits_in_top_5 = self._average(
            result.mine_hits_in_top_5
            for result in results
        )

        return BacktestSummary(
            board_size=board_size,
            mine_count=mine_count,
            total_cells=total_cells,

            games_evaluated=games_evaluated,

            average_top_1_precision=(
                average_top_1_precision
            ),

            average_top_3_precision=(
                average_top_3_precision
            ),

            average_top_5_precision=(
                average_top_5_precision
            ),

            top_1_hit_rate=top_1_hit_rate,

            average_top_3_hits=(
                average_top_3_hits
            ),

            average_top_5_hits=(
                average_top_5_hits
            ),

            average_mine_hits_in_top_5=(
                average_mine_hits_in_top_5
            ),

            model_name=self._get_model_name(),

            model_version=self._get_model_version(),

            feature_version=self._get_feature_version(),

            model_path=self._get_model_path(),

            results=results,
        )

    # ========================================================
    # MODEL METADATA
    # ========================================================

    def _get_model_name(self) -> str | None:
        """
        MLPredictor does not expose model_name as an instance
        attribute, so read it from metadata when available.
        """

        metadata = getattr(
            self.predictor,
            "metadata",
            {},
        )

        if isinstance(metadata, dict):

            value = metadata.get(
                "model_name"
            )

            if value is not None:
                return str(value)

        value = getattr(
            self.predictor,
            "MODEL_NAME",
            None,
        )

        return (
            str(value)
            if value is not None
            else None
        )

    def _get_model_version(self) -> str | None:
        """
        Read model version from predictor metadata.
        """

        metadata = getattr(
            self.predictor,
            "metadata",
            {},
        )

        if isinstance(metadata, dict):

            value = metadata.get(
                "model_version"
            )

            if value is not None:
                return str(value)

        value = getattr(
            self.predictor,
            "DEFAULT_MODEL_VERSION",
            None,
        )

        return (
            str(value)
            if value is not None
            else None
        )

    def _get_feature_version(self) -> str | None:
        """
        Read the feature builder version from the predictor.
        """

        feature_builder = getattr(
            self.predictor,
            "feature_builder",
            None,
        )

        value = getattr(
            feature_builder,
            "VERSION",
            None,
        )

        return (
            str(value)
            if value is not None
            else None
        )

    def _get_model_path(self) -> str | None:
        value = getattr(
            self.predictor,
            "model_path",
            None,
        )

        return (
            str(value)
            if value is not None
            else None
        )

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _average(
        values: Any,
    ) -> float:
        values = list(values)

        if not values:
            return 0.0

        return sum(
            float(value)
            for value in values
        ) / len(values)
 
