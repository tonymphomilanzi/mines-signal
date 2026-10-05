from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.telegram_auto_post import (
    TelegramAutoPostContentType,
    TelegramAutoPostStatus,
)


# ------------------------------------------------------------
# BASE
# ------------------------------------------------------------

class TelegramAutoPostBase(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )

    content_type: TelegramAutoPostContentType = (
        TelegramAutoPostContentType.MESSAGE
    )

    message: str | None = None

    link_url: HttpUrl | None = None

    media_url: HttpUrl | None = None

    caption: str | None = None

    is_active: bool = True

    scheduled_at: datetime | None = None


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------

class TelegramAutoPostCreate(
    TelegramAutoPostBase
):
    """
    Create a new Telegram auto-post.

    New posts are created as DRAFT.
    """

    pass


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------

class TelegramAutoPostUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    content_type: (
        TelegramAutoPostContentType | None
    ) = None

    message: str | None = None

    link_url: HttpUrl | None = None

    media_url: HttpUrl | None = None

    caption: str | None = None

    is_active: bool | None = None

    scheduled_at: datetime | None = None


# ------------------------------------------------------------
# RESPONSE
# ------------------------------------------------------------

class TelegramAutoPostResponse(BaseModel):
    id: UUID

    title: str

    content_type: TelegramAutoPostContentType

    message: str | None

    link_url: str | None

    media_url: str | None

    caption: str | None

    status: TelegramAutoPostStatus

    is_active: bool

    scheduled_at: datetime | None

    published_at: datetime | None

    telegram_message_id: int | None

    channel_id: str | None

    channel_username: str | None

    attempts: int

    error_message: str | None

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


# ------------------------------------------------------------
# LIST
# ------------------------------------------------------------

class TelegramAutoPostListResponse(BaseModel):
    items: list[TelegramAutoPostResponse]

    total: int

    page: int

    page_size: int


# ------------------------------------------------------------
# QUEUE
# ------------------------------------------------------------

class TelegramAutoPostQueueResponse(BaseModel):
    message: str

    post: TelegramAutoPostResponse


# ------------------------------------------------------------
# ACTION
# ------------------------------------------------------------

class TelegramAutoPostActionResponse(BaseModel):
    message: str

    post: TelegramAutoPostResponse


# ------------------------------------------------------------
# STATISTICS
# ------------------------------------------------------------

class TelegramAutoPostStatisticsResponse(BaseModel):
    total: int

    draft: int

    queued: int

    publishing: int

    published: int

    failed: int

    cancelled: int

    active: int

    next_scheduled_at: datetime | None

