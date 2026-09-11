from fastapi.testclient import TestClient

from bk_exp.api.main import app

client = TestClient(app)


def test_tour_returns_primary_route_and_all_points() -> None:
    response = client.get("/api/tours/biggie")

    assert response.status_code == 200
    body = response.json()
    assert body["character"] == "biggie"
    assert len(body["primary_route"]) >= 1
    assert len(body["all_points"]) >= 4


def test_feedback_changes_preference_weight() -> None:
    payload = {"session_id": "test-preference", "character": "rbg", "feedback_type": "accepted"}

    response = client.post("/api/feedback", json=payload)

    assert response.status_code == 200
    assert response.json()["character_preference_weight"] == 0.65


def test_crossover_excludes_primary_character() -> None:
    response = client.post(
        "/api/crossovers/evaluate",
        json={
            "session_id": "test-crossover",
            "primary_character": "biggie",
            "latitude": 40.6894,
            "longitude": -73.965,
            "remaining_minutes": 120,
            "remaining_budget_usd": 20,
        },
    )

    assert response.status_code == 200
    assert all(offer["point"]["character"] != "biggie" for offer in response.json()["offers"])


def test_crew_manifest_has_all_four_specialists() -> None:
    response = client.get("/api/crew/manifest")

    assert response.status_code == 200
    assert len(response.json()["agents"]) == 4


def test_one_login_requires_provider_configuration() -> None:
    response = client.get("/auth/one/login")

    assert response.status_code == 503
