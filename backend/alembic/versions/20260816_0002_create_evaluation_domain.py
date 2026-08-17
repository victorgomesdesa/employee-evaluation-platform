"""Create evaluation domain tables.

Revision ID: 20260816_0002
Revises: 20260816_0001
Create Date: 2026-08-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260816_0002"
down_revision: Union[str, None] = "20260816_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_question",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "evaluation",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evaluator_id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("week_reference", sa.Date(), nullable=False),
        sa.Column("total_score", sa.Numeric(precision=4, scale=2), nullable=False),
        sa.ForeignKeyConstraint(
            ["employee_id"],
            ["employee.id"],
            name="fk_evaluation_employee",
        ),
        sa.ForeignKeyConstraint(
            ["evaluator_id"],
            ["employee.id"],
            name="fk_evaluation_evaluator",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "evaluator_id",
            "employee_id",
            "week_reference",
            name="uq_evaluation_evaluator_employee_week",
        ),
    )
    op.create_table(
        "evaluation_answer",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("evaluation_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.CheckConstraint(
            "score BETWEEN 1 AND 4",
            name="chk_evaluation_answer_score",
        ),
        sa.ForeignKeyConstraint(
            ["evaluation_id"],
            ["evaluation.id"],
            name="fk_evaluation_answer_evaluation",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["evaluation_question.id"],
            name="fk_evaluation_answer_question",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("evaluation_answer")
    op.drop_table("evaluation")
    op.drop_table("evaluation_question")
