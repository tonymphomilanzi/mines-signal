from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.administrator import (
    Administrator,
    AdministratorStatus,
)


security = HTTPBearer(
    auto_error=False,
)


AUTH_COOKIE_NAME = "mines_admin_token"


def get_current_administrator(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
    auth_cookie: str | None = Cookie(
        default=None,
        alias=AUTH_COOKIE_NAME,
    ),
    db: Session = Depends(get_db),
) -> Administrator:
    """
    Return the currently authenticated administrator.

    Authentication can come from either:

    1. Authorization: Bearer <token>
    2. HTTP-only mines_admin_token cookie
    """

    # --------------------------------------------------------
    # Get token
    # --------------------------------------------------------

    token = None

    if credentials is not None:
        token = credentials.credentials

    elif auth_cookie:
        token = auth_cookie

    # --------------------------------------------------------
    # No authentication
    # --------------------------------------------------------

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Decode JWT
    # --------------------------------------------------------

    try:
        payload = decode_access_token(token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Get administrator ID
    # --------------------------------------------------------

    administrator_id = payload.get("sub")

    if not administrator_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Convert to UUID
    # --------------------------------------------------------

    try:
        administrator_uuid = UUID(
            str(administrator_id)
        )

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Find administrator
    # --------------------------------------------------------

    administrator = db.scalar(
        select(Administrator).where(
            Administrator.id == administrator_uuid
        )
    )

    if administrator is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Administrator account not found.",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # --------------------------------------------------------
    # Check active state
    # --------------------------------------------------------

    if not administrator.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is disabled.",
        )

    if administrator.status != AdministratorStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator account is not active.",
        )

    return administrator