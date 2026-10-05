from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.administrator import (
    Administrator,
    AdministratorRole,
    AdministratorStatus,
)


def get_administrator_by_email(
    db: Session,
    email: str,
) -> Administrator | None:
    statement = select(Administrator).where(
        Administrator.email == email.lower().strip()
    )

    return db.scalar(statement)


def get_administrators(
    db: Session,
) -> list[Administrator]:
    statement = (
        select(Administrator)
        .order_by(Administrator.created_at.desc())
    )

    return list(db.scalars(statement).all())


def get_administrator_by_id(
    db: Session,
    administrator_id: str,
) -> Administrator | None:
    statement = select(Administrator).where(
        Administrator.id == administrator_id
    )

    return db.scalar(statement)


def create_administrator(
    db: Session,
    *,
    first_name: str,
    last_name: str,
    email: str,
    role: str,
    status: str,
    password: str,
) -> Administrator:

    normalized_email = email.lower().strip()

    existing = get_administrator_by_email(
        db,
        normalized_email,
    )

    if existing:
        raise ValueError(
            "An administrator with this email already exists."
        )

    try:
        administrator_role = AdministratorRole(role)
    except ValueError:
        raise ValueError(
            f"Invalid administrator role: {role}"
        )

    try:
        administrator_status = AdministratorStatus(status)
    except ValueError:
        raise ValueError(
            f"Invalid administrator status: {status}"
        )

    administrator = Administrator(
        first_name=first_name.strip(),
        last_name=last_name.strip(),
        email=normalized_email,
        password_hash=hash_password(password),
        role=administrator_role,
        status=administrator_status,
        is_active=(
            administrator_status
            == AdministratorStatus.ACTIVE
        ),
    )

    db.add(administrator)
    db.commit()
    db.refresh(administrator)

    return administrator


def activate_administrator(
    db: Session,
    administrator: Administrator,
) -> Administrator:

    administrator.status = AdministratorStatus.ACTIVE
    administrator.is_active = True

    db.commit()
    db.refresh(administrator)

    return administrator


def deactivate_administrator(
    db: Session,
    administrator: Administrator,
) -> Administrator:

    administrator.status = AdministratorStatus.INACTIVE
    administrator.is_active = False

    db.commit()
    db.refresh(administrator)

    return administrator


def delete_administrator(
    db: Session,
    administrator: Administrator,
) -> None:

    db.delete(administrator)
    db.commit()