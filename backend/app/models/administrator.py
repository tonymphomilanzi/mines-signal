import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AdministratorRole(str, enum.Enum):
    SUPER_ADMINISTRATOR = "SUPER_ADMINISTRATOR"
    ADMINISTRATOR = "ADMINISTRATOR"
    MODERATOR = "MODERATOR"
    SUPPORT = "SUPPORT"


class AdministratorStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    PENDING = "PENDING"


class Administrator(Base):
    __tablename__ = "administrators"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[AdministratorRole] = mapped_column(
        Enum(AdministratorRole, name="administrator_role"),
        nullable=False,
        default=AdministratorRole.ADMINISTRATOR,
    )

    status: Mapped[AdministratorStatus] = mapped_column(
        Enum(AdministratorStatus, name="administrator_status"),
        nullable=False,
        default=AdministratorStatus.PENDING,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
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