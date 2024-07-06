""" """

from __future__ import annotations

from collections.abc import Sequence

from alembic.op import add_column
import sqlalchemy as sa

revision: str = "132fd421135"
down_revision: str | Sequence[str] | None = "aslfjlas132412"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    add_column(
        "nonebot_plugin_fishing_fishingrecord",
        sa.Column("count_coin", sa.Float(), nullable=False),
    )
