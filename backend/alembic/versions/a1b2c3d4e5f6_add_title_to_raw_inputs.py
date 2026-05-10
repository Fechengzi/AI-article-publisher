"""add title to raw_inputs

Revision ID: a1b2c3d4e5f6
Revises: 855843de6577
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "855843de6577"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "raw_inputs",
        sa.Column("title", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("raw_inputs", "title")
