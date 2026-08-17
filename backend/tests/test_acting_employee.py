from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.database.session import get_session
from app.main import app
from app.repositories import HierarchyRepository


@pytest.mark.parametrize("header_value", ["", "abc", "1.5", "-2", "+2", " 2 ", "0"])
def test_malformed_x_leader_id_returns_bad_request(
    api_client: TestClient,
    header_value: str,
) -> None:
    response = api_client.get(
        "/api/me/subordinates",
        headers={"X-Leader-Id": header_value},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "X-Leader-Id deve ser um número inteiro válido."
    }


@pytest.mark.integration
def test_nonexistent_x_leader_id_returns_bad_request_before_business_logic(
    api_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_called(*args: object, **kwargs: object) -> None:
        raise AssertionError("A lógica de subordinados não deveria ser executada.")

    monkeypatch.setattr(HierarchyRepository, "get_subordinates", fail_if_called)
    response = api_client.get(
        "/api/me/subordinates",
        headers={"X-Leader-Id": "999999"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Funcionário informado em X-Leader-Id não existe."
    }


@pytest.mark.integration
def test_leaf_employee_is_valid_acting_employee(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/me/subordinates",
        headers={"X-Leader-Id": "10"},
    )

    assert response.status_code == 200
    assert response.json() == []


def test_malformed_x_leader_id_does_not_query_database() -> None:
    class FailOnLookupSession:
        def get(self, *args: object, **kwargs: object) -> None:
            raise AssertionError("A consulta ao banco não deveria ocorrer.")

    app.dependency_overrides[get_session] = lambda: FailOnLookupSession()

    try:
        with TestClient(app) as client:
            malformed_response = client.get(
                "/api/me/subordinates",
                headers={"X-Leader-Id": "invalid"},
            )
            missing_response = client.get("/api/me/subordinates")
    finally:
        app.dependency_overrides.clear()

    assert malformed_response.status_code == 400
    assert missing_response.status_code == 400
