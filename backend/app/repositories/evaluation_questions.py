from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EvaluationQuestion


class EvaluationQuestionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> list[EvaluationQuestion]:
        return list(
            self._session.scalars(
                select(EvaluationQuestion).order_by(EvaluationQuestion.display_order)
            )
        )
