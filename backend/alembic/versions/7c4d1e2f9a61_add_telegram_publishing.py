"""add telegram publishing

Revision ID: 7c4d1e2f9a61
Revises: 690bf431dca3
Create Date: 2026-10-01 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7c4d1e2f9a61"
down_revision: Union[str, None] = "690bf431dca3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    # ========================================================
    # ENUM TYPES
    # ========================================================

    telegram_message_status = postgresql.ENUM(
        "PENDING",
        "PUBLISHED",
        "FAILED",
        name="telegram_message_status",
    )

    telegram_sync_status = postgresql.ENUM(
        "PENDING",
        "SYNCED",
        "FAILED",
        name="telegram_sync_status",
    )

    telegram_parse_status = postgresql.ENUM(
        "SUCCESS",
        "PARTIAL",
        "FAILED",
        name="telegram_parse_status",
    )

    telegram_message_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    telegram_sync_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    telegram_parse_status.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ========================================================
    # TELEGRAM CONFIGURATION
    # ========================================================

    op.create_table(
        "telegram_configuration",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "bot_name",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "channel_id",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "channel_name",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "channel_username",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "automatic_publishing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "publish_confirmed_signals",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "publish_results",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "publishing_template",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
    )

    # ========================================================
    # TELEGRAM MESSAGES
    # ========================================================

    op.create_table(
        "telegram_messages",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),

        sa.Column(
            "signal_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "telegram_message_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "channel_id",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "channel_name",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "channel_username",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "status",
            postgresql.ENUM(
                "PENDING",
                "PUBLISHED",
                "FAILED",
                name="telegram_message_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),

        sa.Column(
            "sync_status",
            postgresql.ENUM(
                "PENDING",
                "SYNCED",
                "FAILED",
                name="telegram_sync_status",
                create_type=False,
            ),
            nullable=False,
            server_default="PENDING",
        ),

        sa.Column(
            "parse_status",
            postgresql.ENUM(
                "SUCCESS",
                "PARTIAL",
                "FAILED",
                name="telegram_parse_status",
                create_type=False,
            ),
            nullable=False,
            server_default="SUCCESS",
        ),

        sa.Column(
            "message_text",
            sa.Text(),
            nullable=False,
        ),

        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "views",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "forwards",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),

        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "parsed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["signal_id"],
            ["signals.id"],
            ondelete="CASCADE",
        ),
    )

    # ========================================================
    # INDEXES
    # ========================================================

    op.create_index(
        "ix_telegram_messages_signal_id",
        "telegram_messages",
        ["signal_id"],
        unique=True,
    )

    op.create_index(
        "ix_telegram_messages_telegram_message_id",
        "telegram_messages",
        ["telegram_message_id"],
        unique=False,
    )

    op.create_index(
        "ix_telegram_messages_status",
        "telegram_messages",
        ["status"],
        unique=False,
    )

    # ========================================================
    # INITIAL CONFIGURATION
    # ========================================================

    op.execute(
        """
        INSERT INTO telegram_configuration (
            id,
            automatic_publishing,
            publish_confirmed_signals,
            publish_results,
            created_at,
            updated_at
        )
        VALUES (
            gen_random_uuid(),
            TRUE,
            TRUE,
            TRUE,
            NOW(),
            NOW()
        )
        """
    )


def downgrade() -> None:

    op.drop_index(
        "ix_telegram_messages_status",
        table_name="telegram_messages",
    )

    op.drop_index(
        "ix_telegram_messages_telegram_message_id",
        table_name="telegram_messages",
    )

    op.drop_index(
        "ix_telegram_messages_signal_id",
        table_name="telegram_messages",
    )

    op.drop_table(
        "telegram_messages"
    )

    op.drop_table(
        "telegram_configuration"
    )

    op.execute(
        "DROP TYPE IF EXISTS telegram_parse_status"
    )

    op.execute(
        "DROP TYPE IF EXISTS telegram_sync_status"
    )

    op.execute(
        "DROP TYPE IF EXISTS telegram_message_status"
    )
 
