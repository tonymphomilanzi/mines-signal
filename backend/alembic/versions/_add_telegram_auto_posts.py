"""add telegram auto posts

Revision ID: add_telegram_auto_posts
Revises: 7c4d1e2f9a61
Create Date: 2026-10-02
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "add_telegram_auto_posts"
down_revision: Union[str, Sequence[str], None] = "7c4d1e2f9a61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------
    # ENUM: telegram_auto_post_content_type
    # ------------------------------------------------------------

    content_type_enum = postgresql.ENUM(
        "MESSAGE",
        "LINK",
        "VIDEO",
        "IMAGE",
        name="telegram_auto_post_content_type",
    )

    content_type_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ------------------------------------------------------------
    # ENUM: telegram_auto_post_status
    # ------------------------------------------------------------

    status_enum = postgresql.ENUM(
        "DRAFT",
        "QUEUED",
        "PUBLISHING",
        "PUBLISHED",
        "FAILED",
        "CANCELLED",
        name="telegram_auto_post_status",
    )

    status_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ------------------------------------------------------------
    # TABLE: telegram_auto_posts
    # ------------------------------------------------------------

    op.create_table(
        "telegram_auto_posts",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "content_type",
            postgresql.ENUM(
                "MESSAGE",
                "LINK",
                "VIDEO",
                "IMAGE",
                name="telegram_auto_post_content_type",
                create_type=False,
            ),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "link_url",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "media_url",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "caption",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "status",
            postgresql.ENUM(
                "DRAFT",
                "QUEUED",
                "PUBLISHING",
                "PUBLISHED",
                "FAILED",
                "CANCELLED",
                name="telegram_auto_post_status",
                create_type=False,
            ),
            nullable=False,
        ),

        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "scheduled_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.Column(
            "telegram_message_id",
            sa.Integer(),
            nullable=True,
        ),

        sa.Column(
            "channel_id",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "channel_username",
            sa.String(length=150),
            nullable=True,
        ),

        sa.Column(
            "attempts",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "error_message",
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

        sa.PrimaryKeyConstraint("id"),
    )

    # ------------------------------------------------------------
    # INDEXES
    # ------------------------------------------------------------

    op.create_index(
        "ix_telegram_auto_posts_content_type",
        "telegram_auto_posts",
        ["content_type"],
        unique=False,
    )

    op.create_index(
        "ix_telegram_auto_posts_status",
        "telegram_auto_posts",
        ["status"],
        unique=False,
    )

    op.create_index(
        "ix_telegram_auto_posts_is_active",
        "telegram_auto_posts",
        ["is_active"],
        unique=False,
    )

    op.create_index(
        "ix_telegram_auto_posts_scheduled_at",
        "telegram_auto_posts",
        ["scheduled_at"],
        unique=False,
    )

    op.create_index(
        "ix_telegram_auto_posts_telegram_message_id",
        "telegram_auto_posts",
        ["telegram_message_id"],
        unique=False,
    )


def downgrade() -> None:
    # ------------------------------------------------------------
    # DROP INDEXES
    # ------------------------------------------------------------

    op.drop_index(
        "ix_telegram_auto_posts_telegram_message_id",
        table_name="telegram_auto_posts",
    )

    op.drop_index(
        "ix_telegram_auto_posts_scheduled_at",
        table_name="telegram_auto_posts",
    )

    op.drop_index(
        "ix_telegram_auto_posts_is_active",
        table_name="telegram_auto_posts",
    )

    op.drop_index(
        "ix_telegram_auto_posts_status",
        table_name="telegram_auto_posts",
    )

    op.drop_index(
        "ix_telegram_auto_posts_content_type",
        table_name="telegram_auto_posts",
    )

    # ------------------------------------------------------------
    # DROP TABLE
    # ------------------------------------------------------------

    op.drop_table("telegram_auto_posts")

    # ------------------------------------------------------------
    # DROP ENUMS
    # ------------------------------------------------------------

    status_enum = postgresql.ENUM(
        "DRAFT",
        "QUEUED",
        "PUBLISHING",
        "PUBLISHED",
        "FAILED",
        "CANCELLED",
        name="telegram_auto_post_status",
    )

    status_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )

    content_type_enum = postgresql.ENUM(
        "MESSAGE",
        "LINK",
        "VIDEO",
        "IMAGE",
        name="telegram_auto_post_content_type",
    )

    content_type_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )
 
