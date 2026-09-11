import asyncio

from fastapi.testclient import TestClient

from bk_exp.api.main import app
from bk_exp.agents.crew import CrewAmpClient
from bk_exp.models import TourCharacter
from bk_exp.services.research import normalize_citations, research_character

client = TestClient(app)


def test_map_page_includes_route_panel_and_map_client() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert 'id="route-stops"' in response.text
    assert "maplibre-gl" in response.text
    assert 'id="research-tour"' in response.text


def test_tour_returns_primary_route_and_all_points() -> None:
    response = client.get("/api/tours/biggie")

    assert response.status_code == 200
    body = response.json()
    assert body["character"] == "biggie"
    assert len(body["primary_route"]) >= 3
    assert len(body["all_points"]) >= 12
    assert all(point["source_url"].startswith("https://") for point in body["primary_route"])
    assert all(point["source_title"] for point in body["primary_route"])


def test_every_character_has_a_three_stop_route() -> None:
    for character in ("basquiat", "whitman", "biggie", "rbg"):
        response = client.get(f"/api/tours/{character}")

        assert response.status_code == 200
        assert len(response.json()["primary_route"]) == 3


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


def test_crew_inputs_requires_its_provider_configuration() -> None:
    response = client.get("/api/crew/inputs")

    assert response.status_code == 503


def test_one_login_requires_provider_configuration() -> None:
    response = client.get("/auth/one/login")

    assert response.status_code == 503


def test_crew_run_requires_its_provider_configuration() -> None:
    response = client.post(
        "/api/crew/run",
        json={"character": "basquiat", "remaining_minutes": 90, "remaining_budget_usd": 20},
    )

    assert response.status_code == 503


def test_amp_client_uses_deployed_crew_url_and_bearer_authentication() -> None:
    client = CrewAmpClient("https://bk-exp.crewai.com/", "test-token")

    assert client._url("/status/run-123") == "https://bk-exp.crewai.com/status/run-123"
    assert client._headers == {"Authorization": "Bearer test-token"}


def test_live_research_requires_you_configuration() -> None:
    response = client.get("/api/research/basquiat")

    assert response.status_code == 503


def test_normalize_citations_keeps_only_complete_unique_web_results() -> None:
    payload = {
        "results": {
            "web": [
                {"title": "Museum", "url": "https://example.org/museum", "snippet": "A cited place."},
                {"title": "Museum again", "url": "https://example.org/museum", "snippet": "Duplicate."},
                {"title": "Missing snippet", "url": "https://example.org/missing"},
                {"title": "Unsafe", "url": "javascript:alert(1)", "snippet": "Rejected."},
            ]
        }
    }

    citations = normalize_citations(payload)

    assert len(citations) == 1
    assert citations[0].url == "https://example.org/museum"


def test_research_character_normalizes_provider_response() -> None:
    class FakeYouClient:
        async def search(self, query: str) -> dict:
            assert "Basquiat" in query
            return {
                "results": {
                    "web": [
                        {
                            "title": "Evidence",
                            "url": "https://example.org/evidence",
                            "snippet": "Documented history.",
                        }
                    ]
                }
            }

    result = asyncio.run(research_character(FakeYouClient(), TourCharacter.BASQUIAT))

    assert result.character == TourCharacter.BASQUIAT
    assert result.citations[0].title == "Evidence"
