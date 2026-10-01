"""add node graph position columns

Revision ID: 6a27cd1492e5
Revises: f35e5edeb94f
Create Date: 2026-08-21 00:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "6a27cd1492e5"
down_revision: Union[str, None] = "f35e5edeb94f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("knowledge_nodes", sa.Column("position_x", sa.Float(), nullable=True))
    op.add_column("knowledge_nodes", sa.Column("position_y", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_nodes", "position_y")
    op.drop_column("knowledge_nodes", "position_x")
