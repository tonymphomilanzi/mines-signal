"""add prediction engine to signals

Revision ID: c4cfec6b6271
Revises: 1f49ed6a5b6b
Create Date: 2026-10-04 03:09:50.588047
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "c4cfec6b6271"
down_revision: Union[str, Sequence[str], None] = "1f49ed6a5b6b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ============================================================
    # ENUM: prediction_engine
    # ============================================================

    prediction_engine_enum = postgresql.ENUM(
        "PATTERN",
        "ML",
        name="prediction_engine",
    )

    prediction_engine_enum.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ============================================================
    # COLUMN: signals.prediction_engine
    # ============================================================

    op.add_column(
        "signals",
        sa.Column(
            "prediction_engine",
            postgresql.ENUM(
                "PATTERN",
                "ML",
                name="prediction_engine",
                create_type=False,
            ),
            nullable=False,
            server_default="PATTERN",
        ),
    )

    # ============================================================
    # INDEX
    # ============================================================

    op.create_index(
        "ix_signals_prediction_engine",
        "signals",
        ["prediction_engine"],
        unique=False,
    )

    # ============================================================
    # REMOVE SERVER DEFAULT
    #
    # Existing signals have already received PATTERN.
    # Future application inserts will use the SQLAlchemy
    # model default instead.
    # ============================================================

    op.alter_column(
        "signals",
        "prediction_engine",
        server_default=None,
    )


def downgrade() -> None:
    # ============================================================
    # DROP INDEX
    # ============================================================

    op.drop_index(
        "ix_signals_prediction_engine",
        table_name="signals",
    )

    # ============================================================
    # DROP COLUMN
    # ============================================================

    op.drop_column(
        "signals",
        "prediction_engine",
    )

    # ============================================================
    # DROP ENUM
    # ============================================================

    prediction_engine_enum = postgresql.ENUM(
        "PATTERN",
        "ML",
        name="prediction_engine",
    )

    prediction_engine_enum.drop(
        op.get_bind(),
        checkfirst=True,
    )
 
