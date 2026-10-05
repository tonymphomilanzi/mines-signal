import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, text, update
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.telegram import TelegramConfiguration
from app.models.telegram_auto_post import (
    TelegramAutoPost,
    TelegramAutoPostContentType,
    TelegramAutoPostStatus,
)
from app.services.telegram_service import (
    _telegram_request,
    get_or_create_configuration,
)


logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# Run the publisher every 20 minutes.
AUTO_PUBLISH_INTERVAL_SECONDS = 20 * 60

# Only publish one item during each cycle.
MAX_POSTS_PER_CYCLE = 1

# A post stuck in PUBLISHING for longer than this period
# will be returned to QUEUED.
PUBLISHING_TIMEOUT_MINUTES = 30

# PostgreSQL advisory lock identifier.
#
# This prevents multiple FastAPI instances from running
# the auto publisher at the same time.
AUTO_PUBLISHER_LOCK_ID = 738291


# ============================================================
# TIME
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================
# DATABASE LOCK
# ============================================================

def acquire_worker_lock(
    db: Session,
) -> bool:
    """
    Attempt to acquire the PostgreSQL advisory lock.

    The lock belongs to the current PostgreSQL connection and
    remains active until explicitly released or the connection
    closes.
    """

    result = db.execute(
        text(
            "SELECT pg_try_advisory_lock(:lock_id)"
        ),
        {
            "lock_id": AUTO_PUBLISHER_LOCK_ID,
        },
    )

    acquired = result.scalar()

    if acquired:
        logger.debug(
            "Telegram Auto Publisher advisory lock acquired."
        )

    return bool(acquired)


def release_worker_lock(
    db: Session,
) -> None:
    """
    Release the PostgreSQL advisory lock.
    """

    try:
        db.execute(
            text(
                "SELECT pg_advisory_unlock(:lock_id)"
            ),
            {
                "lock_id": AUTO_PUBLISHER_LOCK_ID,
            },
        )

        logger.debug(
            "Telegram Auto Publisher advisory lock released."
        )

    except Exception:
        logger.exception(
            "Failed to release Telegram Auto Publisher advisory lock."
        )


# ============================================================
# RECOVER STUCK POSTS
# ============================================================

def recover_stuck_posts(
    db: Session,
) -> int:
    """
    Recover posts that have remained in PUBLISHING state
    longer than the configured timeout.

    These posts are returned to QUEUED so they can be attempted
    again during a later cycle.
    """

    cutoff = (
        utc_now()
        - timedelta(
            minutes=PUBLISHING_TIMEOUT_MINUTES
        )
    )

    result = db.execute(
        update(TelegramAutoPost)
        .where(
            TelegramAutoPost.status
            == TelegramAutoPostStatus.PUBLISHING,
            TelegramAutoPost.updated_at < cutoff,
            TelegramAutoPost.is_active.is_(True),
        )
        .values(
            status=TelegramAutoPostStatus.QUEUED,
            error_message=(
                "Publishing attempt timed out and "
                "was returned to the queue."
            ),
            updated_at=utc_now(),
        )
    )

    db.commit()

    recovered = result.rowcount or 0

    if recovered:
        logger.warning(
            "Recovered %s stuck Telegram auto post(s).",
            recovered,
        )

    return recovered


# ============================================================
# CLAIM NEXT POST
# ============================================================

def claim_next_auto_post(
    db: Session,
) -> TelegramAutoPost | None:
    """
    Atomically claim the next queued auto post.

    PostgreSQL row locking prevents two database workers from
    claiming the same post simultaneously.
    """

    now = utc_now()

    post = db.scalar(
        select(TelegramAutoPost)
        .where(
            TelegramAutoPost.status
            == TelegramAutoPostStatus.QUEUED,

            TelegramAutoPost.is_active.is_(True),

            TelegramAutoPost.scheduled_at.is_not(None),

            TelegramAutoPost.scheduled_at <= now,
        )
        .order_by(
            TelegramAutoPost.scheduled_at.asc(),
            TelegramAutoPost.created_at.asc(),
        )
        .with_for_update(
            skip_locked=True,
        )
    )

    if post is None:
        return None

    post.status = (
        TelegramAutoPostStatus.PUBLISHING
    )

    post.attempts = (
        (post.attempts or 0) + 1
    )

    post.error_message = None
    post.updated_at = now

    db.commit()
    db.refresh(post)

    logger.info(
        "Telegram auto post claimed: "
        "id=%s title=%s attempt=%s",
        post.id,
        post.title,
        post.attempts,
    )

    return post


# ============================================================
# TELEGRAM CONFIGURATION
# ============================================================

def get_publish_configuration(
    db: Session,
) -> TelegramConfiguration:
    """
    Load the Telegram configuration used for publishing.
    """

    configuration = (
        get_or_create_configuration(db)
    )

    if not configuration.channel_id:
        raise RuntimeError(
            "Telegram channel ID is not configured."
        )

    return configuration


# ============================================================
# MESSAGE CONTENT
# ============================================================

def _message_text(
    post: TelegramAutoPost,
) -> str:
    """
    Build text content for MESSAGE and LINK posts.
    """

    message = (
        post.message
        or post.caption
        or post.title
        or ""
    ).strip()

    if (
        post.content_type
        == TelegramAutoPostContentType.LINK
    ):
        if not post.link_url:
            raise RuntimeError(
                "Link auto post does not contain link_url."
            )

        if message:
            return (
                f"{message}\n\n"
                f"{post.link_url}"
            )

        return str(post.link_url)

    return message


def _media_caption(
    post: TelegramAutoPost,
) -> str | None:
    """
    Build caption for VIDEO and IMAGE posts.

    Telegram media captions are limited to 1024
    characters.
    """

    caption = (
        post.caption
        or post.message
        or post.title
        or ""
    ).strip()

    if not caption:
        return None

    return caption[:1024]


# ============================================================
# PUBLISH MESSAGE
# ============================================================

def _publish_message(
    post: TelegramAutoPost,
    channel_id: str,
) -> dict[str, Any]:
    """
    Publish a normal Telegram message.
    """

    text_content = _message_text(post)

    if not text_content:
        raise RuntimeError(
            "Auto post does not contain message content."
        )

    return _telegram_request(
        "sendMessage",
        {
            "chat_id": channel_id,
            "text": text_content,
            "disable_web_page_preview": False,
        },
    )


# ============================================================
# PUBLISH VIDEO
# ============================================================

def _publish_video(
    post: TelegramAutoPost,
    channel_id: str,
) -> dict[str, Any]:
    """
    Publish a video using its public media URL.
    """

    if not post.media_url:
        raise RuntimeError(
            "Video auto post does not contain media_url."
        )

    payload: dict[str, Any] = {
        "chat_id": channel_id,
        "video": str(post.media_url),
    }

    caption = _media_caption(post)

    if caption:
        payload["caption"] = caption

    return _telegram_request(
        "sendVideo",
        payload,
    )


# ============================================================
# PUBLISH IMAGE
# ============================================================

def _publish_image(
    post: TelegramAutoPost,
    channel_id: str,
) -> dict[str, Any]:
    """
    Publish an image using its public media URL.
    """

    if not post.media_url:
        raise RuntimeError(
            "Image auto post does not contain media_url."
        )

    payload: dict[str, Any] = {
        "chat_id": channel_id,
        "photo": str(post.media_url),
    }

    caption = _media_caption(post)

    if caption:
        payload["caption"] = caption

    return _telegram_request(
        "sendPhoto",
        payload,
    )


# ============================================================
# SEND AUTO POST TO TELEGRAM
# ============================================================

def send_auto_post_to_telegram(
    post: TelegramAutoPost,
    configuration: TelegramConfiguration,
) -> dict[str, Any]:
    """
    Send the auto post to Telegram based on its content type.
    """

    channel_id = configuration.channel_id

    if not channel_id:
        raise RuntimeError(
            "Telegram channel ID is not configured."
        )

    if post.content_type in (
        TelegramAutoPostContentType.MESSAGE,
        TelegramAutoPostContentType.LINK,
    ):
        return _publish_message(
            post,
            channel_id,
        )

    if (
        post.content_type
        == TelegramAutoPostContentType.VIDEO
    ):
        return _publish_video(
            post,
            channel_id,
        )

    if (
        post.content_type
        == TelegramAutoPostContentType.IMAGE
    ):
        return _publish_image(
            post,
            channel_id,
        )

    raise RuntimeError(
        "Unsupported auto post content type: "
        f"{post.content_type}"
    )


# ============================================================
# MARK PUBLISHED
# ============================================================

def mark_auto_post_published(
    db: Session,
    post: TelegramAutoPost,
    configuration: TelegramConfiguration,
    telegram_result: dict[str, Any],
) -> TelegramAutoPost:
    """
    Mark an auto post as successfully published.
    """

    result = (
        telegram_result.get("result")
        or {}
    )

    telegram_message_id = (
        result.get("message_id")
    )

    if not telegram_message_id:
        raise RuntimeError(
            "Telegram did not return a message ID."
        )

    now = utc_now()

    post.telegram_message_id = (
        telegram_message_id
    )

    post.channel_id = (
        configuration.channel_id
    )

    post.channel_username = (
        configuration.channel_username
    )

    post.status = (
        TelegramAutoPostStatus.PUBLISHED
    )

    post.published_at = now
    post.error_message = None
    post.updated_at = now

    db.commit()
    db.refresh(post)

    return post


# ============================================================
# MARK FAILED
# ============================================================

def mark_auto_post_failed(
    db: Session,
    post: TelegramAutoPost,
    error: Exception,
) -> TelegramAutoPost:
    """
    Mark an auto post as failed without crashing
    the background worker.
    """

    post.status = (
        TelegramAutoPostStatus.FAILED
    )

    post.error_message = str(error)
    post.updated_at = utc_now()

    db.commit()
    db.refresh(post)

    return post


# ============================================================
# PROCESS ONE POST
# ============================================================

def process_auto_post(
    db: Session,
    post: TelegramAutoPost,
    configuration: TelegramConfiguration,
) -> TelegramAutoPost:
    """
    Publish one claimed auto post and update its status.
    """

    telegram_result = (
        send_auto_post_to_telegram(
            post,
            configuration,
        )
    )

    return mark_auto_post_published(
        db,
        post,
        configuration,
        telegram_result,
    )


# ============================================================
# RUN ONE PUBLISHING CYCLE
# ============================================================

def run_auto_publisher_cycle() -> dict[str, Any]:
    """
    Process at most MAX_POSTS_PER_CYCLE queued posts.

    This function is synchronous so it can also be executed
    manually from a Python shell or test.
    """

    db = SessionLocal()

    lock_acquired = False

    try:
        # ----------------------------------------------------
        # SINGLE WORKER LOCK
        # ----------------------------------------------------

        lock_acquired = acquire_worker_lock(db)

        if not lock_acquired:
            logger.info(
                "Telegram Auto Publisher cycle skipped: "
                "another worker is active."
            )

            return {
                "processed": False,
                "status": "LOCKED",
            }

        # ----------------------------------------------------
        # RECOVER STUCK POSTS
        # ----------------------------------------------------

        recovered = recover_stuck_posts(db)

        # ----------------------------------------------------
        # LOAD TELEGRAM CONFIGURATION
        # ----------------------------------------------------

        configuration = (
            get_publish_configuration(db)
        )

        # ----------------------------------------------------
        # AUTOMATIC PUBLISHING SWITCH
        # ----------------------------------------------------

        if not configuration.automatic_publishing:
            logger.info(
                "Telegram Auto Publisher is disabled "
                "in Telegram configuration."
            )

            return {
                "processed": False,
                "status": "DISABLED",
                "recovered": recovered,
            }

        # ----------------------------------------------------
        # PROCESS QUEUED POSTS
        # ----------------------------------------------------

        processed = 0
        results: list[dict[str, Any]] = []

        while processed < MAX_POSTS_PER_CYCLE:

            post = claim_next_auto_post(db)

            if post is None:
                break

            post_id = post.id

            try:
                published_post = (
                    process_auto_post(
                        db,
                        post,
                        configuration,
                    )
                )

                logger.info(
                    "Telegram auto post published: "
                    "id=%s title=%s "
                    "telegram_message_id=%s",
                    published_post.id,
                    published_post.title,
                    published_post.telegram_message_id,
                )

                results.append(
                    {
                        "post_id": str(
                            published_post.id
                        ),
                        "status": "PUBLISHED",
                        "telegram_message_id": (
                            published_post.telegram_message_id
                        ),
                    }
                )

            except Exception as exc:
                logger.exception(
                    "Telegram auto post failed: "
                    "id=%s title=%s",
                    post_id,
                    post.title,
                )

                failed_post = (
                    mark_auto_post_failed(
                        db,
                        post,
                        exc,
                    )
                )

                results.append(
                    {
                        "post_id": str(
                            failed_post.id
                        ),
                        "status": "FAILED",
                        "error": str(exc),
                    }
                )

            processed += 1

        # ----------------------------------------------------
        # CYCLE RESULT
        # ----------------------------------------------------

        if not results:
            return {
                "processed": False,
                "status": "NO_POST",
                "recovered": recovered,
            }

        return {
            "processed": True,
            "status": "COMPLETED",
            "processed_count": len(results),
            "recovered": recovered,
            "results": results,
        }

    except Exception as exc:
        logger.exception(
            "Telegram Auto Publisher cycle failed."
        )

        return {
            "processed": False,
            "status": "ERROR",
            "error": str(exc),
        }

    finally:
        # ----------------------------------------------------
        # RELEASE WORKER LOCK
        # ----------------------------------------------------

        if lock_acquired:
            release_worker_lock(db)

        db.close()


# ============================================================
# BACKGROUND WORKER
# ============================================================

async def auto_publisher_worker() -> None:
    """
    Long-running Telegram Auto Publisher worker.

    The first cycle runs immediately.

    Afterwards the worker executes once every 20 minutes.
    """

    logger.info(
        "Telegram Auto Publisher worker started."
    )

    # --------------------------------------------------------
    # INITIAL CYCLE
    # --------------------------------------------------------

    try:
        result = await asyncio.to_thread(
            run_auto_publisher_cycle
        )

        logger.info(
            "Initial Telegram Auto Publisher cycle: %s",
            result,
        )

    except Exception:
        logger.exception(
            "Initial Telegram Auto Publisher cycle failed."
        )

    # --------------------------------------------------------
    # SCHEDULED CYCLES
    # --------------------------------------------------------

    while True:
        try:
            await asyncio.sleep(
                AUTO_PUBLISH_INTERVAL_SECONDS
            )

            result = await asyncio.to_thread(
                run_auto_publisher_cycle
            )

            logger.info(
                "Telegram Auto Publisher cycle completed: %s",
                result,
            )

        except asyncio.CancelledError:
            logger.info(
                "Telegram Auto Publisher worker stopped."
            )
            raise

        except Exception:
            logger.exception(
                "Telegram Auto Publisher cycle failed."
            )


# ============================================================
# WORKER CONTROL
# ============================================================

_worker_task: asyncio.Task | None = None


async def start_auto_publisher() -> None:
    """
    Start the Telegram Auto Publisher background task.

    Safe to call multiple times.
    """

    global _worker_task

    if (
        _worker_task is not None
        and not _worker_task.done()
    ):
        logger.info(
            "Telegram Auto Publisher is already running."
        )
        return

    _worker_task = asyncio.create_task(
        auto_publisher_worker()
    )

    logger.info(
        "Telegram Auto Publisher task created."
    )


async def stop_auto_publisher() -> None:
    """
    Stop the Telegram Auto Publisher gracefully.
    """

    global _worker_task

    if _worker_task is None:
        return

    if not _worker_task.done():
        logger.info(
            "Stopping Telegram Auto Publisher..."
        )

        _worker_task.cancel()

        try:
            await _worker_task

        except asyncio.CancelledError:
            pass

    _worker_task = None

    logger.info(
        "Telegram Auto Publisher stopped."
    )
 
