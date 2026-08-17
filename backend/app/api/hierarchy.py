from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_session
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
    acting_employee_id: Annotated[
        str | None,
        Query(
            alias="actingEmployeeId",
            description="Identificador temporário do funcionário atuante.",
        ),
    ] = None,
    session: Session = Depends(get_session),
) -> list[SubordinateResponse]:
    if acting_employee_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O identificador do funcionário atuante é obrigatório.",
        )

    try:
        leader_id = int(acting_employee_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O identificador do funcionário atuante deve ser um número inteiro.",
        ) from error

    if leader_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O identificador do funcionário atuante deve ser positivo.",
        )

    repository = HierarchyRepository(session)
    service = HierarchyService(repository)
    return service.get_subordinates(leader_id)
