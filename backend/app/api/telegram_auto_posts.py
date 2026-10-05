import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.administrator import Administrator
from app.models.telegram_auto_post import (
    TelegramAutoPostContentType,
    TelegramAutoPostStatus,
)
from app.schemas.telegram_auto_post import (
    TelegramAutoPostActionResponse,
    TelegramAutoPostCreate,
    TelegramAutoPostListResponse,
    TelegramAutoPostQueueResponse,
    TelegramAutoPostResponse,
    TelegramAutoPostStatisticsResponse,
    TelegramAutoPostUpdate,
)
from app.core.dependencies import (
    get_current_administrator,
)
from app.services.telegram_auto_post_service import (
    cancel_auto_post,
    create_auto_post,
    delete_auto_post,
    get_auto_post,
    get_auto_post_statistics,
    get_auto_posts,
    queue_auto_post,
    retry_auto_post,
    update_auto_post,
)


router = APIRouter(
    prefix="/api/telegram/auto-posts",
    tags=["Telegram Auto Publisher"],
)


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------

@router.post(
    "",
    response_model=TelegramAutoPostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_auto_post_endpoint(
    data: TelegramAutoPostCreate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    return create_auto_post(
        db,
        data,
    )


# ------------------------------------------------------------
# LIST
# ------------------------------------------------------------

@router.get(
    "",
    response_model=TelegramAutoPostListResponse,
)
def list_auto_posts_endpoint(
    page: int = Query(
        default=1,
        ge=1,
    ),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    status_filter: TelegramAutoPostStatus | None = Query(
        default=None,
        alias="status",
    ),
    content_type: TelegramAutoPostContentType | None = None,
    active_only: bool = False,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    items, total = get_auto_posts(
        db,
        page=page,
        page_size=page_size,
        status=status_filter,
        content_type=content_type,
        active_only=active_only,
    )

    return TelegramAutoPostListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ------------------------------------------------------------
# STATISTICS
# ------------------------------------------------------------

@router.get(
    "/statistics",
    response_model=TelegramAutoPostStatisticsResponse,
)
def auto_post_statistics_endpoint(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    return get_auto_post_statistics(db)


# ------------------------------------------------------------
# GET ONE
# ------------------------------------------------------------

@router.get(
    "/{post_id}",
    response_model=TelegramAutoPostResponse,
)
def get_auto_post_endpoint(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    post = get_auto_post(
        db,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Auto-post not found.",
        )

    return post


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------

@router.patch(
    "/{post_id}",
    response_model=TelegramAutoPostResponse,
)
def update_auto_post_endpoint(
    post_id: uuid.UUID,
    data: TelegramAutoPostUpdate,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    post = get_auto_post(
        db,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Auto-post not found.",
        )

    try:
        return update_auto_post(
            db,
            post,
            data,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------

@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_auto_post_endpoint(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    post = get_auto_post(
        db,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Auto-post not found.",
        )

    try:
        delete_auto_post(
            db,
            post,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


# ------------------------------------------------------------
# QUEUE
# ------------------------------------------------------------

@router.post(
    "/{post_id}/queue",
    response_model=TelegramAutoPostQueueResponse,
)
def queue_auto_post_endpoint(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    post = get_auto_post(
        db,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Auto-post not found.",
        )

    try:
        post = queue_auto_post(
            db,
            post,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Auto-post queued successfully.",
        "post": post,
    }


# ------------------------------------------------------------
# CANCEL
# ------------------------------------------------------------

@router.post(
    "/{post_id}/cancel",
    response_model=TelegramAutoPostActionResponse,
)
def cancel_auto_post_endpoint(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    post = get_auto_post(
        db,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Auto-post not found.",
        )

    try:
        post = cancel_auto_post(
            db,
            post,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Auto-post cancelled successfully.",
        "post": post,
    }


# ------------------------------------------------------------
# RETRY
# ------------------------------------------------------------

@router.post(
    "/{post_id}/retry",
    response_model=TelegramAutoPostActionResponse,
)
def retry_auto_post_endpoint(
    post_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    post = get_auto_post(
        db,
        post_id,
    )

    if post is None:
        raise HTTPException(
            status_code=404,
            detail="Auto-post not found.",
        )

    try:
        post = retry_auto_post(
            db,
            post,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "message": "Auto-post queued for retry.",
        "post": post,
    }

