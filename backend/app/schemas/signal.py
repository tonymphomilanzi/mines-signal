from datetime import datetime
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.models.signal import (
    PredictionEngine,
)


# ============================================================
# CREATE SIGNAL
# ============================================================

class CreateSignalRequest(BaseModel):
    game: str = Field(
        default="Mines Classic",
        min_length=1,
        max_length=100,
    )

    board_size: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    mine_count: int = Field(
        ge=1,
    )

    attempts: int = Field(
        default=3,
        ge=1,
    )

    # The model selected on the Create Signal page.
    model_id: UUID

    # The engine that will generate the production
    # recommendation for this signal.
    prediction_engine: PredictionEngine = Field(
        default=PredictionEngine.PATTERN,
    )


# ============================================================
# PRODUCTION PREDICTION RESPONSE
# ============================================================

class PredictionResponse(BaseModel):
    id: UUID

    signal_id: UUID

    model_id: UUID | None

    safe_positions: list[int]

    predicted_mine_positions: list[int]

    confidence: float | None

    attempts: int

    model_version: str | None

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# ML POSITION PREDICTION RESPONSE
# ============================================================

class MLPositionPredictionResponse(BaseModel):
    """
    ML prediction for one board position.

    Probabilities are returned as values between 0 and 1.

    safe_probability:
        Probability assigned by the ML model that the
        position is SAFE.

    mine_probability:
        Probability assigned by the ML model that the
        position is a MINE.
    """

    position: int

    row: int

    column: int

    safe_probability: float

    mine_probability: float

    rank: int

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# ML PREDICTION RESPONSE
# ============================================================

class MLPredictionResponse(BaseModel):
    """
    Stored ML prediction details.

    When prediction_engine is ML, this represents the
    production ML prediction.

    When prediction_engine is PATTERN, this can contain
    the ML comparison prediction generated alongside the
    Pattern Engine.
    """

    id: UUID

    signal_id: UUID

    model_name: str

    model_version: str

    feature_version: str

    board_size: int

    mine_count: int

    top_positions: list[int]

    position_predictions: list[
        MLPositionPredictionResponse
    ]

    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# RESULT RESPONSE
# ============================================================

class SignalResultResponse(BaseModel):
    id: UUID

    signal_id: UUID

    actual_mine_positions: list[int]

    actual_safe_positions: list[int]

    correct_predictions: int

    incorrect_predictions: int

    accuracy: float | None

    status: str

    recorded_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# SIGNAL RESPONSE
# ============================================================

class SignalResponse(BaseModel):
    id: UUID

    signal_number: str

    game: str

    board_size: int

    mine_count: int

    model_id: UUID | None

    # Engine selected for this signal.
    prediction_engine: PredictionEngine

    confidence: float | None

    attempts: int

    recommended_positions: list[int]

    status: str

    model_version: str | None

    generated_at: datetime

    published_at: datetime | None

    confirmed_at: datetime | None

    result_status: str | None

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# SIGNAL DETAIL RESPONSE
# ============================================================

class SignalDetailResponse(
    SignalResponse
):
    predictions: list[
        PredictionResponse
    ] = Field(
        default_factory=list,
    )

    # Stored ML prediction details.
    ml_prediction: MLPredictionResponse | None = None

    result: SignalResultResponse | None = None


# ============================================================
# SIGNAL LIST RESPONSE
# ============================================================

class SignalListResponse(BaseModel):
    items: list[SignalResponse]

    total: int


# ============================================================
# ANALYZE RESPONSE
# ============================================================

class AnalyzeSignalResponse(BaseModel):
    message: str

    signal: SignalResponse

    # Production prediction generated by the
    # engine selected on the signal.
    prediction: PredictionResponse

    # Stored ML prediction details, when ML prediction
    # generation is available.
    ml_prediction: MLPredictionResponse | None = None


# ============================================================
# CONFIRM RESPONSE
# ============================================================

class ConfirmSignalResponse(BaseModel):
    message: str

    signal: SignalResponse


# ============================================================
# RESULT REQUEST
# ============================================================

class CreateSignalResultRequest(BaseModel):
    actual_mine_positions: list[int] = Field(
        default_factory=list,
    )

    actual_safe_positions: list[int] = Field(
        default_factory=list,
    )


# ============================================================
# RESULT CREATION RESPONSE
# ============================================================

class CreateSignalResultResponse(BaseModel):
    message: str

    signal: SignalResponse

    result: SignalResultResponse


# ============================================================
# RESULT LIST ITEM
# ============================================================

class SignalResultListItem(BaseModel):
    id: UUID | None

    signal_id: UUID

    signal_number: str

    game: str

    board_size: int

    mine_count: int

    confidence: float | None

    predicted_safe_positions: list[int]

    actual_safe_positions: list[int]

    actual_mine_positions: list[int]

    correct_predictions: int

    incorrect_predictions: int

    accuracy: float | None

    status: str

    attempts: int

    model_version: str | None

    signal_created_at: datetime

    recorded_at: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )


# ============================================================
# RESULT LIST RESPONSE
# ============================================================

class SignalResultListResponse(BaseModel):
    items: list[SignalResultListItem]

    total: int


# ============================================================
# RESULT DETAIL RESPONSE
# ============================================================

class SignalResultDetailResponse(
    SignalResultListItem
):
    pass
 
