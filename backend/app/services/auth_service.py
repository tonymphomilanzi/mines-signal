from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    verify_password,
)
from app.models.administrator import (
    Administrator,
    AdministratorStatus,
)


def authenticate_administrator(
    db: Session,
    email: str,
    password: str,
) -> Administrator:

    normalized_email = email.lower().strip()

    statement = select(Administrator).where(
        Administrator.email == normalized_email
    )

    administrator = db.scalar(statement)

    if administrator is None:
        raise ValueError("Invalid email or password.")

    if not verify_password(
        password,
        administrator.password_hash,
    ):
        raise ValueError("Invalid email or password.")

    if administrator.status != AdministratorStatus.ACTIVE:
        raise PermissionError(
            "This administrator account is not active."
        )

    if not administrator.is_active:
        raise PermissionError(
            "This administrator account is disabled."
        )

    administrator.last_login_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(administrator)

    return administrator


def login_administrator(
    db: Session,
    email: str,
    password: str,
) -> tuple[Administrator, str]:

    administrator = authenticate_administrator(
        db=db,
        email=email,
        password=password,
    )

    token = create_access_token(
        subject=str(administrator.id),
    )

    return administrator, token