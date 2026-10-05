from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_administrator,
)
from app.db.session import get_db
from app.models.administrator import Administrator
from app.schemas.dashboard import (
    DashboardResponse,
)
from app.services.dashboard_service import (
    get_dashboard_data,
)


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)


# ============================================================
# DASHBOARD
# ============================================================

@router.get(
    "",
    response_model=DashboardResponse,
)
def get_dashboard(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    return get_dashboard_data(db)
 
