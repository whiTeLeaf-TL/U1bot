""" """

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "aslfjlas132412"
down_revision: str | Sequence[str] | None = "68463f3e5f33"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    op.alter_column(
        "nonebot_plugin_fishing_fishingrecord",
        "coin",
        existing_type=sa.Float(),
        type_=sa.Float(),
        nullable=False,
    )
