from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Sequence

from sqlalchemy import exists, select, text
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


@dataclass(frozen=True, slots=True)
class EvaluatorRecord:
    id: int
    name: str
    position_name: str


@dataclass(frozen=True, slots=True)
class PrimaryEvaluationAnswerRecord:
    question_id: int
    question_text: str
    score: int
    weight: int


@dataclass(frozen=True, slots=True)
class PrimaryEvaluationRecord:
    id: int
    employee_id: int
    evaluator: EvaluatorRecord
    evaluator_depth: int
    week_reference: date
    created_at: datetime
    total_score: Decimal
    answers: tuple[PrimaryEvaluationAnswerRecord, ...]


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

    def get_global_depth(self, employee_id: int) -> int | None:
        query = text(
            """
            WITH RECURSIVE organization AS (
                SELECT
                    employee.id AS employee_id,
                    0 AS depth
                FROM employee
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM leader_lead
                    WHERE leader_lead.lead_id = employee.id
                )

                UNION ALL

                SELECT
                    leader_lead.lead_id AS employee_id,
                    organization.depth + 1 AS depth
                FROM leader_lead
                JOIN organization
                    ON leader_lead.leader_id = organization.employee_id
            )
            SELECT organization.depth
            FROM organization
            WHERE organization.employee_id = :employee_id
            """
        )
        return self._session.scalar(query, {"employee_id": employee_id})

    def get_primary(self, employee_id: int) -> PrimaryEvaluationRecord | None:
        query = text(
            """
            WITH RECURSIVE organization AS (
                SELECT
                    employee.id AS employee_id,
                    0 AS depth
                FROM employee
                WHERE NOT EXISTS (
                    SELECT 1
                    FROM leader_lead
                    WHERE leader_lead.lead_id = employee.id
                )

                UNION ALL

                SELECT
                    leader_lead.lead_id AS employee_id,
                    organization.depth + 1 AS depth
                FROM leader_lead
                JOIN organization
                    ON leader_lead.leader_id = organization.employee_id
            )
            SELECT
                evaluation.id,
                evaluation.employee_id,
                evaluation.evaluator_id,
                evaluator.name AS evaluator_name,
                evaluator.position_name AS evaluator_position_name,
                organization.depth AS evaluator_depth,
                evaluation.week_reference,
                evaluation.created_at,
                evaluation.total_score
            FROM evaluation
            JOIN employee AS evaluator
                ON evaluator.id = evaluation.evaluator_id
            JOIN organization
                ON organization.employee_id = evaluation.evaluator_id
            WHERE evaluation.employee_id = :employee_id
            ORDER BY
                evaluation.week_reference DESC,
                organization.depth ASC,
                evaluation.created_at DESC
            LIMIT 1
            """
        )
        row = self._session.execute(
            query,
            {"employee_id": employee_id},
        ).mappings().one_or_none()

        if row is None:
            return None

        answer_query = text(
            """
            SELECT
                evaluation_answer.question_id,
                evaluation_question.text AS question_text,
                evaluation_answer.score,
                evaluation_answer.weight
            FROM evaluation_answer
            JOIN evaluation_question
                ON evaluation_question.id = evaluation_answer.question_id
            WHERE evaluation_answer.evaluation_id = :evaluation_id
            ORDER BY evaluation_question.display_order
            """
        )
        answer_rows = self._session.execute(
            answer_query,
            {"evaluation_id": row["id"]},
        ).mappings()

        return PrimaryEvaluationRecord(
            id=row["id"],
            employee_id=row["employee_id"],
            evaluator=EvaluatorRecord(
                id=row["evaluator_id"],
                name=row["evaluator_name"],
                position_name=row["evaluator_position_name"],
            ),
            evaluator_depth=row["evaluator_depth"],
            week_reference=row["week_reference"],
            created_at=row["created_at"],
            total_score=row["total_score"],
            answers=tuple(
                PrimaryEvaluationAnswerRecord(
                    question_id=answer["question_id"],
                    question_text=answer["question_text"],
                    score=answer["score"],
                    weight=answer["weight"],
                )
                for answer in answer_rows
            ),
        )

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
