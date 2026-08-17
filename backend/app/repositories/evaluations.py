from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import exists, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Employee, Evaluation, EvaluationAnswer

WEEKLY_UNIQUE_CONSTRAINT = "uq_evaluation_evaluator_employee_week"


class WeeklyEvaluationConflictError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class EvaluationAnswerData:
    question_id: int
    score: int
    weight: int


@dataclass(frozen=True, slots=True)
class EvaluationAnswerRecord:
    question_id: int
    score: int
    weight: int


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    id: int
    evaluator_id: int
    employee_id: int
    created_at: datetime
    week_reference: date
    total_score: Decimal
    answers: tuple[EvaluationAnswerRecord, ...]


class EvaluationRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_employee(self, employee_id: int) -> Employee | None:
        return self._session.get(Employee, employee_id)

    def exists_for_week(
        self,
        evaluator_id: int,
        employee_id: int,
        week_reference: date,
    ) -> bool:
        query = select(
            exists().where(
                Evaluation.evaluator_id == evaluator_id,
                Evaluation.employee_id == employee_id,
                Evaluation.week_reference == week_reference,
            )
        )
        return bool(self._session.scalar(query))

    def create(
        self,
        *,
        evaluator_id: int,
        employee_id: int,
        week_reference: date,
        total_score: Decimal,
        answers: Sequence[EvaluationAnswerData],
    ) -> EvaluationRecord:
        try:
            evaluation = Evaluation(
                evaluator_id=evaluator_id,
                employee_id=employee_id,
                week_reference=week_reference,
                total_score=total_score,
            )
            self._session.add(evaluation)
            self._session.flush()

            answer_models = self._add_answers(evaluation.id, answers)
            self._session.flush()

            record = EvaluationRecord(
                id=evaluation.id,
                evaluator_id=evaluation.evaluator_id,
                employee_id=evaluation.employee_id,
                created_at=evaluation.created_at,
                week_reference=evaluation.week_reference,
                total_score=evaluation.total_score,
                answers=tuple(
                    EvaluationAnswerRecord(
                        question_id=answer.question_id,
                        score=answer.score,
                        weight=answer.weight,
                    )
                    for answer in answer_models
                ),
            )
            self._session.commit()
            return record
        except IntegrityError as error:
            self._session.rollback()
            if self._get_constraint_name(error) == WEEKLY_UNIQUE_CONSTRAINT:
                raise WeeklyEvaluationConflictError from error
            raise
        except Exception:
            self._session.rollback()
            raise

    def _add_answers(
        self,
        evaluation_id: int,
        answers: Sequence[EvaluationAnswerData],
    ) -> list[EvaluationAnswer]:
        answer_models = [
            EvaluationAnswer(
                evaluation_id=evaluation_id,
                question_id=answer.question_id,
                score=answer.score,
                weight=answer.weight,
            )
            for answer in answers
        ]
        self._session.add_all(answer_models)
        return answer_models

    @staticmethod
    def _get_constraint_name(error: IntegrityError) -> str | None:
        diagnostic = getattr(error.orig, "diag", None)
        return getattr(diagnostic, "constraint_name", None)
