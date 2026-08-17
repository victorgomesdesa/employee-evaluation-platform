import pytest
from fastapi.testclient import TestClient


def get_subordinates(client: TestClient, employee_id: int) -> list[dict[str, object]]:
    response = client.get(
        "/api/me/subordinates",
        headers={"X-Leader-Id": str(employee_id)},
    )

    assert response.status_code == 200
    return response.json()


@pytest.mark.integration
def test_bob_returns_twelve_subordinates(api_client: TestClient) -> None:
    subordinates = get_subordinates(api_client, 2)

    assert len(subordinates) == 12
    assert set(subordinates[0]) == {
        "id",
        "name",
        "email",
        "positionName",
        "relationship",
        "depth",
    }


@pytest.mark.integration
def test_bob_returns_five_direct_and_seven_indirect_subordinates(
    api_client: TestClient,
) -> None:
    subordinates = get_subordinates(api_client, 2)
    direct = {item["name"] for item in subordinates if item["relationship"] == "direct"}
    indirect = {
        item["name"] for item in subordinates if item["relationship"] == "indirect"
    }

    assert direct == {
        "David Okafor",
        "Eva Müller",
        "Grace Kim",
        "Paul Nakamura",
        "Quinn Santos",
    }
    assert indirect == {
        "Henry Patel",
        "Isabelle Dubois",
        "James Watanabe",
        "Karen Oliveira",
        "Liam Johansson",
        "Mia Fernandez",
        "Noah Chukwu",
    }


@pytest.mark.integration
def test_david_returns_expected_subordinates(api_client: TestClient) -> None:
    subordinates = get_subordinates(api_client, 4)

    assert {item["name"] for item in subordinates} == {
        "Henry Patel",
        "Liam Johansson",
        "James Watanabe",
        "Karen Oliveira",
    }


@pytest.mark.integration
def test_henry_returns_james_and_karen(api_client: TestClient) -> None:
    subordinates = get_subordinates(api_client, 8)

    assert {item["name"] for item in subordinates} == {
        "James Watanabe",
        "Karen Oliveira",
    }


@pytest.mark.integration
def test_james_returns_empty_list(api_client: TestClient) -> None:
    assert get_subordinates(api_client, 10) == []


@pytest.mark.integration
def test_david_excludes_self_peers_superiors_and_unrelated_employees(
    api_client: TestClient,
) -> None:
    subordinate_names = {
        item["name"] for item in get_subordinates(api_client, 4)
    }

    assert "David Okafor" not in subordinate_names
    assert "Eva Müller" not in subordinate_names
    assert "Bob Sinclair" not in subordinate_names
    assert "Alice Hartman" not in subordinate_names
    assert "Carol Nguyen" not in subordinate_names
    assert "Frank Rossi" not in subordinate_names


@pytest.mark.integration
def test_bob_returns_correct_relative_depth(api_client: TestClient) -> None:
    subordinates = get_subordinates(api_client, 2)
    depth_by_name = {item["name"]: item["depth"] for item in subordinates}

    assert depth_by_name == {
        "David Okafor": 1,
        "Eva Müller": 1,
        "Grace Kim": 1,
        "Paul Nakamura": 1,
        "Quinn Santos": 1,
        "Henry Patel": 2,
        "Isabelle Dubois": 2,
        "Liam Johansson": 2,
        "Mia Fernandez": 2,
        "Noah Chukwu": 2,
        "James Watanabe": 3,
        "Karen Oliveira": 3,
    }


@pytest.mark.integration
def test_relationship_matches_relative_depth(api_client: TestClient) -> None:
    subordinates = get_subordinates(api_client, 1)

    assert all(
        item["relationship"] == ("direct" if item["depth"] == 1 else "indirect")
        for item in subordinates
    )


def test_subordinates_requires_x_leader_id(api_client: TestClient) -> None:
    response = api_client.get(
        "/api/me/subordinates",
        params={"actingEmployeeId": 2},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "X-Leader-Id é obrigatório."}
