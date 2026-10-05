import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_administrator
from app.db.session import get_db
from app.schemas.performance import (
    BoardPerformanceResponse,
    ModelPerformanceResponse,
    PerformanceOverviewResponse,
    RecentPerformanceResponse,
)
from app.services.performance_service import (
    get_board_performance,
    get_model_performance,
    get_performance_overview,
    get_recent_performance,
    get_single_model_performance,
)


router = APIRouter(
    prefix="/api/performance",
    tags=["Performance"],
)


# ------------------------------------------------------------
# OVERVIEW
# ------------------------------------------------------------

@router.get(
    "/overview",
    response_model=PerformanceOverviewResponse,
)
def performance_overview(
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Return system-wide performance metrics.
    """

    return get_performance_overview(db)


# ------------------------------------------------------------
# MODEL PERFORMANCE
# ------------------------------------------------------------

@router.get(
    "/models",
    response_model=list[ModelPerformanceResponse],
)
def performance_models(
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Return performance grouped by model.
    """

    return get_model_performance(db)


# ------------------------------------------------------------
# SINGLE MODEL PERFORMANCE
# ------------------------------------------------------------

@router.get(
    "/models/{model_id}",
    response_model=ModelPerformanceResponse,
)
def performance_model(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Return performance for one model.
    """

    performance = get_single_model_performance(
        db=db,
        model_id=model_id,
    )

    if performance is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    return performance


# ------------------------------------------------------------
# BOARD PERFORMANCE
# ------------------------------------------------------------

@router.get(
    "/board",
    response_model=list[BoardPerformanceResponse],
)
def performance_board(
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Return performance grouped by board size
    and mine configuration.
    """

    return get_board_performance(db)


# ------------------------------------------------------------
# RECENT PERFORMANCE
# ------------------------------------------------------------

@router.get(
    "/recent",
    response_model=list[RecentPerformanceResponse],
)
def performance_recent(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_administrator=Depends(
        get_current_administrator
    ),
):
    """
    Return the most recent completed signal results.
    """

    return get_recent_performance(
        db=db,
        limit=limit,
    )
 
