import os
from datetime import datetime, timezone
from typing import Any

import httpx
from dotenv import load_dotenv
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.signal import Signal
from app.models.telegram import (
    TelegramConfiguration,
    TelegramMessage,
    TelegramMessageStatus,
    TelegramParseStatus,
    TelegramSyncStatus,
)


# ============================================================
# ENVIRONMENT
# ============================================================

# Load .env before reading Telegram environment variables.
load_dotenv()


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHANNEL_ID = os.getenv(
    "TELEGRAM_CHANNEL_ID"
)

TELEGRAM_CHANNEL_USERNAME = os.getenv(
    "TELEGRAM_CHANNEL_USERNAME"
)

TELEGRAM_CHANNEL_NAME = os.getenv(
    "TELEGRAM_CHANNEL_NAME"
)


# Telegram Bot API
TELEGRAM_API_BASE = (
    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    if TELEGRAM_BOT_TOKEN
    else None
)


# ============================================================
# TIME
# ============================================================

def utc_now() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(timezone.utc)


# ============================================================
# CONFIGURATION
# ============================================================

def get_or_create_configuration(
    db: Session,
) -> TelegramConfiguration:
    """
    Get the existing Telegram configuration.

    If no configuration exists, create one using .env values.

    If a configuration already exists, missing Telegram
    channel values are automatically filled from .env.

    Existing database values are preserved so administrator
    changes are not overwritten.
    """

    configuration = db.scalar(
        select(TelegramConfiguration)
        .order_by(
            TelegramConfiguration.created_at.asc()
        )
    )

    # --------------------------------------------------------
    # CREATE INITIAL CONFIGURATION
    # --------------------------------------------------------

    if configuration is None:
        configuration = TelegramConfiguration(
            bot_name=None,
            channel_id=TELEGRAM_CHANNEL_ID,
            channel_name=TELEGRAM_CHANNEL_NAME,
            channel_username=TELEGRAM_CHANNEL_USERNAME,
            automatic_publishing=True,
            publish_confirmed_signals=True,
            publish_results=True,
            publishing_template=None,
        )

        db.add(configuration)
        db.commit()
        db.refresh(configuration)

        return configuration

    # --------------------------------------------------------
    # BACKFILL MISSING ENVIRONMENT VALUES
    # --------------------------------------------------------

    changed = False

    if (
        not configuration.channel_id
        and TELEGRAM_CHANNEL_ID
    ):
        configuration.channel_id = (
            TELEGRAM_CHANNEL_ID
        )
        changed = True

    if (
        not configuration.channel_username
        and TELEGRAM_CHANNEL_USERNAME
    ):
        configuration.channel_username = (
            TELEGRAM_CHANNEL_USERNAME
        )
        changed = True

    if (
        not configuration.channel_name
        and TELEGRAM_CHANNEL_NAME
    ):
        configuration.channel_name = (
            TELEGRAM_CHANNEL_NAME
        )
        changed = True

    if changed:
        configuration.updated_at = utc_now()

        db.commit()
        db.refresh(configuration)

    return configuration


def update_configuration(
    db: Session,
    **values: Any,
) -> TelegramConfiguration:
    """
    Update Telegram configuration.
    """

    configuration = get_or_create_configuration(db)

    allowed_fields = {
        "bot_name",
        "channel_id",
        "channel_name",
        "channel_username",
        "automatic_publishing",
        "publish_confirmed_signals",
        "publish_results",
        "publishing_template",
    }

    for field, value in values.items():

        if field not in allowed_fields:
            continue

        if hasattr(configuration, field):
            setattr(
                configuration,
                field,
                value,
            )

    configuration.updated_at = utc_now()

    db.commit()
    db.refresh(configuration)

    return configuration


# ============================================================
# TELEGRAM API
# ============================================================

def _telegram_request(
    method: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Make a request to the Telegram Bot API.
    """

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not TELEGRAM_API_BASE:
        raise RuntimeError(
            "Telegram API base URL is not configured."
        )

    url = f"{TELEGRAM_API_BASE}/{method}"

    try:
        response = httpx.post(
            url,
            json=payload or {},
            timeout=20.0,
        )

        response.raise_for_status()

    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Telegram API request failed: {exc}"
        ) from exc

    try:
        data = response.json()

    except ValueError as exc:
        raise RuntimeError(
            "Telegram API returned invalid JSON."
        ) from exc

    if not data.get("ok"):
        description = data.get(
            "description",
            "Unknown Telegram API error.",
        )

        raise RuntimeError(
            f"Telegram API error: {description}"
        )

    return data


# ============================================================
# CONNECTION CHECK
# ============================================================

def check_connection(
    db: Session | None = None,
) -> dict[str, Any]:
    """
    Check Telegram bot connectivity.

    Verifies the bot using getMe() and, when a database
    session is provided, uses the saved Telegram configuration.
    """

    channel_id = TELEGRAM_CHANNEL_ID
    channel_username = TELEGRAM_CHANNEL_USERNAME
    channel_name = TELEGRAM_CHANNEL_NAME

    if db is not None:

        configuration = get_or_create_configuration(db)

        channel_id = (
            configuration.channel_id
            or TELEGRAM_CHANNEL_ID
        )

        channel_username = (
            configuration.channel_username
            or TELEGRAM_CHANNEL_USERNAME
        )

        channel_name = (
            configuration.channel_name
            or TELEGRAM_CHANNEL_NAME
        )

    # --------------------------------------------------------
    # BOT TOKEN CHECK
    # --------------------------------------------------------

    if not TELEGRAM_BOT_TOKEN:
        return {
            "configured": bool(
                channel_id
            ),
            "connected": False,
            "bot_name": None,
            "bot_username": None,
            "channel_id": channel_id,
            "channel_username": channel_username,
            "channel_name": channel_name,
        }

    # --------------------------------------------------------
    # TELEGRAM CONNECTION
    # --------------------------------------------------------

    try:
        data = _telegram_request(
            "getMe"
        )

        bot = data.get(
            "result"
        ) or {}

        bot_username = (
            f"@{bot['username']}"
            if bot.get("username")
            else None
        )

        return {
            "configured": bool(
                channel_id
            ),
            "connected": True,
            "bot_name": bot.get(
                "first_name"
            ),
            "bot_username": bot_username,
            "channel_id": channel_id,
            "channel_username": channel_username,
            "channel_name": channel_name,
        }

    except Exception:
        return {
            "configured": bool(
                channel_id
            ),
            "connected": False,
            "bot_name": None,
            "bot_username": None,
            "channel_id": channel_id,
            "channel_username": channel_username,
            "channel_name": channel_name,
        }


# ============================================================
# SIGNAL MESSAGE
# ============================================================

def _build_board(
    board_size: int,
    recommended_positions: list[int],
) -> str:
    """
    Build a simple text representation of the recommended board.

    Positions are treated as 1-based positions.
    """

    total_cells = board_size * board_size

    recommended = set(
        recommended_positions
    )

    rows: list[str] = []

    for start in range(
        1,
        total_cells + 1,
        board_size,
    ):
        row: list[str] = []

        for position in range(
            start,
            min(
                start + board_size,
                total_cells + 1,
            ),
        ):
            if position in recommended:
                row.append("⭐️")
            else:
                row.append("🟦")

        rows.append(
            "".join(row)
        )

    return "\n".join(rows)


def _build_confidence_bar(
    confidence: float | None,
) -> str:
    """
    Build a 10-segment confidence bar based on
    the actual model confidence percentage.

    Examples:

    0%    -> ⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
    10%   -> 🟩⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️⬜️
    25%   -> 🟩🟩🟩⬜️⬜️⬜️⬜️⬜️⬜️⬜️
    42.85% -> 🟩🟩🟩🟩⬜️⬜️⬜️⬜️⬜️⬜️
    50%   -> 🟩🟩🟩🟩🟩⬜️⬜️⬜️⬜️⬜️
    75%   -> 🟩🟩🟩🟩🟩🟩🟩🟩⬜️⬜️
    90%   -> 🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜️
    100%  -> 🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩
    """

    total_bars = 10

    if confidence is None:
        return "⬜️" * total_bars

    # Keep confidence safely inside 0–100.
    confidence = max(
        0.0,
        min(
            100.0,
            float(confidence),
        ),
    )

    filled_bars = round(
        (confidence / 100.0)
        * total_bars
    )

    filled_bars = max(
        0,
        min(
            total_bars,
            filled_bars,
        ),
    )

    empty_bars = (
        total_bars
        - filled_bars
    )

    return (
        "🟩" * filled_bars
        + "⬜️" * empty_bars
    )


def build_signal_message(
    signal: Signal,
    template: str | None = None,
) -> str:
    """
    Build the Telegram message for a published signal.
    """

    board_size = int(
        getattr(
            signal,
            "board_size",
            5,
        )
        or 5
    )

    mine_count = int(
        getattr(
            signal,
            "mine_count",
            0,
        )
        or 0
    )

    attempts = int(
        getattr(
            signal,
            "attempts",
            0,
        )
        or 0
    )

    confidence = getattr(
        signal,
        "confidence",
        None,
    )

    recommended_positions = (
        getattr(
            signal,
            "recommended_positions",
            None,
        )
        or []
    )

    signal_number = (
        getattr(
            signal,
            "signal_number",
            None,
        )
        or str(
            getattr(
                signal,
                "id",
                "",
            )
        )
    )

    game = (
        getattr(
            signal,
            "game",
            None,
        )
        or "Mines Classic"
    )

    model_version = (
        getattr(
            signal,
            "model_version",
            None,
        )
        or "N/A"
    )

    board = _build_board(
        board_size=board_size,
        recommended_positions=recommended_positions,
    )

    confidence_text = (
        f"{confidence:.2f}%"
        if confidence is not None
        else "N/A"
    )

    # --------------------------------------------------------
    # DYNAMIC CONFIDENCE BAR
    # --------------------------------------------------------

    confidence_bar = _build_confidence_bar(
        confidence
    )

    default_message = (
        "👑 <b>ENTRY CONFIRMED</b> 👑\n"
        "\n"
        "👇 <b>Model Confidence</b> 👇\n"
        f"{confidence_bar} "
        f"{confidence_text}\n"
        "\n"
        f"{board}\n"
        "\n"
        f"🎮 <b>Game:</b> {game}\n"
        f"💣 <b>Mines:</b> {mine_count}\n"
        f"♻️ <b>Attempts:</b> {attempts}\n"
        f"🧠 <b>Model:</b> {model_version}\n"
        f"🆔 <b>Signal:</b> {signal_number}\n"
        "\n"
        "Register here 👇👇\n"
        "https://1win.com/?p=gg3f\n"
        "add promo code: ALBERT123\n"
        "\n"
        "⚠️ Please Do Not Use These Signals For Now ⚠️\n"
    )

    if template:
        try:
            return template.format(
                signal_number=signal_number,
                game=game,
                board_size=board_size,
                mine_count=mine_count,
                attempts=attempts,
                confidence=confidence_text,
                model_version=model_version,
                recommended_positions=", ".join(
                    str(position)
                    for position in recommended_positions
                ),
                board=board,
            )

        except (KeyError, ValueError):
            return default_message

    return default_message


# ============================================================
# CREATE PENDING MESSAGE
# ============================================================

def create_pending_message(
    db: Session,
    signal: Signal,
    configuration: TelegramConfiguration,
) -> TelegramMessage:
    """
    Create or retrieve the Telegram message record for a signal.
    """

    existing = db.scalar(
        select(TelegramMessage).where(
            TelegramMessage.signal_id
            == signal.id
        )
    )

    if existing:
        return existing

    message_text = build_signal_message(
        signal,
        configuration.publishing_template,
    )

    message = TelegramMessage(
        signal_id=signal.id,
        telegram_message_id=None,
        channel_id=(
            configuration.channel_id
            or TELEGRAM_CHANNEL_ID
            or ""
        ),
        channel_name=(
            configuration.channel_name
            or TELEGRAM_CHANNEL_NAME
        ),
        channel_username=(
            configuration.channel_username
            or TELEGRAM_CHANNEL_USERNAME
        ),
        status=TelegramMessageStatus.PENDING,
        sync_status=TelegramSyncStatus.PENDING,
        parse_status=TelegramParseStatus.SUCCESS,
        message_text=message_text,
        attempts=0,
        error_message=None,
        views=0,
        forwards=0,
        published_at=None,
        synced_at=None,
        parsed_at=None,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# ============================================================
# PUBLISH SIGNAL
# ============================================================

def publish_signal_to_telegram(
    db: Session,
    signal: Signal,
) -> TelegramMessage:
    """
    Publish a signal to Telegram.
    """

    configuration = get_or_create_configuration(db)

    channel_id = (
        configuration.channel_id
        or TELEGRAM_CHANNEL_ID
    )

    if not channel_id:
        raise RuntimeError(
            "Telegram channel ID is not configured."
        )

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "Telegram bot token is not configured."
        )

    message = create_pending_message(
        db,
        signal,
        configuration,
    )

    message.status = (
        TelegramMessageStatus.PENDING
    )

    message.sync_status = (
        TelegramSyncStatus.PENDING
    )

    message.error_message = None

    message.attempts = (
        (message.attempts or 0) + 1
    )

    message.updated_at = utc_now()

    db.commit()
    db.refresh(message)

    try:
        data = _telegram_request(
            "sendMessage",
            {
                "chat_id": channel_id,
                "text": message.message_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )

        telegram_result = (
            data.get("result") or {}
        )

        telegram_message_id = (
            telegram_result.get(
                "message_id"
            )
        )

        now = utc_now()

        message.telegram_message_id = (
            telegram_message_id
        )

        message.status = (
            TelegramMessageStatus.PUBLISHED
        )

        message.sync_status = (
            TelegramSyncStatus.SYNCED
        )

        message.parse_status = (
            TelegramParseStatus.SUCCESS
        )

        message.error_message = None
        message.published_at = now
        message.synced_at = now
        message.parsed_at = now
        message.updated_at = now

        db.commit()
        db.refresh(message)

        return message

    except Exception as exc:

        message.status = (
            TelegramMessageStatus.FAILED
        )

        message.sync_status = (
            TelegramSyncStatus.FAILED
        )

        message.error_message = str(exc)
        message.updated_at = utc_now()

        db.commit()
        db.refresh(message)

        raise


# ============================================================
# RETRY
# ============================================================

def retry_telegram_message(
    db: Session,
    message_id: Any,
) -> TelegramMessage:
    """
    Retry an existing Telegram message.
    """

    message = db.scalar(
        select(TelegramMessage).where(
            TelegramMessage.id
            == message_id
        )
    )

    if not message:
        raise ValueError(
            "Telegram message not found."
        )

    signal = db.scalar(
        select(Signal).where(
            Signal.id
            == message.signal_id
        )
    )

    if not signal:
        raise ValueError(
            "Associated signal not found."
        )

    configuration = get_or_create_configuration(
        db
    )

    channel_id = (
        configuration.channel_id
        or message.channel_id
        or TELEGRAM_CHANNEL_ID
    )

    if not channel_id:
        raise RuntimeError(
            "Telegram channel ID is not configured."
        )

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "Telegram bot token is not configured."
        )

    message.message_text = build_signal_message(
        signal,
        configuration.publishing_template,
    )

    message.status = (
        TelegramMessageStatus.PENDING
    )

    message.sync_status = (
        TelegramSyncStatus.PENDING
    )

    message.error_message = None

    message.attempts = (
        (message.attempts or 0) + 1
    )

    message.updated_at = utc_now()

    db.commit()
    db.refresh(message)

    try:
        data = _telegram_request(
            "sendMessage",
            {
                "chat_id": channel_id,
                "text": message.message_text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
        )

        telegram_result = (
            data.get("result") or {}
        )

        now = utc_now()

        message.telegram_message_id = (
            telegram_result.get(
                "message_id"
            )
        )

        message.status = (
            TelegramMessageStatus.PUBLISHED
        )

        message.sync_status = (
            TelegramSyncStatus.SYNCED
        )

        message.parse_status = (
            TelegramParseStatus.SUCCESS
        )

        message.error_message = None
        message.published_at = now
        message.synced_at = now
        message.parsed_at = now
        message.updated_at = now

        db.commit()
        db.refresh(message)

        return message

    except Exception as exc:

        message.status = (
            TelegramMessageStatus.FAILED
        )

        message.sync_status = (
            TelegramSyncStatus.FAILED
        )

        message.error_message = str(exc)
        message.updated_at = utc_now()

        db.commit()
        db.refresh(message)

        raise


# ============================================================
# TEST MESSAGE
# ============================================================

def send_test_message(
    message: str,
    channel_id: str | None = None,
) -> dict[str, Any]:
    """
    Send a simple test message to the configured Telegram channel.
    """

    target_channel = (
        channel_id
        or TELEGRAM_CHANNEL_ID
    )

    if not target_channel:
        raise RuntimeError(
            "Telegram channel ID is not configured."
        )

    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError(
            "Telegram bot token is not configured."
        )

    return _telegram_request(
        "sendMessage",
        {
            "chat_id": target_channel,
            "text": message,
            "parse_mode": "HTML",
        },
    )


# ============================================================
# GET MESSAGES
# ============================================================

def get_telegram_messages(
    db: Session,
    limit: int = 50,
) -> list[TelegramMessage]:
    """
    Return recent Telegram messages.
    """

    limit = max(
        1,
        min(limit, 100),
    )

    return list(
        db.scalars(
            select(TelegramMessage)
            .order_by(
                TelegramMessage.created_at.desc()
            )
            .limit(limit)
        )
    )


def get_telegram_message(
    db: Session,
    message_id: Any,
) -> TelegramMessage | None:
    """
    Return a single Telegram message.
    """

    return db.scalar(
        select(TelegramMessage).where(
            TelegramMessage.id
            == message_id
        )
    )


# ============================================================
# STATISTICS
# ============================================================

def get_telegram_statistics(
    db: Session,
) -> dict[str, int]:
    """
    Return Telegram publishing statistics.
    """

    published = db.scalar(
        select(
            func.count(
                TelegramMessage.id
            )
        ).where(
            TelegramMessage.status
            == TelegramMessageStatus.PUBLISHED
        )
    ) or 0

    pending = db.scalar(
        select(
            func.count(
                TelegramMessage.id
            )
        ).where(
            TelegramMessage.status
            == TelegramMessageStatus.PENDING
        )
    ) or 0

    failed = db.scalar(
        select(
            func.count(
                TelegramMessage.id
            )
        ).where(
            TelegramMessage.status
            == TelegramMessageStatus.FAILED
        )
    ) or 0

    total = db.scalar(
        select(
            func.count(
                TelegramMessage.id
            )
        )
    ) or 0

    return {
        "published": int(published),
        "pending": int(pending),
        "failed": int(failed),
        "total": int(total),
    }


# ============================================================
# STATUS
# ============================================================

def get_telegram_status(
    db: Session,
) -> dict[str, Any]:
    """
    Return the complete Telegram connection status.
    """

    status = check_connection(db)

    return {
        **status,
        "checked_at": utc_now(),
    }
 
