"""Update version

迁移 ID: 68463f3e5f33
父迁移: 7609e6d106dd
创建时间: 2024-04-13 01:21:12.144452

"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "68463f3e5f33"
down_revision: str | Sequence[str] | None = "7609e6d106dd"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade(name: str = "") -> None:
    if name:
        return
    op.create_table(
        "nonebot_plugin_fishing_fishingswitch",
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("switch", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint(
            "group_id", name=op.f("pk_nnonebot_plugin_fishing_fishingswitch")
        ),
        info={"bind_key": "nonebot_plugin_fishing"},
    )
    # ### end Alembic commands ###


def downgrade(name: str = "") -> None:
    if name:
        return
    op.drop_table("nonebot_plugin_fishing_fishingswitch")
    # ### end Alembic commands ###
