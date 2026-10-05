from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# ------------------------------------------------------------
# PERFORMANCE OVERVIEW
# ------------------------------------------------------------

class PerformanceOverviewResponse(BaseModel):
    total_completed_signals: int

    successful_signals: int
    failed_signals: int
    success_rate: float | None

    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int
    prediction_accuracy: float | None

    correct_safe_predictions: int
    incorrect_safe_predictions: int
    safe_prediction_precision: float | None

    correct_mine_predictions: int
    incorrect_mine_predictions: int
    mine_prediction_precision: float | None

    average_result_accuracy: float | None


# ------------------------------------------------------------
# MODEL PERFORMANCE
# ------------------------------------------------------------

class ModelPerformanceResponse(BaseModel):
    model_id: UUID
    model_version: str
    model_name: str

    total_completed_signals: int

    successful_signals: int
    failed_signals: int
    success_rate: float | None

    prediction_accuracy: float | None

    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int

    correct_safe_predictions: int
    incorrect_safe_predictions: int
    safe_prediction_precision: float | None

    correct_mine_predictions: int
    incorrect_mine_predictions: int
    mine_prediction_precision: float | None

    average_result_accuracy: float | None


# ------------------------------------------------------------
# BOARD PERFORMANCE
# ------------------------------------------------------------

class BoardPerformanceResponse(BaseModel):
    board_size: int
    mine_count: int

    total_completed_signals: int

    successful_signals: int
    failed_signals: int
    success_rate: float | None

    prediction_accuracy: float | None

    total_predictions: int
    correct_predictions: int
    incorrect_predictions: int

    correct_safe_predictions: int
    incorrect_safe_predictions: int
    safe_prediction_precision: float | None

    correct_mine_predictions: int
    incorrect_mine_predictions: int
    mine_prediction_precision: float | None

    average_result_accuracy: float | None


# ------------------------------------------------------------
# RECENT PERFORMANCE
# ------------------------------------------------------------

class RecentPerformanceResponse(BaseModel):
    signal_id: UUID
    result_id: UUID

    game: str

    board_size: int
    mine_count: int

    model_id: UUID | None
    model_version: str | None

    status: str

    correct_predictions: int
    incorrect_predictions: int
    accuracy: float | None

    correct_safe_predictions: int
    incorrect_safe_predictions: int

    correct_mine_predictions: int
    incorrect_mine_predictions: int

    confidence: float | None

    recorded_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )
 
