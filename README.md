# BK-EXP: Adaptive Brooklyn Cultural Tours

BK-EXP is an adaptive walking-tour agent for Brooklyn stories connected to
Jean-Michel Basquiat, Walt Whitman, The Notorious B.I.G., and Ruth Bader
Ginsburg. A visitor selects a primary character, available time, mobility
preferences, and budget. The system retrieves current, source-attributed points
of interest, creates a cohesive route, and continuously evaluates nearby
crossover opportunities. Rather than replacing a visitor's chosen experience,
it explains the cultural connection, added travel time and cost, and whether
the detour fits the remaining budget. The visitor can accept, defer, or reject
each recommendation.

The project uses a CrewAI crew of four specialized agents: a research agent
retrieves public-web evidence through You.com Search; a cultural curator
normalizes sources against clean civic and institutional data; a route designer
constructs the initial itinerary; and an adaptation agent ranks live crossover
options using feedback and trip constraints. Crew execution takes place in a
Daytona sandbox so tool use and route experiments are isolated and
reproducible. One provides the consent-based authentication boundary: visitors
sign in through One and explicitly authorize preference and feedback storage.

Feedback closes the learning loop. After every suggestion, BK-EXP records a
small, transparent event such as “accepted,” “skipped for time,” or “not
interested.” The adaptation agent updates per-visitor preference weights and
uses them on the next decision, so future crossovers better match demonstrated
interests without altering a tour that is already in progress. The ontology in
this repository preserves character, place, evidence, narrative connection, and
route-state relationships as structured data.

> **Status:** Working local prototype. The FastAPI service includes an
> interactive MapLibre map, browser geolocation, original SVG character
> markers, feedback-based crossover ranking, four instantiated CrewAI agents,
> and a configured One OAuth boundary. Live provider execution requires team
> credentials; database persistence and production routing remain next steps.

## Hackathon requirement map

| Requirement | Planned implementation |
|---|---|
| Self-improving agent | Explicit feedback events update a visitor preference profile that changes crossover ranking. |
| CrewAI | Four-agent crew: `researcher`, `curator`, `route_designer`, and `adaptation_evaluator`. |
| You.com API | The `researcher` calls a You.com Search endpoint for current POI discovery and stores source URLs, retrieval time, and snippets. |
| Daytona | Each crew run is created and executed in an isolated Daytona sandbox; run metadata is retained for observability. |
| One | One authentication establishes visitor identity and consent before saving preferences or feedback. |
| Clean Data | POIs are normalized, deduplicated, geocoded, provenance-tagged, and only promoted after source-quality checks. |
| Demo | A 1–3 minute script is provided below. |
| Public GitHub repository | Publish this folder as `bk-exp` once implementation and secrets configuration are complete. |

## Product behavior

1. The visitor signs in through One and chooses a primary character, tour time
   budget, spending budget, and accessibility preferences.
2. The research and curator agents retrieve and validate Brooklyn POIs.
3. The route designer creates an evidence-backed primary itinerary.
4. At each navigation update, the adaptation evaluator checks nearby POIs
   associated with another supported character.
5. A crossover is offered only if it fits remaining time, cost, and accessibility
   constraints. The original route remains preserved and can be resumed.
6. The visitor’s response is saved as feedback, updating future recommendation
   weights for that authenticated visitor.

## Architecture

```text
One sign-in + consent
        |
        v
Tour API -----> preference / feedback store
   |                    |
   |                    v
   |              learned profile
   v
Daytona sandbox --> CrewAI crew (4 agents)
   |                   |       |        |
   |                   |       |        +--> adaptation evaluator
   |                   |       +-----------> route designer
   |                   +-------------------> cultural curator
   +--> You.com Search --------------------> researcher
        |
        v
clean POI store <--> ontology / route state <--> web navigation client
```

### Agent contracts

| Agent | Input | Output | Learning responsibility |
|---|---|---|---|
| Researcher | Character, Brooklyn boundary, query template | Candidate POIs with search citations | Never promotes an uncited result. |
| Cultural curator | Candidate POIs and source records | Normalized, deduplicated POIs with confidence | Marks weak evidence for review. |
| Route designer | Validated POIs and trip constraints | Ordered primary route plus travel/time estimates | Preserves narrative continuity. |
| Adaptation evaluator | Current location, route state, feedback profile | Ranked crossover offers or no-change decision | Updates/rereads preference weights after feedback. |

### Crossover policy

An offer must have verified provenance, be reachable within the visitor’s
remaining time and accessibility constraints, and score higher than a configured
minimum relevance threshold. Every offer includes: cultural connection, added
minutes, added cost, impact on the primary narrative, and **Accept**, **Not
now**, and **Keep original route** actions. Rejection never deletes the primary
route; acceptance creates a route branch and retains the original as a resumable
path.

## Clean-data policy

The production ingestion pipeline will retain only records that:

- identify a public, reputable primary or institutional source;
- include a canonical place name, Brooklyn coordinates or a geocodable address,
  and retrieval timestamp;
- distinguish documented association from editorial interpretation;
- are deduplicated by normalized name, coordinates, and source URL;
- retain source URLs and evidence snippets for visitor-facing attribution; and
- are reviewed before publishing any contested or low-confidence connection.

The You.com response is discovery evidence, not the sole authority for a
historical claim. The curator verifies claims against the linked source and
approved civic, archive, museum, library, or official venue data.

## Repository layout

```text
bk-exp/
├── .github/workflows/ci.yml       # Bootstrap validation and future test gate
├── docs/                          # Architecture decisions, demo assets, runbooks
├── ontology/tour-navigation.owl   # Route, POI, provenance, and feedback vocabulary
├── src/
│   ├── api/                       # FastAPI endpoints and One session boundary
│   ├── agents/                    # CrewAI agent/task definitions
│   ├── clients/                   # You.com, One, Daytona, routing adapters
│   ├── domain/                    # Typed tour, POI, feedback, and route models
│   ├── services/                  # Cleaning, routing, ranking, learning services
│   └── storage/                   # Repository interfaces and migrations
├── tests/                         # Unit, contract, and integration tests
├── .dockerignore
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

The service and tests now live in `src/` and `tests/`. The demo preference store
is process-local so it is safe to run without credentials; replace it with the
database repository before deployment.

## Local setup

### Prerequisites

- Python 3.11–3.13
- [uv](https://docs.astral.sh/uv/) or pip
- A You.com API key
- A Daytona API key and configured Daytona account
- A CrewAI-compatible LLM provider key
- One developer credentials and the approved redirect URI from the One console

1. Copy `.env.example` to `.env` and fill the values locally. Do not commit
   `.env`.
2. Install the planned Python dependencies:

   ```powershell
   uv sync
   ```

3. When the API service is implemented, run the application with:

   ```powershell
   uv run uvicorn src.api.main:app --reload
   ```

4. Open `http://localhost:8000`, select a character, and grant browser location
   access. The original SVG marker follows GPS updates; nearby character
   crossovers are re-ranked after each response.

### Container run

```powershell
docker build -t bk-exp .
docker run --rm -p 8000:8000 --env-file .env bk-exp
```

### Required environment variables

| Variable | Purpose |
|---|---|
| `YOU_API_KEY` | Authenticates server-side You.com API requests. |
| `YOU_SEARCH_URL` | The approved You.com Search endpoint URL for the team’s API plan. |
| `DAYTONA_API_KEY` | Creates isolated CrewAI execution sandboxes. |
| `OPENAI_API_KEY` | Supplies the CrewAI model provider credential. |
| `ONE_CLIENT_ID` | Identifies BK-EXP to One. |
| `ONE_CLIENT_SECRET` | Server-only One OAuth client secret. |
| `ONE_REDIRECT_URI` | Registered One OAuth callback URL. |
| `DATABASE_URL` | Feedback, preferences, and POI persistence. |

One endpoint names and scopes must be copied from the team’s approved One
developer configuration; this project does not guess or hard-code them.

### Crew execution

`GET /api/crew/inputs` discovers the required inputs from the deployed CrewAI
AMP crew. `POST /api/crew/run` starts a remote execution with `character`,
`remaining_minutes`, `remaining_budget_usd`, and live research citations; it
returns a `kickoff_id`. The browser polls `GET /api/crew/runs/{kickoff_id}`
until the deployed crew returns a terminal status. This requires `YOU_API_KEY`,
`YOU_SEARCH_URL`, `CREW_AMP_URL`, and `CREW_AMP_BEARER_TOKEN`.
Before invoking the LLM crew, the endpoint performs a required server-side
You.com retrieval and refuses the run if that retrieval does not yield complete,
unique citations. The resulting evidence is included in the crew inputs; the
research task additionally requires the research agent to use its You.com tool
to broaden or verify that evidence.

The web application exposes both operations: **Refresh live research** calls
`GET /api/research/{character}` and renders cited discovery findings in a
curator-review panel, while **Run 4-agent route review** calls
`POST /api/crew/run`. Search results never replace the vetted route
automatically; a curator must review the evidence and geospatial data before a
candidate is promoted into navigable route data.

## CI/CD

The GitHub Actions workflow validates the OWL/XML schema, project configuration,
and focused FastAPI behavior. The next increment will add formatting, type
checks, provider contract tests, image build, and an environment-protected
Daytona deployment job.

**Promotion path:** pull request checks → `main` → build immutable container →
staging deployment → authenticated smoke test → production approval. Provider
secrets belong in GitHub Environments or the deployment secret store, never in
workflow YAML or container layers.

## Demo outline (1–3 minutes)

1. Sign in through One and select a Basquiat tour with 90 minutes remaining.
2. Show You.com-powered, cited POIs and the curator’s provenance panel.
3. Start the primary route and arrive near a Notorious B.I.G. connection.
4. Show the crossover card: relevance, added walking time, cost, and original
   route impact.
5. Choose **Not now** because of time; show the feedback event and preserved
   Basquiat route.
6. Trigger a second nearby opportunity and show how the learned time sensitivity
   suppresses an unsuitable detour or changes its ranking.
7. Briefly show the Daytona run record and CrewAI agent trace.

## Delivery checklist

- [x] Add a standard OAuth authorization-code boundary for One, using only
  provider-configured endpoints and credentials.
- [ ] Add a server-side You.com client with response schemas, retries, and rate limits.
- [x] Define and instantiate the four CrewAI agents and their sequential tasks.
- [ ] Run crews in Daytona and persist sandbox/run metadata.
- [ ] Implement clean POI ingestion, human review, and source attribution.
- [x] Implement feedback-based crossover ranking with original-route preservation.
- [x] Add API tests and a container build definition.
- [ ] Record and publish the 1–3 minute YouTube demo.
- [ ] Publish the repository and replace this checklist with deployment links.

## References

- [CrewAI documentation](https://docs.crewai.com/)
- [Daytona documentation](https://www.daytona.io/docs/)
- [You.com Platform](https://you.com/platform)
- [One Hackathon portal](https://hackathon.withone.ai/)
