from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from decimal import Decimal
from threading import Barrier
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.api.evaluations import get_evaluation_service
from app.config import settings
from app.database.session import get_session
from app.main import app
from app.models import Evaluation, EvaluationAnswer
from app.repositories import (
    EvaluationAnswerData,
    EvaluationQuestionRepository,
    EvaluationRepository,
    HierarchyRepository,
)
from app.services import EvaluationService, HierarchyService

FIXED_DATETIME = datetime(2026, 8, 19, 12, 0, tzinfo=ZoneInfo("America/Sao_Paulo"))
EXPECTED_WEIGHTS = [25, 20, 20, 15, 10, 10]


def valid_payload(employee_id: int = 4) -> dict[str, object]:
    return {
        "employeeId": employee_id,
        "answers": [
            {"questionId": 1, "score": 3},
            {"questionId": 2, "score": 3},
            {"questionId": 3, "score": 3},
            {"questionId": 4, "score": 3},
            {"questionId": 5, "score": 3},
            {"questionId": 6, "score": 4},
        ],
    }


def build_evaluation_service(session: Session) -> EvaluationService:
    return EvaluationService(
        evaluation_repository=EvaluationRepository(session),
        question_repository=EvaluationQuestionRepository(session),
        hierarchy_service=HierarchyService(HierarchyRepository(session)),
        now_provider=lambda: FIXED_DATETIME,
    )


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


@pytest.fixture
def evaluation_client(database_session: Session) -> Generator[TestClient, None, None]:
    app.dependency_overrides[get_session] = lambda: database_session
    app.dependency_overrides[get_evaluation_service] = lambda: build_evaluation_service(
        database_session
    )

    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()


def submit_evaluation(
    client: TestClient,
    *,
    leader_id: int = 2,
    payload: dict[str, object] | None = None,
):
    return client.post(
        "/api/evaluations",
        headers={"X-Leader-Id": str(leader_id)},
        json=payload or valid_payload(),
    )


@pytest.mark.integration
def test_direct_subordinate_evaluation_is_created_atomically(
    evaluation_client: TestClient,
    database_session: Session,
) -> None:
    response = submit_evaluation(evaluation_client)

    assert response.status_code == 201
    body = response.json()
    assert body["evaluatorId"] == 2
    assert body["employeeId"] == 4
    assert body["weekReference"] == "2026-08-17"
    assert body["totalScore"] == "3.10"
    assert len(body["answers"]) == 6
    assert [answer["weight"] for answer in body["answers"]] == EXPECTED_WEIGHTS
    assert database_session.scalar(select(func.count()).select_from(Evaluation)) == 1
    assert (
        database_session.scalar(select(func.count()).select_from(EvaluationAnswer))
        == 6
    )


@pytest.mark.integration
def test_indirect_subordinate_can_be_evaluated(
    evaluation_client: TestClient,
) -> None:
    response = submit_evaluation(
        evaluation_client,
        payload=valid_payload(employee_id=10),
    )

    assert response.status_code == 201
    assert response.json()["employeeId"] == 10


@pytest.mark.integration
@pytest.mark.parametrize(
    ("leader_id", "employee_id"),
    [
        (2, 2),
        (4, 5),
        (4, 2),
        (4, 18),
    ],
    ids=["self", "peer", "superior", "unrelated"],
)
def test_unauthorized_target_returns_forbidden(
    evaluation_client: TestClient,
    leader_id: int,
    employee_id: int,
) -> None:
    response = submit_evaluation(
        evaluation_client,
        leader_id=leader_id,
        payload=valid_payload(employee_id=employee_id),
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "Você não pode avaliar este funcionário."}


@pytest.mark.integration
def test_nonexistent_target_returns_not_found(evaluation_client: TestClient) -> None:
    response = submit_evaluation(
        evaluation_client,
        payload=valid_payload(employee_id=999999),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Funcionário não encontrado."}


@pytest.mark.integration
def test_missing_x_leader_id_returns_bad_request(
    evaluation_client: TestClient,
) -> None:
    response = evaluation_client.post("/api/evaluations", json=valid_payload())

    assert response.status_code == 400


@pytest.mark.integration
def test_malformed_x_leader_id_returns_bad_request(
    evaluation_client: TestClient,
) -> None:
    response = evaluation_client.post(
        "/api/evaluations",
        headers={"X-Leader-Id": "invalid"},
        json=valid_payload(),
    )

    assert response.status_code == 400


@pytest.mark.integration
def test_nonexistent_x_leader_id_returns_bad_request(
    evaluation_client: TestClient,
) -> None:
    response = evaluation_client.post(
        "/api/evaluations",
        headers={"X-Leader-Id": "999999"},
        json=valid_payload(),
    )

    assert response.status_code == 400


@pytest.mark.integration
def test_duplicate_weekly_evaluation_returns_conflict(
    evaluation_client: TestClient,
) -> None:
    first_response = submit_evaluation(evaluation_client)
    second_response = submit_evaluation(evaluation_client)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json() == {
        "detail": "Este funcionário já foi avaliado por este líder nesta semana."
    }


@pytest.mark.integration
def test_different_leaders_can_evaluate_same_employee_in_week(
    evaluation_client: TestClient,
) -> None:
    bob_response = submit_evaluation(
        evaluation_client,
        leader_id=2,
        payload=valid_payload(employee_id=8),
    )
    david_response = submit_evaluation(
        evaluation_client,
        leader_id=4,
        payload=valid_payload(employee_id=8),
    )

    assert bob_response.status_code == 201
    assert david_response.status_code == 201


@pytest.mark.integration
def test_same_leader_can_evaluate_different_employees_in_week(
    evaluation_client: TestClient,
) -> None:
    david_response = submit_evaluation(
        evaluation_client,
        payload=valid_payload(employee_id=4),
    )
    eva_response = submit_evaluation(
        evaluation_client,
        payload=valid_payload(employee_id=5),
    )

    assert david_response.status_code == 201
    assert eva_response.status_code == 201


@pytest.mark.parametrize(
    "answers",
    [
        valid_payload()["answers"][:5],
        valid_payload()["answers"] + [{"questionId": 1, "score": 3}],
    ],
    ids=["fewer", "more"],
)
def test_answer_count_must_be_exactly_six(
    evaluation_client: TestClient,
    answers: list[dict[str, object]],
) -> None:
    payload = valid_payload()
    payload["answers"] = answers

    response = submit_evaluation(evaluation_client, payload=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "answers",
    [
        [
            {"questionId": 1, "score": 3},
            {"questionId": 2, "score": 3},
            {"questionId": 3, "score": 3},
            {"questionId": 4, "score": 3},
            {"questionId": 5, "score": 3},
            {"questionId": 1, "score": 4},
        ],
        [
            {"questionId": 1, "score": 3},
            {"questionId": 2, "score": 3},
            {"questionId": 3, "score": 3},
            {"questionId": 4, "score": 3},
            {"questionId": 5, "score": 3},
            {"questionId": 999, "score": 4},
        ],
    ],
    ids=["duplicated-and-missing", "unknown-and-missing"],
)
def test_question_set_must_match_persisted_questions(
    evaluation_client: TestClient,
    answers: list[dict[str, object]],
) -> None:
    payload = valid_payload()
    payload["answers"] = answers

    response = submit_evaluation(evaluation_client, payload=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "invalid_score",
    [0, 5, -1, 2.5, "3", None, True, False],
    ids=["zero", "five", "negative", "float", "string", "null", "true", "false"],
)
def test_score_validation_is_strict(
    evaluation_client: TestClient,
    invalid_score: object,
) -> None:
    payload = valid_payload()
    payload["answers"][0]["score"] = invalid_score

    response = submit_evaluation(evaluation_client, payload=payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "Dados da requisição inválidos."}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("totalScore", 4),
        ("evaluatorId", 2),
        ("weekReference", "2026-08-17"),
        ("createdAt", "2026-08-19T12:00:00-03:00"),
    ],
)
def test_backend_controlled_request_fields_are_rejected(
    evaluation_client: TestClient,
    field: str,
    value: object,
) -> None:
    payload = valid_payload()
    payload[field] = value

    response = submit_evaluation(evaluation_client, payload=payload)

    assert response.status_code == 422


def test_client_provided_answer_weight_is_rejected(
    evaluation_client: TestClient,
) -> None:
    payload = valid_payload()
    payload["answers"][0]["weight"] = 25

    response = submit_evaluation(evaluation_client, payload=payload)

    assert response.status_code == 422


@pytest.mark.integration
def test_answer_failure_rolls_back_entire_evaluation(
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = EvaluationRepository(database_session)
    original_add_answers = repository._add_answers

    def fail_after_partial_answers(
        evaluation_id: int,
        answers: list[EvaluationAnswerData],
    ):
        partial_answers = original_add_answers(evaluation_id, answers[:3])
        database_session.flush()
        raise RuntimeError("Falha simulada ao persistir respostas.")

    monkeypatch.setattr(repository, "_add_answers", fail_after_partial_answers)
    answers = [
        EvaluationAnswerData(question_id=index, score=3, weight=weight)
        for index, weight in enumerate(EXPECTED_WEIGHTS, start=1)
    ]

    with pytest.raises(RuntimeError):
        repository.create(
            evaluator_id=2,
            employee_id=4,
            week_reference=date(2026, 8, 17),
            total_score=Decimal("3.00"),
            answers=answers,
        )

    assert database_session.scalar(select(func.count()).select_from(Evaluation)) == 0
    assert (
        database_session.scalar(select(func.count()).select_from(EvaluationAnswer))
        == 0
    )


@pytest.mark.integration
def test_unrelated_integrity_error_is_not_reported_as_weekly_conflict(
    database_session: Session,
) -> None:
    repository = EvaluationRepository(database_session)

    with pytest.raises(IntegrityError):
        repository.create(
            evaluator_id=2,
            employee_id=4,
            week_reference=date(2026, 8, 17),
            total_score=Decimal("3.00"),
            answers=[
                EvaluationAnswerData(
                    question_id=999999,
                    score=3,
                    weight=25,
                )
            ],
        )

    assert database_session.scalar(select(func.count()).select_from(Evaluation)) == 0


@pytest.mark.integration
def test_concurrent_identical_submissions_use_unique_constraint(
    database_session: Session,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert settings.test_database_url is not None
    session_factory = sessionmaker(
        bind=database_session.get_bind(),
        autoflush=False,
        autocommit=False,
    )
    barrier = Barrier(2)
    original_exists_for_week = EvaluationRepository.exists_for_week

    def synchronized_exists_for_week(
        repository: EvaluationRepository,
        evaluator_id: int,
        employee_id: int,
        week_reference: date,
    ) -> bool:
        result = original_exists_for_week(
            repository,
            evaluator_id,
            employee_id,
            week_reference,
        )
        barrier.wait(timeout=10)
        return result

    monkeypatch.setattr(
        EvaluationRepository,
        "exists_for_week",
        synchronized_exists_for_week,
    )

    def concurrent_session() -> Generator[Session, None, None]:
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = concurrent_session

    def send_request() -> int:
        with TestClient(app) as client:
            response = submit_evaluation(client)
            return response.status_code

    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            status_codes = list(executor.map(lambda _: send_request(), range(2)))
    finally:
        app.dependency_overrides.clear()

    database_session.expire_all()
    evaluation_count = database_session.scalar(
        select(func.count()).select_from(Evaluation)
    )

    assert sorted(status_codes) == [201, 409]
    assert evaluation_count == 1
