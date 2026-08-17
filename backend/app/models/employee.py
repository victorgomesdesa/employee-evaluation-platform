from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.leader_lead import LeaderLead


class Employee(Base):
    __tablename__ = "employee"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    position_name: Mapped[str] = mapped_column(String(100), nullable=False)

    leading_links: Mapped[list["LeaderLead"]] = relationship(
        back_populates="leader",
        foreign_keys="LeaderLead.leader_id",
        passive_deletes=True,
    )
    reporting_links: Mapped[list["LeaderLead"]] = relationship(
        back_populates="lead",
        foreign_keys="LeaderLead.lead_id",
        passive_deletes=True,
    )
    evaluations_as_evaluator: Mapped[list["Evaluation"]] = relationship(
        back_populates="evaluator",
        foreign_keys="Evaluation.evaluator_id",
        passive_deletes=True,
    )
    evaluations_as_employee: Mapped[list["Evaluation"]] = relationship(
        back_populates="employee",
        foreign_keys="Evaluation.employee_id",
        passive_deletes=True,
    )
