from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.employee import Employee
    from app.models.evaluation_answer import EvaluationAnswer


class Evaluation(Base):
    __tablename__ = "evaluation"
    __table_args__ = (
        UniqueConstraint(
            "evaluator_id",
            "employee_id",
            "week_reference",
            name="uq_evaluation_evaluator_employee_week",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluator_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", name="fk_evaluation_evaluator"),
        nullable=False,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey("employee.id", name="fk_evaluation_employee"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    week_reference: Mapped[date] = mapped_column(Date, nullable=False)
    total_score: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)

    evaluator: Mapped["Employee"] = relationship(
        back_populates="evaluations_as_evaluator",
        foreign_keys=[evaluator_id],
    )
    employee: Mapped["Employee"] = relationship(
        back_populates="evaluations_as_employee",
        foreign_keys=[employee_id],
    )
    answers: Mapped[list["EvaluationAnswer"]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
