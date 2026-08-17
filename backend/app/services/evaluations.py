from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.models import EvaluationQuestion
from app.repositories import (
    EvaluationAnswerData,
    EvaluationQuestionRepository,
    EvaluationRecord,
    EvaluationRepository,
    PrimaryEvaluationRecord,
    WeeklyEvaluationConflictError,
)
from app.services.hierarchy import HierarchyService
from app.utils import get_current_datetime, get_week_reference


class TargetEmployeeNotFoundError(Exception):
    pass


class EvaluationForbiddenError(Exception):
    pass


class EvaluationAlreadyExistsError(Exception):
    pass


class InvalidEvaluationAnswersError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class EvaluationAnswerInput:
    question_id: int
    score: int


class EvaluationService:
    def __init__(
        self,
        evaluation_repository: EvaluationRepository,
        question_repository: EvaluationQuestionRepository,
        hierarchy_service: HierarchyService,
        now_provider: Callable[[], datetime] = get_current_datetime,
    ) -> None:
        self._evaluation_repository = evaluation_repository
        self._question_repository = question_repository
        self._hierarchy_service = hierarchy_service
        self._now_provider = now_provider

    def create_evaluation(
        self,
        *,
        evaluator_id: int,
        employee_id: int,
        answers: Sequence[EvaluationAnswerInput],
    ) -> EvaluationRecord:
        target_employee = self._evaluation_repository.get_employee(employee_id)
        if target_employee is None:
            raise TargetEmployeeNotFoundError

        if not self._hierarchy_service.is_subordinate(evaluator_id, employee_id):
            raise EvaluationForbiddenError

        week_reference = get_week_reference(self._now_provider())
        if self._evaluation_repository.exists_for_week(
            evaluator_id,
            employee_id,
            week_reference,
        ):
            raise EvaluationAlreadyExistsError

        questions = self._question_repository.get_all()
        answer_data = self._validate_and_snapshot_answers(answers, questions)
        total_score = self._calculate_total_score(answer_data)

        try:
            return self._evaluation_repository.create(
                evaluator_id=evaluator_id,
                employee_id=employee_id,
                week_reference=week_reference,
                total_score=total_score,
                answers=answer_data,
            )
        except WeeklyEvaluationConflictError as error:
            raise EvaluationAlreadyExistsError from error

    def get_primary_evaluation(
        self,
        *,
        acting_employee_id: int,
        employee_id: int,
    ) -> PrimaryEvaluationRecord | None:
        target_employee = self._evaluation_repository.get_employee(employee_id)
        if target_employee is None:
            raise TargetEmployeeNotFoundError

        if not self._hierarchy_service.is_subordinate(
            acting_employee_id,
            employee_id,
        ):
            raise EvaluationForbiddenError

        return self._evaluation_repository.get_primary(employee_id)

    @staticmethod
    def _validate_and_snapshot_answers(
        answers: Sequence[EvaluationAnswerInput],
        questions: Sequence[EvaluationQuestion],
    ) -> list[EvaluationAnswerData]:
        if len(answers) != 6:
            raise InvalidEvaluationAnswersError(
                "A avaliação deve conter exatamente seis respostas."
            )

        question_by_id = {question.id: question for question in questions}
        submitted_ids = [answer.question_id for answer in answers]

        if len(set(submitted_ids)) != len(submitted_ids):
            raise InvalidEvaluationAnswersError(
                "Cada pergunta deve ser respondida uma única vez."
            )

        if set(submitted_ids) != set(question_by_id):
            raise InvalidEvaluationAnswersError(
                "Todas as perguntas válidas devem ser respondidas."
            )

        return [
            EvaluationAnswerData(
                question_id=answer.question_id,
                score=answer.score,
                weight=question_by_id[answer.question_id].weight,
            )
            for answer in answers
        ]

    @staticmethod
    def _calculate_total_score(answers: Sequence[EvaluationAnswerData]) -> Decimal:
        weighted_total = sum(
            (Decimal(answer.score) * Decimal(answer.weight) for answer in answers),
            start=Decimal("0"),
        )
        return (weighted_total / Decimal("100")).quantize(Decimal("0.01"))
