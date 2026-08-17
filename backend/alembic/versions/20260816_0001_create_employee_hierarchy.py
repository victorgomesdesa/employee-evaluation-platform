"""Create employee hierarchy tables.

Revision ID: 20260816_0001
Revises:
Create Date: 2026-08-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employee",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("position_name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "leader_lead",
        sa.Column("leader_id", sa.Integer(), nullable=False),
        sa.Column("lead_id", sa.Integer(), nullable=False),
        sa.CheckConstraint("leader_id <> lead_id", name="chk_no_self_lead"),
        sa.ForeignKeyConstraint(
            ["lead_id"],
            ["employee.id"],
            name="fk_lead",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["leader_id"],
            ["employee.id"],
            name="fk_leader",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("leader_id", "lead_id"),
    )


def downgrade() -> None:
    op.drop_table("leader_lead")
    op.drop_table("employee")
