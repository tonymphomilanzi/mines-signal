"""merge ml predictions and telegram auto posts

Revision ID: 1f49ed6a5b6b
Revises: add_ml_predictions, add_telegram_auto_posts
Create Date: 2026-10-04 03:02:05.601255

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f49ed6a5b6b'
down_revision: Union[str, Sequence[str], None] = ('add_ml_predictions', 'add_telegram_auto_posts')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass