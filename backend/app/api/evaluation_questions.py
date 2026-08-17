from fastapi import APIRouter

from app.data import EVALUATION_QUESTIONS
from app.schemas import EvaluationQuestionResponse

router = APIRouter(prefix="/api/evaluation", tags=["Avaliação"])


@router.get(
    "/questions",
    response_model=list[EvaluationQuestionResponse],
    summary="Listar perguntas de avaliação",
    response_description="Perguntas fixas da avaliação, ordenadas para exibição.",
)
def get_evaluation_questions() -> tuple[EvaluationQuestionResponse, ...]:
    return EVALUATION_QUESTIONS
