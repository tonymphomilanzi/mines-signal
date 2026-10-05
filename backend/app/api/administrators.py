from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.administrator import (
    AdministratorListResponse,
    AdministratorResponse,
    CreateAdministratorRequest,
)
from app.services.administrator_service import (
    activate_administrator,
    create_administrator,
    deactivate_administrator,
    delete_administrator,
    get_administrator_by_id,
    get_administrators,
)


router = APIRouter(
    prefix="/api/administrators",
    tags=["Administrators"],
)


# ============================================================
# CREATE
# ============================================================

@router.post(
    "",
    response_model=AdministratorResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_administrator_endpoint(
    payload: CreateAdministratorRequest,
    db: Session = Depends(get_db),
):
    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match.",
        )

    try:
        administrator = create_administrator(
            db,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            role=payload.role,
            status=payload.status,
            password=payload.password,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return administrator


# ============================================================
# LIST
# ============================================================

@router.get(
    "",
    response_model=AdministratorListResponse,
)
def list_administrators(
    db: Session = Depends(get_db),
):
    administrators = get_administrators(db)

    return AdministratorListResponse(
        items=administrators,
        total=len(administrators),
    )


# ============================================================
# GET ONE
# ============================================================

@router.get(
    "/{administrator_id}",
    response_model=AdministratorResponse,
)
def get_administrator(
    administrator_id: str,
    db: Session = Depends(get_db),
):
    administrator = get_administrator_by_id(
        db,
        administrator_id,
    )

    if not administrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found.",
        )

    return administrator


# ============================================================
# ACTIVATE
# ============================================================

@router.patch(
    "/{administrator_id}/activate",
    response_model=AdministratorResponse,
)
def activate_administrator_endpoint(
    administrator_id: str,
    db: Session = Depends(get_db),
):
    administrator = get_administrator_by_id(
        db,
        administrator_id,
    )

    if not administrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found.",
        )

    return activate_administrator(
        db,
        administrator,
    )


# ============================================================
# DEACTIVATE
# ============================================================

@router.patch(
    "/{administrator_id}/deactivate",
    response_model=AdministratorResponse,
)
def deactivate_administrator_endpoint(
    administrator_id: str,
    db: Session = Depends(get_db),
):
    administrator = get_administrator_by_id(
        db,
        administrator_id,
    )

    if not administrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found.",
        )

    return deactivate_administrator(
        db,
        administrator,
    )


# ============================================================
# DELETE
# ============================================================

@router.delete(
    "/{administrator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_administrator_endpoint(
    administrator_id: str,
    db: Session = Depends(get_db),
):
    administrator = get_administrator_by_id(
        db,
        administrator_id,
    )

    if not administrator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Administrator not found.",
        )

    delete_administrator(
        db,
        administrator,
    )

    return None