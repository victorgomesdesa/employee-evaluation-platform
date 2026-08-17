from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.employee import Employee


class LeaderLead(Base):
    __tablename__ = "leader_lead"
    __table_args__ = (
        CheckConstraint("leader_id <> lead_id", name="chk_no_self_lead"),
    )

    leader_id: Mapped[int] = mapped_column(
        ForeignKey(
            "employee.id",
            name="fk_leader",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )
    lead_id: Mapped[int] = mapped_column(
        ForeignKey(
            "employee.id",
            name="fk_lead",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        primary_key=True,
    )

    leader: Mapped["Employee"] = relationship(
        back_populates="leading_links",
        foreign_keys=[leader_id],
    )
    lead: Mapped["Employee"] = relationship(
        back_populates="reporting_links",
        foreign_keys=[lead_id],
    )
