from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import urlencode

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from bk_exp.agents.crew import CrewAmpClient, CrewAmpError
from bk_exp.clients.one import OneAuthError, OneOAuthClient
from bk_exp.clients.you import YouSearchClient, YouSearchError
from bk_exp.models import (
    CrewRunRequest,
    CrewRunResponse,
    CrewInputsResponse,
    CrewStatusResponse,
    CrossoverRequest,
    CrossoverResponse,
    FeedbackRequest,
    FeedbackResponse,
    ResearchResponse,
    TourCharacter,
    TourResponse,
)
from bk_exp.settings import Settings
from bk_exp.services.research import research_character
from bk_exp.services.tours import POINTS_OF_INTEREST, PreferenceStore, crossover_offers

static_directory = Path(__file__).parents[1] / "static"
preferences = PreferenceStore()
settings = Settings()
app = FastAPI(title="BK-EXP Tour API", version="0.1.0")
app.add_middleware(SessionMiddleware, secret_key=settings.session_secret or "local-development-only")
app.mount("/static", StaticFiles(directory=static_directory), name="static")


@app.get("/", include_in_schema=False)
def map_page() -> FileResponse:
    return FileResponse(static_directory / "index.html")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/tours/{character}", response_model=TourResponse)
def tour(character: TourCharacter) -> TourResponse:
    primary_route = [point for point in POINTS_OF_INTEREST if point.character == character]
    if not primary_route:
        raise HTTPException(status_code=404, detail="No curated route is available for this character.")
    return TourResponse(character=character, primary_route=primary_route, all_points=POINTS_OF_INTEREST)


@app.get("/api/research/{character}", response_model=ResearchResponse)
async def research(character: TourCharacter) -> ResearchResponse:
    if not settings.you_api_key or not settings.you_search_url:
        raise HTTPException(
            status_code=503,
            detail="Live research needs YOU_API_KEY and YOU_SEARCH_URL.",
        )
    client = YouSearchClient(api_key=settings.you_api_key, base_url=settings.you_search_url)
    try:
        return await research_character(client, character)
    except YouSearchError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/crossovers/evaluate", response_model=CrossoverResponse)
def evaluate_crossovers(request: CrossoverRequest) -> CrossoverResponse:
    return CrossoverResponse(offers=crossover_offers(request, preferences))


@app.post("/api/feedback", response_model=FeedbackResponse)
def record_feedback(request: FeedbackRequest) -> FeedbackResponse:
    return preferences.record(request)


def configured_crew_client() -> CrewAmpClient:
    if not settings.crew_is_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "CrewAI AMP needs YOU_API_KEY, YOU_SEARCH_URL, CREW_AMP_URL, and "
                "CREW_AMP_BEARER_TOKEN."
            ),
        )
    return CrewAmpClient(settings.crew_amp_url, settings.crew_amp_bearer_token)


@app.get("/api/crew/inputs", response_model=CrewInputsResponse)
async def crew_inputs() -> CrewInputsResponse:
    try:
        return CrewInputsResponse(inputs=(await configured_crew_client().inputs()))
    except CrewAmpError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/crew/run", response_model=CrewRunResponse)
async def run_crew(request: CrewRunRequest) -> CrewRunResponse:
    crew_client = configured_crew_client()
    research_client = YouSearchClient(api_key=settings.you_api_key, base_url=settings.you_search_url)
    try:
        research = await research_character(research_client, request.character)
    except YouSearchError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    if not research.citations:
        raise HTTPException(
            status_code=422,
            detail="You.com returned no complete, unique citations for curator review.",
        )
    try:
        response = await crew_client.kickoff(
            {
                **request.model_dump(),
                "research_citations": [citation.model_dump() for citation in research.citations],
            }
        )
    except CrewAmpError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    kickoff_id = response.get("kickoff_id")
    if not isinstance(kickoff_id, str) or not kickoff_id:
        raise HTTPException(status_code=502, detail="CrewAI AMP kickoff response did not include kickoff_id.")
    return CrewRunResponse(kickoff_id=kickoff_id, research=research)


@app.get("/api/crew/runs/{kickoff_id}", response_model=CrewStatusResponse)
async def crew_status(kickoff_id: str) -> CrewStatusResponse:
    try:
        response = await configured_crew_client().status(kickoff_id)
    except CrewAmpError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    status = response.get("status")
    if not isinstance(status, str) or not status:
        raise HTTPException(status_code=502, detail="CrewAI AMP status response did not include status.")
    return CrewStatusResponse(kickoff_id=kickoff_id, status=status, result=response.get("result"))


def configured_one_client() -> OneOAuthClient:
    if not settings.one_is_configured():
        raise HTTPException(
            status_code=503,
            detail="One OAuth is not configured. Set the ONE_* variables and SESSION_SECRET.",
        )
    return OneOAuthClient(
        client_id=settings.one_client_id,
        client_secret=settings.one_client_secret,
        authorization_url=settings.one_authorization_url,
        token_url=settings.one_token_url,
        redirect_uri=settings.one_redirect_uri,
    )


@app.get("/auth/one/login")
def one_login(request: Request) -> RedirectResponse:
    client = configured_one_client()
    state = token_urlsafe(32)
    request.session["one_oauth_state"] = state
    return RedirectResponse(f"{client.authorization_url}?{urlencode(client.authorization_parameters(state))}")


@app.get("/auth/one/callback")
async def one_callback(request: Request, code: str, state: str) -> RedirectResponse:
    client = configured_one_client()
    expected_state = request.session.pop("one_oauth_state", None)
    if expected_state != state:
        raise HTTPException(status_code=400, detail="Invalid One OAuth state.")
    try:
        token = await client.exchange_code(code)
    except OneAuthError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    request.session["one_authenticated"] = True
    request.session["one_access_token"] = token.get("access_token")
    return RedirectResponse("/")
