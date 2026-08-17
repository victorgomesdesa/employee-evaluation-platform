from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_acting_employee
from app.database.session import get_session
from app.models import Employee
from app.repositories import (
    EvaluationQuestionRepository,
    EvaluationRepository,
    HierarchyRepository,
)
from app.schemas import (
    EvaluationAnswerResponse,
    EvaluationCreate,
    EvaluationResponse,
)
from app.services import (
    EvaluationAlreadyExistsError,
    EvaluationAnswerInput,
    EvaluationForbiddenError,
    EvaluationService,
    HierarchyService,
    InvalidEvaluationAnswersError,
    TargetEmployeeNotFoundError,
)

router = APIRouter(prefix="/api", tags=["Avaliação"])


def get_evaluation_service(
    session: Session = Depends(get_session),
) -> EvaluationService:
    return EvaluationService(
        evaluation_repository=EvaluationRepository(session),
        question_repository=EvaluationQuestionRepository(session),
        hierarchy_service=HierarchyService(HierarchyRepository(session)),
    )


@router.post(
    "/evaluations",
    response_model=EvaluationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar avaliação",
    response_description="Avaliação registrada com suas seis respostas.",
)
def create_evaluation(
    request: EvaluationCreate,
    acting_employee: Employee = Depends(get_acting_employee),
    service: EvaluationService = Depends(get_evaluation_service),
) -> EvaluationResponse:
    try:
        record = service.create_evaluation(
            evaluator_id=acting_employee.id,
            employee_id=request.employee_id,
            answers=[
                EvaluationAnswerInput(
                    question_id=answer.question_id,
                    score=answer.score,
                )
                for answer in request.answers
            ],
        )
    except TargetEmployeeNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Funcionário não encontrado.",
        ) from error
    except EvaluationForbiddenError as error:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode avaliar este funcionário.",
        ) from error
    except EvaluationAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este funcionário já foi avaliado por este líder nesta semana.",
        ) from error
    except InvalidEvaluationAnswersError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error

    return EvaluationResponse(
        id=record.id,
        employee_id=record.employee_id,
        evaluator_id=record.evaluator_id,
        week_reference=record.week_reference,
        created_at=record.created_at,
        total_score=record.total_score,
        answers=[
            EvaluationAnswerResponse(
                question_id=answer.question_id,
                score=answer.score,
                weight=answer.weight,
            )
            for answer in record.answers
        ],
    )
