from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.signal import Signal, SignalStatus
from app.services.telegram_service import check_connection


# ============================================================
# DASHBOARD
# ============================================================

def get_dashboard_data(db: Session) -> dict:
    """
    Build the administrator dashboard summary.

    Dashboard metrics:

    - Signals created today
    - Signals that have been published
    - Signals waiting for actual results
    - Recent signals
    - Telegram connection status
    """

    # --------------------------------------------------------
    # TODAY
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)

    start_of_today = datetime(
        year=now.year,
        month=now.month,
        day=now.day,
        tzinfo=timezone.utc,
    )

    start_of_tomorrow = (
        start_of_today + timedelta(days=1)
    )

    # --------------------------------------------------------
    # SIGNALS TODAY
    # --------------------------------------------------------

    signals_today_statement = (
        select(func.count())
        .select_from(Signal)
        .where(
            Signal.generated_at >= start_of_today,
            Signal.generated_at < start_of_tomorrow,
        )
    )

    signals_today = db.scalar(
        signals_today_statement
    ) or 0

    # --------------------------------------------------------
    # PUBLISHED
    # --------------------------------------------------------

    published_statement = (
        select(func.count())
        .select_from(Signal)
        .where(
            Signal.published_at.is_not(None)
        )
    )

    published = db.scalar(
        published_statement
    ) or 0

    # --------------------------------------------------------
    # PENDING RESULTS
    # --------------------------------------------------------

    pending_results_statement = (
        select(func.count())
        .select_from(Signal)
        .where(
            Signal.status
            == SignalStatus.RESULT_PENDING
        )
    )

    pending_results = db.scalar(
        pending_results_statement
    ) or 0

    # --------------------------------------------------------
    # RECENT SIGNALS
    # --------------------------------------------------------

    recent_signals_statement = (
        select(Signal)
        .order_by(
            Signal.generated_at.desc()
        )
        .limit(10)
    )

    recent_signals = list(
        db.scalars(
            recent_signals_statement
        ).all()
    )

    # --------------------------------------------------------
    # TELEGRAM
    # --------------------------------------------------------
    #
    # Use the real Telegram service connection check.
    #
    # check_connection() returns:
    #
    # {
    #     "configured": bool,
    #     "connected": bool,
    #     "bot_name": ...,
    #     ...
    # }
    #
    # The dashboard frontend expects:
    #
    # "CONNECTED"
    # or
    # "OFFLINE"
    #
    # Therefore we convert the Telegram service boolean
    # into the dashboard status string here.
    # --------------------------------------------------------

    try:
        telegram_connection = check_connection(db)

        telegram_status = (
            "CONNECTED"
            if telegram_connection.get("connected") is True
            else "OFFLINE"
        )

    except Exception:
        telegram_status = "OFFLINE"

    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
        "signals_today": int(signals_today),
        "published": int(published),
        "pending_results": int(
            pending_results
        ),
        "telegram_status": telegram_status,
        "recent_signals": recent_signals,
        "generated_at": now,
    }
 
