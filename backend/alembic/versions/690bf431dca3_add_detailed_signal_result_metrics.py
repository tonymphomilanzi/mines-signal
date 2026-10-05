"""add detailed signal result metrics

Revision ID: 690bf431dca3
Revises: 348fc00cc407
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "690bf431dca3"
down_revision: Union[str, Sequence[str], None] = "348fc00cc407"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "results",
        sa.Column(
            "correct_safe_predictions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "results",
        sa.Column(
            "incorrect_safe_predictions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "results",
        sa.Column(
            "correct_mine_predictions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    op.add_column(
        "results",
        sa.Column(
            "incorrect_mine_predictions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )

    # Remove the database defaults after existing rows
    # have been populated with zero.
    op.alter_column(
        "results",
        "correct_safe_predictions",
        server_default=None,
    )

    op.alter_column(
        "results",
        "incorrect_safe_predictions",
        server_default=None,
    )

    op.alter_column(
        "results",
        "correct_mine_predictions",
        server_default=None,
    )

    op.alter_column(
        "results",
        "incorrect_mine_predictions",
        server_default=None,
    )


def downgrade() -> None:
    op.drop_column(
        "results",
        "incorrect_mine_predictions",
    )

    op.drop_column(
        "results",
        "correct_mine_predictions",
    )

    op.drop_column(
        "results",
        "incorrect_safe_predictions",
    )

    op.drop_column(
        "results",
        "correct_safe_predictions",
    )
 
