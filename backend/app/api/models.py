import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_administrator,
)
from app.db.session import get_db
from app.models.administrator import Administrator
from app.schemas.model import (
    CreateModelRequest,
    ModelListResponse,
    ModelResponse,
    UpdateModelRequest,
)
from app.services.model_service import (
    activate_model,
    archive_model,
    create_model,
    delete_model,
    get_model,
    get_models,
    update_model,
)


router = APIRouter(
    prefix="/api/models",
    tags=["Models"],
)


@router.get(
    "",
    response_model=ModelListResponse,
)
def list_models(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    models = get_models(db)

    return ModelListResponse(
        items=models,
        total=len(models),
    )


@router.post(
    "",
    response_model=ModelResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_model_endpoint(
    payload: CreateModelRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    try:
        return create_model(
            db=db,
            name=payload.name,
            version=payload.version,
            model_type=payload.model_type,
            description=payload.description,
            board_size=payload.board_size,
            maximum_attempts=payload.maximum_attempts,
            confidence_score=payload.confidence_score,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.get(
    "/{model_id}",
    response_model=ModelResponse,
)
def get_model_endpoint(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    model = get_model(
        db,
        model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    return model


@router.patch(
    "/{model_id}",
    response_model=ModelResponse,
)
def update_model_endpoint(
    model_id: uuid.UUID,
    payload: UpdateModelRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    model = get_model(
        db,
        model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    values = payload.model_dump(
        exclude_unset=True
    )

    if not values:
        return model

    try:
        return update_model(
            db,
            model,
            values,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch(
    "/{model_id}/activate",
    response_model=ModelResponse,
)
def activate_model_endpoint(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    model = get_model(
        db,
        model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    try:
        return activate_model(
            db,
            model,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.patch(
    "/{model_id}/deactivate",
    response_model=ModelResponse,
)
def deactivate_model_endpoint(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    model = get_model(
        db,
        model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    try:
        return archive_model(
            db,
            model,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@router.delete(
    "/{model_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_model_endpoint(
    model_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    model = get_model(
        db,
        model_id,
    )

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found.",
        )

    try:
        delete_model(
            db,
            model,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return None