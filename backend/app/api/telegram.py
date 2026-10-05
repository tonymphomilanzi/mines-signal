import uuid
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
)
from sqlalchemy.orm import Session

from app.core.dependencies import (
    get_current_administrator,
)
from app.db.session import get_db
from app.models.administrator import Administrator
from app.schemas.telegram import (
    TelegramConfigurationResponse,
    TelegramMessageListResponse,
    TelegramMessageResponse,
    TelegramRetryResponse,
    TelegramStatusResponse,
    TelegramTestMessageRequest,
    TelegramTestMessageResponse,
    UpdateTelegramConfigurationRequest,
)
from app.services.telegram_service import (
    check_connection,
    get_or_create_configuration,
    get_telegram_message,
    get_telegram_messages,
    get_telegram_statistics,
    retry_telegram_message,
    send_test_message,
    update_configuration,
)


router = APIRouter(
    prefix="/api/telegram",
    tags=["Telegram"],
)


# ============================================================
# LIST
# ============================================================

@router.get(
    "",
    response_model=TelegramMessageListResponse,
)
def list_telegram_messages(
    limit: int = Query(
        default=50,
        ge=1,
        le=200,
    ),
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    messages = get_telegram_messages(
        db,
        limit=limit,
    )

    return TelegramMessageListResponse(
        items=messages,
        total=len(messages),
    )


# ============================================================
# DETAIL
# ============================================================

@router.get(
    "/messages/{message_id}",
    response_model=TelegramMessageResponse,
)
def get_telegram_message_endpoint(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    message = get_telegram_message(
        db,
        message_id,
    )

    if message is None:
        raise HTTPException(
            status_code=404,
            detail="Telegram message not found.",
        )

    return message


# ============================================================
# CONFIGURATION
# ============================================================

@router.get(
    "/config",
    response_model=TelegramConfigurationResponse,
)
def get_telegram_configuration(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    configuration = get_or_create_configuration(
        db
    )

    connection = check_connection(db)

    return TelegramConfigurationResponse(
        bot_name=(
            configuration.bot_name
            or connection.get("bot_name")
        ),
        channel_id=(
            configuration.channel_id
            or connection.get("channel_id")
        ),
        channel_name=(
            configuration.channel_name
            or connection.get("channel_name")
        ),
        channel_username=(
            configuration.channel_username
            or connection.get(
                "channel_username"
            )
        ),
        automatic_publishing=(
            configuration.automatic_publishing
        ),
        publish_confirmed_signals=(
            configuration.publish_confirmed_signals
        ),
        publish_results=(
            configuration.publish_results
        ),
        publishing_template=(
            configuration.publishing_template
        ),
        bot_configured=bool(
            connection.get("connected")
            and connection.get("bot_username")
        ),
        connected=bool(
            connection.get("connected")
        ),
    )


@router.patch(
    "/config",
    response_model=TelegramConfigurationResponse,
)
def update_telegram_configuration(
    payload: UpdateTelegramConfigurationRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    values = payload.model_dump(
        exclude_none=True
    )

    configuration = update_configuration(
        db,
        **values,
    )

    connection = check_connection(db)

    return TelegramConfigurationResponse(
        bot_name=(
            configuration.bot_name
            or connection.get("bot_name")
        ),
        channel_id=(
            configuration.channel_id
            or connection.get("channel_id")
        ),
        channel_name=(
            configuration.channel_name
            or connection.get("channel_name")
        ),
        channel_username=(
            configuration.channel_username
            or connection.get(
                "channel_username"
            )
        ),
        automatic_publishing=(
            configuration.automatic_publishing
        ),
        publish_confirmed_signals=(
            configuration.publish_confirmed_signals
        ),
        publish_results=(
            configuration.publish_results
        ),
        publishing_template=(
            configuration.publishing_template
        ),
        bot_configured=bool(
            connection.get("connected")
            and connection.get("bot_username")
        ),
        connected=bool(
            connection.get("connected")
        ),
    )


# ============================================================
# STATUS
# ============================================================

@router.get(
    "/status",
    response_model=TelegramStatusResponse,
)
def telegram_status(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    """
    Return the current Telegram bot and channel status.

    The database configuration is synchronized with the
    environment configuration by get_or_create_configuration().
    """

    connection = check_connection(db)

    return TelegramStatusResponse(
        configured=bool(
            connection.get("configured")
        ),
        connected=bool(
            connection.get("connected")
        ),
        bot_name=connection.get(
            "bot_name"
        ),
        bot_username=connection.get(
            "bot_username"
        ),
        channel_id=connection.get(
            "channel_id"
        ),
        channel_username=connection.get(
            "channel_username"
        ),
        checked_at=datetime.now(
            timezone.utc
        ),
    )


# ============================================================
# STATISTICS
# ============================================================

@router.get(
    "/statistics",
)
def telegram_statistics(
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    return get_telegram_statistics(db)


# ============================================================
# TEST MESSAGE
# ============================================================

 
 
@router.post(
    "/test",
    response_model=TelegramTestMessageResponse,
)
def telegram_test_message(
    payload: TelegramTestMessageRequest,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    try:
        configuration = get_or_create_configuration(
            db
        )

        channel_id = (
            configuration.channel_id
        )

        if not channel_id:
            raise RuntimeError(
                "Telegram channel ID is not configured."
            )

        result = send_test_message(
            payload.message,
            channel_id=channel_id,
        )

        telegram_result = (
            result.get("result") or {}
        )

        telegram_message_id = (
            telegram_result.get(
                "message_id"
            )
        )

        return TelegramTestMessageResponse(
            success=True,
            message=(
                "Test message sent successfully "
                "to the configured Telegram channel."
            ),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )
 

 
# ============================================================
# RETRY
# ============================================================

@router.post(
    "/messages/{message_id}/retry",
    response_model=TelegramRetryResponse,
)
def retry_telegram_message_endpoint(
    message_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_admin: Administrator = Depends(
        get_current_administrator
    ),
):
    try:
        message = retry_telegram_message(
            db,
            message_id,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return TelegramRetryResponse(
        message=(
            "Telegram message retry completed."
        ),
        telegram_message=message,
    )
 
