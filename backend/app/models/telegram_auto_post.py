import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# AUTO POST CONTENT TYPE
# ============================================================


class TelegramAutoPostContentType(str, enum.Enum):
    MESSAGE = "MESSAGE"
    LINK = "LINK"
    VIDEO = "VIDEO"
    IMAGE = "IMAGE"


# ============================================================
# AUTO POST STATUS
# ============================================================


class TelegramAutoPostStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    QUEUED = "QUEUED"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# ============================================================
# TELEGRAM AUTO POST
# ============================================================


class TelegramAutoPost(Base):
    __tablename__ = "telegram_auto_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # --------------------------------------------------------
    # CONTENT
    # --------------------------------------------------------

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content_type: Mapped[
        TelegramAutoPostContentType
    ] = mapped_column(
        Enum(
            TelegramAutoPostContentType,
            name="telegram_auto_post_content_type",
        ),
        nullable=False,
        default=TelegramAutoPostContentType.MESSAGE,
        index=True,
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    link_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    media_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    caption: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    status: Mapped[
        TelegramAutoPostStatus
    ] = mapped_column(
        Enum(
            TelegramAutoPostStatus,
            name="telegram_auto_post_status",
        ),
        nullable=False,
        default=TelegramAutoPostStatus.DRAFT,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # --------------------------------------------------------
    # SCHEDULING
    # --------------------------------------------------------

    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # --------------------------------------------------------
    # TELEGRAM RESULT
    # --------------------------------------------------------

    telegram_message_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    channel_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    channel_username: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    # --------------------------------------------------------
    # RETRIES / ERRORS
    # --------------------------------------------------------

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # --------------------------------------------------------
    # TIMESTAMPS
    # --------------------------------------------------------

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
