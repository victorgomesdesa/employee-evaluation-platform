from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.repositories import EvaluationQuestionRepository
from app.schemas import EvaluationQuestionResponse

router = APIRouter(prefix="/api/evaluation", tags=["Avaliação"])


@router.get(
    "/questions",
    response_model=list[EvaluationQuestionResponse],
    summary="Listar perguntas de avaliação",
    response_description="Perguntas fixas da avaliação, ordenadas para exibição.",
)
def get_evaluation_questions(
    session: Session = Depends(get_session),
) -> list[EvaluationQuestionResponse]:
    repository = EvaluationQuestionRepository(session)
    questions = repository.get_all()

    return [
        EvaluationQuestionResponse(
            id=question.id,
            text=question.text,
            weight=question.weight,
            display_order=question.display_order,
        )
        for question in questions
    ]
