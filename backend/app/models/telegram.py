import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


# ============================================================
# TELEGRAM MESSAGE STATUS
# ============================================================

class TelegramMessageStatus(str, enum.Enum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


# ============================================================
# TELEGRAM SYNC STATUS
# ============================================================

class TelegramSyncStatus(str, enum.Enum):
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


# ============================================================
# TELEGRAM PARSE STATUS
# ============================================================

class TelegramParseStatus(str, enum.Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


# ============================================================
# TELEGRAM MESSAGE
# ============================================================

class TelegramMessage(Base):
    __tablename__ = "telegram_messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    signal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "signals.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    telegram_message_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
    )

    channel_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    channel_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    channel_username: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    status: Mapped[TelegramMessageStatus] = mapped_column(
        Enum(
            TelegramMessageStatus,
            name="telegram_message_status",
        ),
        nullable=False,
        default=TelegramMessageStatus.PENDING,
        index=True,
    )

    sync_status: Mapped[TelegramSyncStatus] = mapped_column(
        Enum(
            TelegramSyncStatus,
            name="telegram_sync_status",
        ),
        nullable=False,
        default=TelegramSyncStatus.PENDING,
    )

    parse_status: Mapped[TelegramParseStatus] = mapped_column(
        Enum(
            TelegramParseStatus,
            name="telegram_parse_status",
        ),
        nullable=False,
        default=TelegramParseStatus.SUCCESS,
    )

    message_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    views: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    forwards: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

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


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

class TelegramConfiguration(Base):
    __tablename__ = "telegram_configuration"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    bot_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    channel_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    channel_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    channel_username: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    automatic_publishing: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    publish_confirmed_signals: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    publish_results: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    publishing_template: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

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
 
