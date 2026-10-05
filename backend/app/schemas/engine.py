from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# PATTERN TEST
# ============================================================

class PatternEngineTestRequest(BaseModel):
    model_id: UUID

    board_size: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    mine_count: int = Field(
        default=3,
        ge=1,
    )


class PatternEngineTestResponse(BaseModel):
    engine: str
    engine_version: str
    model_id: UUID
    board_size: int
    mine_count: int
    historical_results_used: int
    safe_positions: list[int]
    predicted_mine_positions: list[int]
    confidence: float | None


# ============================================================
# POSITION DIAGNOSTICS
# ============================================================

class PatternPositionDiagnostic(BaseModel):
    position: int

    mine_frequency: float
    safe_frequency: float

    mine_count: int
    safe_count: int

    row: int
    column: int
    structure: str

    row_frequency: float
    column_frequency: float
    structural_frequency: float

    best_pair_frequency: float
    best_triplet_frequency: float

    safe_position_component: float
    safe_mine_penalty_component: float
    safe_row_penalty_component: float
    safe_column_penalty_component: float
    safe_structure_penalty_component: float
    safe_score: float

    mine_position_component: float
    mine_safe_penalty_component: float
    mine_pair_component: float
    mine_triplet_component: float
    mine_row_component: float
    mine_column_component: float
    mine_structure_component: float
    mine_score: float

    decision: str


class PatternPairDiagnostic(BaseModel):
    positions: list[int]
    occurrences: int
    frequency: float


class PatternTripletDiagnostic(BaseModel):
    positions: list[int]
    occurrences: int
    frequency: float


class PatternStructureDiagnostic(BaseModel):
    structure: str
    mine_frequency: float
    safe_frequency: float
    mine_count: int
    safe_count: int


class PatternRowColumnDiagnostic(BaseModel):
    index: int
    mine_frequency: float
    safe_frequency: float
    mine_count: int
    safe_count: int


class PatternEngineDiagnosticsResponse(BaseModel):
    engine: str
    engine_version: str
    model_id: UUID
    board_size: int
    mine_count: int
    historical_results_used: int

    safe_positions: list[int]
    predicted_mine_positions: list[int]

    confidence: float | None

    position_diagnostics: list[
        PatternPositionDiagnostic
    ]

    repeated_pairs: list[
        PatternPairDiagnostic
    ]

    repeated_triplets: list[
        PatternTripletDiagnostic
    ]

    row_patterns: list[
        PatternRowColumnDiagnostic
    ]

    column_patterns: list[
        PatternRowColumnDiagnostic
    ]

    structural_patterns: list[
        PatternStructureDiagnostic
    ]


# ============================================================
# HISTORICAL BACKTEST REQUEST
# ============================================================

class PatternBacktestRequest(BaseModel):
    model_id: UUID

    board_size: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    mine_count: int = Field(
        default=3,
        ge=1,
    )

    limit: int = Field(
        default=100,
        ge=2,
        le=1000,
    )


# ============================================================
# BACKTEST GAME
# ============================================================

class PatternBacktestGameResult(BaseModel):
    sequence: int

    signal_id: UUID
    signal_number: str | None

    result_id: UUID
    recorded_at: datetime

    historical_results_used: int

    predicted_safe_positions: list[int]
    predicted_mine_positions: list[int]

    actual_safe_positions: list[int]
    actual_mine_positions: list[int]

    safe_hits: int
    safe_misses: int
    safe_precision_percent: float
    safe_recall_percent: float

    mine_hits: int
    mine_misses: int
    mine_precision_percent: float
    mine_recall_percent: float

    combined_hits: int
    combined_predictions: int
    combined_precision_percent: float

    overlap_count: int

    confidence: float | None


# ============================================================
# BACKTEST SKIPPED GAME
# ============================================================

class PatternBacktestSkippedGame(BaseModel):
    sequence: int
    signal_id: UUID
    result_id: UUID
    recorded_at: datetime
    reason: str


# ============================================================
# BACKTEST SUMMARY
# ============================================================

class PatternBacktestSummary(BaseModel):
    total_completed_results: int
    evaluated_games: int
    skipped_games: int

    safe_predictions: int
    safe_hits: int
    safe_precision_percent: float | None
    safe_recall_percent: float | None

    mine_predictions: int
    mine_hits: int
    mine_precision_percent: float | None
    mine_recall_percent: float | None

    combined_predictions: int
    combined_hits: int
    combined_precision_percent: float | None

    average_confidence: float | None

    games_with_safe_hit: int
    games_with_all_safe_predictions_correct: int
    games_with_all_mine_predictions_correct: int


# ============================================================
# BACKTEST RESPONSE
# ============================================================

class PatternBacktestResponse(BaseModel):
    engine: str
    engine_version: str

    model_id: UUID
    model_version: str

    board_size: int
    mine_count: int

    summary: PatternBacktestSummary

    games: list[
        PatternBacktestGameResult
    ]

    skipped_games: list[
        PatternBacktestSkippedGame
    ]