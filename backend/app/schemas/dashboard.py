from datetime import datetime

from pydantic import BaseModel

from app.schemas.signal import SignalResponse


# ============================================================
# DASHBOARD RESPONSE
# ============================================================

class DashboardResponse(BaseModel):
    signals_today: int
    published: int
    pending_results: int

    telegram_status: str

    recent_signals: list[SignalResponse]

    generated_at: datetime
 
