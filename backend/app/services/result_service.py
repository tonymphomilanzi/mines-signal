import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.prediction import Prediction
from app.models.result import ResultStatus, SignalResult
from app.models.signal import Signal, SignalStatus
from app.services.prediction_service import get_latest_prediction


# ============================================================
# POSITION VALIDATION
# ============================================================


def _validate_positions(
    *,
    board_size: int,
    mine_count: int,
    actual_mine_positions: list[int],
    actual_safe_positions: list[int],
) -> None:
    """
    Validate that the submitted result represents a complete
    and valid board.

    Positions use a 1-based convention:

        5 × 5 board = positions 1 through 25

    Rules:
    - No duplicate mine positions.
    - No duplicate safe positions.
    - All positions must be inside the board.
    - Safe and mine positions cannot overlap.
    - Mine count must exactly match the signal configuration.
    - Safe count must equal board_size² - mine_count.
    - Every board position must be accounted for.
    """

    board_total = board_size * board_size

    mine_positions = list(actual_mine_positions)
    safe_positions = list(actual_safe_positions)

    # --------------------------------------------------------
    # DUPLICATES
    # --------------------------------------------------------

    if len(mine_positions) != len(set(mine_positions)):
        raise ValueError(
            "Actual mine positions contain duplicates."
        )

    if len(safe_positions) != len(set(safe_positions)):
        raise ValueError(
            "Actual safe positions contain duplicates."
        )

    # --------------------------------------------------------
    # BOUNDS
    # --------------------------------------------------------
    #
    # Positions are 1-based.
    #
    # Example:
    # 5 × 5 board:
    #     valid positions = 1 ... 25
    #
    # --------------------------------------------------------

    for position in mine_positions:
        if position < 1 or position > board_total:
            raise ValueError(
                f"Mine position {position} is outside the board."
            )

    for position in safe_positions:
        if position < 1 or position > board_total:
            raise ValueError(
                f"Safe position {position} is outside the board."
            )

    # --------------------------------------------------------
    # OVERLAP
    # --------------------------------------------------------

    mine_set = set(mine_positions)
    safe_set = set(safe_positions)

    overlap = mine_set.intersection(safe_set)

    if overlap:
        raise ValueError(
            "A board position cannot be both a mine and safe."
        )

    # --------------------------------------------------------
    # MINE COUNT
    # --------------------------------------------------------

    if len(mine_positions) != mine_count:
        raise ValueError(
            f"Expected exactly {mine_count} mine positions, "
            f"but received {len(mine_positions)}."
        )

    # --------------------------------------------------------
    # SAFE COUNT
    # --------------------------------------------------------

    expected_safe_count = board_total - mine_count

    if len(safe_positions) != expected_safe_count:
        raise ValueError(
            f"Expected exactly {expected_safe_count} safe positions, "
            f"but received {len(safe_positions)}."
        )

    # --------------------------------------------------------
    # COMPLETE BOARD
    # --------------------------------------------------------

    if len(mine_positions) + len(safe_positions) != board_total:
        raise ValueError(
            "The submitted result does not contain the complete board."
        )

    # Positions are 1-based, so the complete board is:
    #
    # 1, 2, 3, ..., board_total
    #
    expected_positions = set(
        range(1, board_total + 1)
    )

    if mine_set.union(safe_set) != expected_positions:
        raise ValueError(
            "The submitted positions do not cover the complete board."
        )


# ============================================================
# CREATE RESULT
# ============================================================


def create_signal_result(
    db: Session,
    *,
    signal: Signal,
    actual_mine_positions: list[int],
    actual_safe_positions: list[int],
) -> SignalResult:
    """
    Record the actual result of a published signal.

    The result is compared against the latest prediction attached
    to the signal.

    The service calculates:

    - Correct safe predictions
    - Incorrect safe predictions
    - Correct mine predictions
    - Incorrect mine predictions
    - Combined correct predictions
    - Combined incorrect predictions
    - Overall prediction accuracy

    Existing project rule:
    A signal is considered SUCCESS when at least one prediction
    was correct.
    """

    # ========================================================
    # SIGNAL STATUS
    # ========================================================

    if signal.status != SignalStatus.RESULT_PENDING:
        raise ValueError(
            "Only RESULT_PENDING signals can have results recorded."
        )

    # ========================================================
    # DUPLICATE RESULT CHECK
    # ========================================================

    existing_result = db.scalar(
        select(SignalResult).where(
            SignalResult.signal_id == signal.id
        )
    )

    if existing_result is not None:
        raise ValueError(
            "A result has already been recorded for this signal."
        )

    # ========================================================
    # NORMALIZE INPUT
    # ========================================================

    actual_mine_positions = list(
        actual_mine_positions
    )

    actual_safe_positions = list(
        actual_safe_positions
    )

    # ========================================================
    # VALIDATE BOARD
    # ========================================================

    _validate_positions(
        board_size=signal.board_size,
        mine_count=signal.mine_count,
        actual_mine_positions=actual_mine_positions,
        actual_safe_positions=actual_safe_positions,
    )

    # ========================================================
    # LOAD LATEST PREDICTION
    # ========================================================

    prediction = get_latest_prediction(
        db=db,
        signal_id=signal.id,
    )

    if prediction is None:
        raise ValueError(
            "No prediction exists for this signal."
        )

    # ========================================================
    # CONVERT TO SETS
    # ========================================================

    predicted_safe = set(
        prediction.safe_positions or []
    )

    predicted_mines = set(
        prediction.predicted_mine_positions or []
    )

    actual_safe = set(
        actual_safe_positions
    )

    actual_mines = set(
        actual_mine_positions
    )

    # ========================================================
    # SAFE PREDICTION METRICS
    # ========================================================

    correct_safe_predictions = len(
        predicted_safe.intersection(
            actual_safe
        )
    )

    incorrect_safe_predictions = len(
        predicted_safe.intersection(
            actual_mines
        )
    )

    # ========================================================
    # MINE PREDICTION METRICS
    # ========================================================

    correct_mine_predictions = len(
        predicted_mines.intersection(
            actual_mines
        )
    )

    incorrect_mine_predictions = len(
        predicted_mines.intersection(
            actual_safe
        )
    )

    # ========================================================
    # COMBINED METRICS
    # ========================================================

    correct_predictions = (
        correct_safe_predictions
        + correct_mine_predictions
    )

    incorrect_predictions = (
        incorrect_safe_predictions
        + incorrect_mine_predictions
    )

    total_predictions = (
        len(predicted_safe)
        + len(predicted_mines)
    )

    # ========================================================
    # ACCURACY
    # ========================================================

    accuracy = (
        (
            correct_predictions
            / total_predictions
        )
        * 100
        if total_predictions > 0
        else None
    )

    if accuracy is not None:
        accuracy = round(
            accuracy,
            2,
        )

    # ========================================================
    # RESULT STATUS
    # ========================================================

    result_status = (
        ResultStatus.SUCCESS
        if correct_predictions > 0
        else ResultStatus.FAILED
    )

    # ========================================================
    # CREATE RESULT
    # ========================================================

    result = SignalResult(
        id=uuid.uuid4(),

        signal_id=signal.id,

        actual_mine_positions=actual_mine_positions,

        actual_safe_positions=actual_safe_positions,

        correct_safe_predictions=
            correct_safe_predictions,

        incorrect_safe_predictions=
            incorrect_safe_predictions,

        correct_mine_predictions=
            correct_mine_predictions,

        incorrect_mine_predictions=
            incorrect_mine_predictions,

        correct_predictions=
            correct_predictions,

        incorrect_predictions=
            incorrect_predictions,

        accuracy=accuracy,

        status=result_status,
    )

    # ========================================================
    # UPDATE SIGNAL STATUS
    # ========================================================

    if result_status == ResultStatus.SUCCESS:
        signal.status = SignalStatus.SUCCESS
    else:
        signal.status = SignalStatus.FAILED

    # ========================================================
    # SAVE
    # ========================================================

    db.add(result)
    db.add(signal)

    db.commit()

    # ========================================================
    # REFRESH
    # ========================================================

    db.refresh(result)
    db.refresh(signal)

    return result


# ============================================================
# GET RESULT
# ============================================================


def get_signal_result(
    db: Session,
    *,
    signal_id: uuid.UUID,
) -> SignalResult | None:
    """
    Return the result belonging to a signal.
    """

    return db.scalar(
        select(SignalResult).where(
            SignalResult.signal_id == signal_id
        )
    )
 
