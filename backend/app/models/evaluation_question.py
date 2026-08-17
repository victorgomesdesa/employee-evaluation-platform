from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.evaluation_answer import EvaluationAnswer


class EvaluationQuestion(Base):
    __tablename__ = "evaluation_question"

    id: Mapped[int] = mapped_column(primary_key=True)
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    weight: Mapped[int] = mapped_column(nullable=False)
    display_order: Mapped[int] = mapped_column(nullable=False)

    answers: Mapped[list["EvaluationAnswer"]] = relationship(
        back_populates="question",
        passive_deletes=True,
    )
