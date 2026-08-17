import pytest
from fastapi.testclient import TestClient

EXPECTED_LEADERS = [
    "Alice Hartman",
    "Bob Sinclair",
    "Carol Nguyen",
    "David Okafor",
    "Eva Müller",
    "Frank Rossi",
    "Henry Patel",
]

EXPECTED_QUESTION_TEXTS = [
    "Entrega de Resultados",
    "Execução e Qualidade do Trabalho",
    "Capacidade de Aprendizado e Desenvolvimento",
    "Resolução de Problemas e Pensamento Crítico",
    "Colaboração, Influência e Liderança",
    "Visão Estratégica e Potencial de Crescimento",
]


@pytest.mark.integration
def test_leaders_is_public_and_returns_expected_employees(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/leaders")

    assert response.status_code == 200
    leaders = response.json()
    assert len(leaders) == 7
    assert [leader["name"] for leader in leaders] == EXPECTED_LEADERS
    assert all(set(leader) == {"id", "name", "positionName"} for leader in leaders)


@pytest.mark.integration
def test_leaders_excludes_leaf_employees(api_client: TestClient) -> None:
    response = api_client.get("/api/leaders")
    leader_names = {leader["name"] for leader in response.json()}

    assert "James Watanabe" not in leader_names
    assert "Tina Bergmann" not in leader_names


def test_evaluation_questions_is_public(api_client: TestClient) -> None:
    response = api_client.get("/api/evaluation/questions")

    assert response.status_code == 200


def test_evaluation_questions_match_fixed_challenge_data(
    api_client: TestClient,
) -> None:
    response = api_client.get("/api/evaluation/questions")
    questions = response.json()

    assert len(questions) == 6
    assert [question["displayOrder"] for question in questions] == [1, 2, 3, 4, 5, 6]
    assert [question["text"] for question in questions] == EXPECTED_QUESTION_TEXTS
    assert [question["weight"] for question in questions] == [25, 20, 20, 15, 10, 10]
    assert sum(question["weight"] for question in questions) == 100
