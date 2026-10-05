from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# TELEGRAM MESSAGE
# ============================================================

class TelegramMessageResponse(BaseModel):
    id: UUID

    signal_id: UUID

    telegram_message_id: int | None

    channel_id: str
    channel_name: str | None
    channel_username: str | None

    status: str
    sync_status: str
    parse_status: str

    message_text: str

    attempts: int
    error_message: str | None

    views: int
    forwards: int

    published_at: datetime | None
    synced_at: datetime | None
    parsed_at: datetime | None

    created_at: datetime
    updated_at: datetime

    signal_number: str | None = None
    game: str | None = None
    board_size: int | None = None
    mine_count: int | None = None
    confidence: float | None = None
    recommended_positions: list[int] = Field(
        default_factory=list
    )
    model_version: str | None = None
    attempts_allowed: int | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class TelegramMessageListResponse(BaseModel):
    items: list[TelegramMessageResponse]
    total: int


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

class TelegramConfigurationResponse(BaseModel):
    bot_name: str | None

    channel_id: str | None
    channel_name: str | None
    channel_username: str | None

    automatic_publishing: bool
    publish_confirmed_signals: bool
    publish_results: bool

    publishing_template: str | None

    bot_configured: bool
    connected: bool

    model_config = ConfigDict(
        from_attributes=True,
    )


class UpdateTelegramConfigurationRequest(BaseModel):
    bot_name: str | None = None

    channel_id: str | None = None
    channel_name: str | None = None
    channel_username: str | None = None

    automatic_publishing: bool | None = None
    publish_confirmed_signals: bool | None = None
    publish_results: bool | None = None

    publishing_template: str | None = None


# ============================================================
# STATUS
# ============================================================

class TelegramStatusResponse(BaseModel):
    configured: bool
    connected: bool

    bot_name: str | None
    bot_username: str | None

    channel_id: str | None
    channel_username: str | None

    checked_at: datetime


# ============================================================
# TEST MESSAGE
# ============================================================

class TelegramTestMessageRequest(BaseModel):
    message: str = Field(
        default="Mines Signal System Telegram test message.",
        min_length=1,
        max_length=4096,
    )


class TelegramTestMessageResponse(BaseModel):
    success: bool
    message: str

    telegram_message_id: int | None = None


# ============================================================
# RETRY
# ============================================================

class TelegramRetryResponse(BaseModel):
    message: str
    telegram_message: TelegramMessageResponse
 
