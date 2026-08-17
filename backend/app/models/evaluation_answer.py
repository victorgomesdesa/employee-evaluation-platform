from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.evaluation import Evaluation
    from app.models.evaluation_question import EvaluationQuestion


class EvaluationAnswer(Base):
    __tablename__ = "evaluation_answer"
    __table_args__ = (
        CheckConstraint("score BETWEEN 1 AND 4", name="chk_evaluation_answer_score"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey(
            "evaluation.id",
            name="fk_evaluation_answer_evaluation",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    question_id: Mapped[int] = mapped_column(
        ForeignKey(
            "evaluation_question.id",
            name="fk_evaluation_answer_question",
        ),
        nullable=False,
    )
    score: Mapped[int] = mapped_column(nullable=False)
    weight: Mapped[int] = mapped_column(nullable=False)

    evaluation: Mapped["Evaluation"] = relationship(back_populates="answers")
    question: Mapped["EvaluationQuestion"] = relationship(back_populates="answers")
