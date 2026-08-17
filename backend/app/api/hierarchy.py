from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_acting_employee
from app.database.session import get_session
from app.models import Employee
from app.repositories import HierarchyRepository
from app.schemas import SubordinateResponse
from app.services import HierarchyService

router = APIRouter(prefix="/api/me", tags=["Hierarquia"])


@router.get(
    "/subordinates",
    response_model=list[SubordinateResponse],
    summary="Listar subordinados",
    response_description="Subordinados diretos e indiretos do funcionário atuante.",
)
def get_subordinates(
    acting_employee: Employee = Depends(get_acting_employee),
    session: Session = Depends(get_session),
) -> list[SubordinateResponse]:
    repository = HierarchyRepository(session)
    service = HierarchyService(repository)
    return service.get_subordinates(acting_employee.id)
