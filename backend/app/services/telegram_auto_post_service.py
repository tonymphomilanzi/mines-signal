from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.telegram_auto_post import (
    TelegramAutoPost,
    TelegramAutoPostStatus,
)
from app.schemas.telegram_auto_post import (
    TelegramAutoPostCreate,
    TelegramAutoPostUpdate,
)


# ------------------------------------------------------------
# CREATE
# ------------------------------------------------------------

def create_auto_post(
    db: Session,
    data: TelegramAutoPostCreate,
) -> TelegramAutoPost:

    post = TelegramAutoPost(
        title=data.title,
        content_type=data.content_type,
        message=data.message,
        link_url=(
            str(data.link_url)
            if data.link_url
            else None
        ),
        media_url=(
            str(data.media_url)
            if data.media_url
            else None
        ),
        caption=data.caption,
        status=TelegramAutoPostStatus.DRAFT,
        is_active=data.is_active,
        scheduled_at=data.scheduled_at,
    )

    db.add(post)
    db.commit()
    db.refresh(post)

    return post


# ------------------------------------------------------------
# GET BY ID
# ------------------------------------------------------------

def get_auto_post(
    db: Session,
    post_id: UUID,
) -> TelegramAutoPost | None:

    return db.scalar(
        select(TelegramAutoPost).where(
            TelegramAutoPost.id == post_id
        )
    )


# ------------------------------------------------------------
# LIST
# ------------------------------------------------------------

def get_auto_posts(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 20,
    status: TelegramAutoPostStatus | None = None,
    content_type=None,
    active_only: bool = False,
) -> tuple[list[TelegramAutoPost], int]:

    page = max(page, 1)

    page_size = min(
        max(page_size, 1),
        100,
    )

    query = select(TelegramAutoPost)

    count_query = select(
        func.count(TelegramAutoPost.id)
    )

    if status is not None:
        query = query.where(
            TelegramAutoPost.status == status
        )

        count_query = count_query.where(
            TelegramAutoPost.status == status
        )

    if content_type is not None:
        query = query.where(
            TelegramAutoPost.content_type
            == content_type
        )

        count_query = count_query.where(
            TelegramAutoPost.content_type
            == content_type
        )

    if active_only:
        query = query.where(
            TelegramAutoPost.is_active.is_(True)
        )

        count_query = count_query.where(
            TelegramAutoPost.is_active.is_(True)
        )

    query = query.order_by(
        TelegramAutoPost.created_at.desc()
    )

    query = query.offset(
        (page - 1) * page_size
    ).limit(page_size)

    items = list(db.scalars(query).all())

    total = db.scalar(count_query) or 0

    return items, total


# ------------------------------------------------------------
# UPDATE
# ------------------------------------------------------------

def update_auto_post(
    db: Session,
    post: TelegramAutoPost,
    data: TelegramAutoPostUpdate,
) -> TelegramAutoPost:

    if post.status == TelegramAutoPostStatus.PUBLISHED:
        raise ValueError(
            "Published auto-posts cannot be edited."
        )

    values = data.model_dump(
        exclude_unset=True
    )

    if "link_url" in values:
        values["link_url"] = (
            str(values["link_url"])
            if values["link_url"]
            else None
        )

    if "media_url" in values:
        values["media_url"] = (
            str(values["media_url"])
            if values["media_url"]
            else None
        )

    for field, value in values.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)

    return post


# ------------------------------------------------------------
# DELETE
# ------------------------------------------------------------

def delete_auto_post(
    db: Session,
    post: TelegramAutoPost,
) -> None:

    if post.status == TelegramAutoPostStatus.PUBLISHED:
        raise ValueError(
            "Published auto-posts cannot be deleted."
        )

    db.delete(post)
    db.commit()


# ------------------------------------------------------------
# QUEUE
# ------------------------------------------------------------

def queue_auto_post(
    db: Session,
    post: TelegramAutoPost,
) -> TelegramAutoPost:

    if post.status not in (
        TelegramAutoPostStatus.DRAFT,
        TelegramAutoPostStatus.FAILED,
    ):
        raise ValueError(
            "Only DRAFT or FAILED auto-posts "
            "can be queued."
        )

    if not post.is_active:
        raise ValueError(
            "Inactive auto-posts cannot be queued."
        )

    post.status = TelegramAutoPostStatus.QUEUED

    if post.scheduled_at is None:
        post.scheduled_at = datetime.now(
            timezone.utc
        )

    post.error_message = None

    db.commit()
    db.refresh(post)

    return post


# ------------------------------------------------------------
# CANCEL
# ------------------------------------------------------------

def cancel_auto_post(
    db: Session,
    post: TelegramAutoPost,
) -> TelegramAutoPost:

    if post.status not in (
        TelegramAutoPostStatus.DRAFT,
        TelegramAutoPostStatus.QUEUED,
        TelegramAutoPostStatus.FAILED,
    ):
        raise ValueError(
            "This auto-post cannot be cancelled."
        )

    post.status = TelegramAutoPostStatus.CANCELLED

    db.commit()
    db.refresh(post)

    return post


# ------------------------------------------------------------
# RETRY
# ------------------------------------------------------------

def retry_auto_post(
    db: Session,
    post: TelegramAutoPost,
) -> TelegramAutoPost:

    if post.status != TelegramAutoPostStatus.FAILED:
        raise ValueError(
            "Only FAILED auto-posts can be retried."
        )

    if not post.is_active:
        raise ValueError(
            "Inactive auto-posts cannot be retried."
        )

    post.status = TelegramAutoPostStatus.QUEUED
    post.error_message = None

    post.scheduled_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(post)

    return post


# ------------------------------------------------------------
# STATISTICS
# ------------------------------------------------------------

def get_auto_post_statistics(
    db: Session,
) -> dict:

    rows = db.execute(
        select(
            TelegramAutoPost.status,
            func.count(TelegramAutoPost.id),
        ).group_by(
            TelegramAutoPost.status
        )
    ).all()

    counts = {
        status.value: 0
        for status in TelegramAutoPostStatus
    }

    for status, count in rows:
        counts[status.value] = count

    active = db.scalar(
        select(
            func.count(TelegramAutoPost.id)
        ).where(
            TelegramAutoPost.is_active.is_(True)
        )
    ) or 0

    next_scheduled_at = db.scalar(
        select(
            TelegramAutoPost.scheduled_at
        )
        .where(
            TelegramAutoPost.status
            == TelegramAutoPostStatus.QUEUED
        )
        .where(
            TelegramAutoPost.is_active.is_(True)
        )
        .where(
            TelegramAutoPost.scheduled_at.is_not(None)
        )
        .order_by(
            TelegramAutoPost.scheduled_at.asc()
        )
        .limit(1)
    )

    return {
        "total": sum(counts.values()),
        "draft": counts[
            TelegramAutoPostStatus.DRAFT.value
        ],
        "queued": counts[
            TelegramAutoPostStatus.QUEUED.value
        ],
        "publishing": counts[
            TelegramAutoPostStatus.PUBLISHING.value
        ],
        "published": counts[
            TelegramAutoPostStatus.PUBLISHED.value
        ],
        "failed": counts[
            TelegramAutoPostStatus.FAILED.value
        ],
        "cancelled": counts[
            TelegramAutoPostStatus.CANCELLED.value
        ],
        "active": active,
        "next_scheduled_at": next_scheduled_at,
    }

