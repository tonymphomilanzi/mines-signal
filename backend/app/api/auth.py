from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_administrator
from app.db.session import get_db
from app.models.administrator import Administrator
from app.schemas.administrator import (
    AdministratorResponse,
    CreateAdministratorRequest,
)
from app.schemas.auth import (
    LoginAdministratorResponse,
    LoginRequest,
    LoginResponse,
)
from app.services.administrator_service import create_administrator
from app.services.auth_service import login_administrator


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


# ============================================================
# COOKIE SETTINGS
# ============================================================

AUTH_COOKIE_NAME = "mines_admin_token"

AUTH_COOKIE_MAX_AGE = 60 * 60  # 1 hour


# ============================================================
# LOGIN
# ============================================================

@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    """
    Authenticate an administrator.

    The JWT is returned in the response for backward
    compatibility and is also stored in an HTTP-only cookie.
    """

    try:
        administrator, token = login_administrator(
            db=db,
            email=str(payload.email),
            password=payload.password,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )

    # --------------------------------------------------------
    # Store JWT in HTTP-only cookie
    # --------------------------------------------------------

    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=token,
        max_age=AUTH_COOKIE_MAX_AGE,
        httponly=True,
        secure=False,
        samesite="lax",
        path="/",
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        administrator=administrator,
    )


# ============================================================
# CURRENT ADMINISTRATOR
# ============================================================

@router.get(
    "/me",
    response_model=LoginAdministratorResponse,
)
def get_me(
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    """
    Return the currently authenticated administrator.
    """

    return current_admin


# ============================================================
# LOGOUT
# ============================================================

@router.post(
    "/logout",
)
def logout(
    response: Response,
):
    """
    Clear the administrator authentication cookie.
    """

    response.delete_cookie(
        key=AUTH_COOKIE_NAME,
        path="/",
    )

    return {
        "message": "Successfully logged out."
    }


# ============================================================
# BOOTSTRAP ADMINISTRATOR
# ============================================================

@router.post(
    "/bootstrap",
    response_model=AdministratorResponse,
)
def bootstrap_admin(
    payload: CreateAdministratorRequest,
    db: Session = Depends(get_db),
):
    """
    Create the first administrator account.

    This endpoint is intended only for initial system setup.
    """

    # --------------------------------------------------------
    # Check if an administrator already exists
    # --------------------------------------------------------

    existing_admin = db.scalar(
        select(Administrator).limit(1)
    )

    if existing_admin is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Administrator already exists. "
                "Use the administrator management system "
                "to create additional administrators."
            ),
        )

    # --------------------------------------------------------
    # Validate passwords
    # --------------------------------------------------------

    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    # --------------------------------------------------------
    # Validate bootstrap role
    # --------------------------------------------------------

    if payload.role != "SUPER_ADMINISTRATOR":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The bootstrap administrator must have "
                "the SUPER_ADMINISTRATOR role."
            ),
        )

    # --------------------------------------------------------
    # Create administrator
    # --------------------------------------------------------

    try:
        administrator = create_administrator(
            db=db,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            password=payload.password,
            role=payload.role,
            status=payload.status,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    return administrator