import re
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_session
from app.models import Employee

VALID_EMPLOYEE_ID = re.compile(r"[0-9]+")


def get_acting_employee(
    x_leader_id: Annotated[
        str | None,
        Header(alias="X-Leader-Id"),
    ] = None,
    session: Session = Depends(get_session),
) -> Employee:
    if x_leader_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Leader-Id é obrigatório.",
        )

    if VALID_EMPLOYEE_ID.fullmatch(x_leader_id) is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Leader-Id deve ser um número inteiro válido.",
        )

    employee_id = int(x_leader_id)
    if employee_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Leader-Id deve ser um número inteiro válido.",
        )

    employee = session.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Funcionário informado em X-Leader-Id não existe.",
        )

    return employee
