from collections.abc import Generator
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import Evaluation, EvaluationAnswer
from app.repositories import EvaluationRepository

QUESTION_TEXTS = [
    "Entrega de Resultados",
    "Execução e Qualidade do Trabalho",
    "Capacidade de Aprendizado e Desenvolvimento",
    "Resolução de Problemas e Pensamento Crítico",
    "Colaboração, Influência e Liderança",
    "Visão Estratégica e Potencial de Crescimento",
]
QUESTION_WEIGHTS = [25, 20, 20, 15, 10, 10]


@pytest.fixture(autouse=True)
def clean_evaluations(database_session: Session) -> Generator[None, None, None]:
    database_session.rollback()
    database_session.execute(delete(EvaluationAnswer))
    database_session.execute(delete(Evaluation))
    database_session.commit()

    yield

    database_session.rollback()
    database_session.execute(delete(EvaluationAnswer))
    database_session.execute(delete(Evaluation))
    database_session.commit()


def create_evaluation(
    session: Session,
    *,
    evaluator_id: int,
    employee_id: int,
    week_reference: date,
    created_at: datetime,
    total_score: Decimal = Decimal("3.10"),
    first_answer_weight: int = 25,
) -> int:
    evaluation = Evaluation(
        evaluator_id=evaluator_id,
        employee_id=employee_id,
        week_reference=week_reference,
        created_at=created_at,
        total_score=total_score,
    )
    session.add(evaluation)
    session.flush()
    evaluation_id = evaluation.id

    for question_id in range(6, 0, -1):
        weight = (
            first_answer_weight
            if question_id == 1
            else QUESTION_WEIGHTS[question_id - 1]
        )
        session.add(
            EvaluationAnswer(
                evaluation_id=evaluation_id,
                question_id=question_id,
                score=3,
                weight=weight,
            )
        )

    session.commit()
    return evaluation_id


def get_latest_evaluation(
    client: TestClient,
    *,
    acting_employee_id: int,
    employee_id: int,
):
    return client.get(
        f"/api/employees/{employee_id}/evaluations/latest",
        headers={"X-Leader-Id": str(acting_employee_id)},
    )


@pytest.mark.integration
def test_direct_subordinate_with_evaluation_returns_selected_record(
    api_client: TestClient,
    database_session: Session,
) -> None:
    evaluation_id = create_evaluation(
        database_session,
        evaluator_id=2,
        employee_id=4,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 19, 15, 0, tzinfo=timezone.utc),
        first_answer_weight=99,
    )

    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=4,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == evaluation_id
    assert body["employeeId"] == 4
    assert body["evaluator"] == {
        "id": 2,
        "name": "Bob Sinclair",
        "positionName": "CTO",
    }
    assert body["totalScore"] == "3.10"
    assert len(body["answers"]) == 6
    assert [answer["questionId"] for answer in body["answers"]] == [1, 2, 3, 4, 5, 6]
    assert [answer["questionText"] for answer in body["answers"]] == QUESTION_TEXTS
    assert body["answers"][0]["weight"] == 99


@pytest.mark.integration
def test_indirect_subordinate_with_evaluation_returns_ok(
    api_client: TestClient,
    database_session: Session,
) -> None:
    create_evaluation(
        database_session,
        evaluator_id=2,
        employee_id=10,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 19, 15, 0, tzinfo=timezone.utc),
    )

    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=10,
    )

    assert response.status_code == 200
    assert response.json()["employeeId"] == 10


@pytest.mark.integration
def test_subordinate_without_evaluation_returns_null(api_client: TestClient) -> None:
    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=5,
    )

    assert response.status_code == 200
    assert response.json() is None


def test_latest_evaluation_requires_acting_identity(api_client: TestClient) -> None:
    response = api_client.get("/api/employees/4/evaluations/latest")

    assert response.status_code == 400
    assert response.json() == {"detail": "X-Leader-Id é obrigatório."}


@pytest.mark.integration
def test_nonexistent_target_returns_not_found(api_client: TestClient) -> None:
    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=999999,
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Funcionário não encontrado."}


@pytest.mark.integration
@pytest.mark.parametrize(
    ("acting_employee_id", "employee_id"),
    [(2, 2), (4, 5), (4, 2), (4, 18)],
    ids=["self", "peer", "superior", "unrelated"],
)
def test_unauthorized_target_returns_forbidden(
    api_client: TestClient,
    acting_employee_id: int,
    employee_id: int,
) -> None:
    response = get_latest_evaluation(
        api_client,
        acting_employee_id=acting_employee_id,
        employee_id=employee_id,
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Você não pode visualizar as avaliações deste funcionário."
    }


@pytest.mark.integration
def test_most_recent_week_wins_before_evaluator_hierarchy(
    api_client: TestClient,
    database_session: Session,
) -> None:
    create_evaluation(
        database_session,
        evaluator_id=2,
        employee_id=8,
        week_reference=date(2026, 8, 10),
        created_at=datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
    )
    david_evaluation_id = create_evaluation(
        database_session,
        evaluator_id=4,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 19, 15, 0, tzinfo=timezone.utc),
    )

    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=8,
    )

    assert response.status_code == 200
    assert response.json()["id"] == david_evaluation_id
    assert response.json()["evaluator"]["id"] == 4


@pytest.mark.integration
def test_higher_ranking_evaluator_wins_within_same_week(
    api_client: TestClient,
    database_session: Session,
) -> None:
    bob_evaluation_id = create_evaluation(
        database_session,
        evaluator_id=2,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc),
    )
    create_evaluation(
        database_session,
        evaluator_id=4,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 20, 15, 0, tzinfo=timezone.utc),
    )

    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=8,
    )

    assert response.status_code == 200
    assert response.json()["id"] == bob_evaluation_id
    assert response.json()["evaluator"]["id"] == 2


@pytest.mark.integration
def test_lower_level_viewer_can_see_higher_level_primary_evaluation(
    api_client: TestClient,
    database_session: Session,
) -> None:
    bob_evaluation_id = create_evaluation(
        database_session,
        evaluator_id=2,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc),
    )
    create_evaluation(
        database_session,
        evaluator_id=4,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 20, 15, 0, tzinfo=timezone.utc),
    )

    response = get_latest_evaluation(
        api_client,
        acting_employee_id=4,
        employee_id=8,
    )

    assert response.status_code == 200
    assert response.json()["id"] == bob_evaluation_id
    assert response.json()["evaluator"]["id"] == 2


@pytest.mark.integration
def test_same_depth_tie_uses_newest_created_at(
    api_client: TestClient,
    database_session: Session,
) -> None:
    create_evaluation(
        database_session,
        evaluator_id=2,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 18, 15, 0, tzinfo=timezone.utc),
    )
    newest_evaluation_id = create_evaluation(
        database_session,
        evaluator_id=3,
        employee_id=8,
        week_reference=date(2026, 8, 17),
        created_at=datetime(2026, 8, 20, 15, 0, tzinfo=timezone.utc),
    )

    response = get_latest_evaluation(
        api_client,
        acting_employee_id=2,
        employee_id=8,
    )

    assert response.status_code == 200
    assert response.json()["id"] == newest_evaluation_id
    assert response.json()["evaluator"]["id"] == 3


@pytest.mark.integration
def test_global_organizational_depths_match_fixture(database_session: Session) -> None:
    repository = EvaluationRepository(database_session)

    assert repository.get_global_depth(1) == 0
    assert repository.get_global_depth(2) == 1
    assert repository.get_global_depth(4) == 2
    assert repository.get_global_depth(8) == 3
    assert repository.get_global_depth(10) == 4


def test_evaluation_routes_are_immutable(api_client: TestClient) -> None:
    evaluation_paths = {
        path: operations
        for path, operations in api_client.app.openapi()["paths"].items()
        if "evaluations" in path
    }

    assert evaluation_paths
    assert all(
        {"put", "patch", "delete"}.isdisjoint(operations)
        for operations in evaluation_paths.values()
    )
