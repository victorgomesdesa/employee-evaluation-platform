from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.repositories import HierarchyRepository
from app.schemas import LeaderResponse
from app.services import HierarchyService

router = APIRouter(prefix="/api", tags=["Líderes"])


@router.get(
    "/leaders",
    response_model=list[LeaderResponse],
    summary="Listar líderes",
    response_description="Líderes disponíveis para seleção.",
)
def get_leaders(session: Session = Depends(get_session)) -> list[LeaderResponse]:
    repository = HierarchyRepository(session)
    service = HierarchyService(repository)
    return service.get_leaders()
