"""add ml predictions

Revision ID: add_ml_predictions
Revises: <PREVIOUS_REVISION_ID>
Create Date: 2026-10-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "add_ml_predictions"

down_revision: Union[
    str,
    Sequence[str],
    None,
] = "7c4d1e2f9a61"

branch_labels: Union[
    str,
    Sequence[str],
    None,
] = None

depends_on: Union[
    str,
    Sequence[str],
    None,
] = None


def upgrade() -> None:
    op.create_table(
        "ml_predictions",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "signal_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "model_name",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "model_version",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "feature_version",
            sa.String(length=50),
            nullable=False,
        ),

        sa.Column(
            "board_size",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "mine_count",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "top_positions",
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
        ),

        sa.Column(
            "position_predictions",
            postgresql.JSONB(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["signal_id"],
            ["signals.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_ml_predictions_signal_id",
        "ml_predictions",
        ["signal_id"],
        unique=False,
    )

    op.create_index(
        "ix_ml_predictions_model_name",
        "ml_predictions",
        ["model_name"],
        unique=False,
    )

    op.create_index(
        "ix_ml_predictions_created_at",
        "ml_predictions",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_ml_predictions_created_at",
        table_name="ml_predictions",
    )

    op.drop_index(
        "ix_ml_predictions_model_name",
        table_name="ml_predictions",
    )

    op.drop_index(
        "ix_ml_predictions_signal_id",
        table_name="ml_predictions",
    )

    op.drop_table("ml_predictions")
 
