from typing import Any

from bk_exp.clients.you import YouSearchClient
from bk_exp.models import ResearchCitation, ResearchResponse, TourCharacter

CHARACTER_QUERIES = {
    TourCharacter.BASQUIAT: "Jean-Michel Basquiat Brooklyn points of interest history",
    TourCharacter.WHITMAN: "Walt Whitman Brooklyn points of interest history",
    TourCharacter.BIGGIE: "The Notorious B.I.G. Brooklyn points of interest history",
    TourCharacter.RBG: "Ruth Bader Ginsburg Brooklyn points of interest history",
}


def _web_results(payload: dict[str, Any]) -> list[dict[str, Any]]:
    results = payload.get("results")
    if isinstance(results, dict):
        web_results = results.get("web")
        if isinstance(web_results, list):
            return [item for item in web_results if isinstance(item, dict)]
    if isinstance(results, list):
        return [item for item in results if isinstance(item, dict)]
    hits = payload.get("hits")
    if isinstance(hits, list):
        return [item for item in hits if isinstance(item, dict)]
    return []


def _text(item: dict[str, Any], *keys: str) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def normalize_citations(payload: dict[str, Any], limit: int = 5) -> list[ResearchCitation]:
    citations: list[ResearchCitation] = []
    seen_urls: set[str] = set()
    for item in _web_results(payload):
        title = _text(item, "title", "name")
        url = _text(item, "url", "link")
        snippet = _text(item, "snippet", "description", "text")
        if not title or not url or not snippet or url in seen_urls:
            continue
        if not url.startswith(("https://", "http://")):
            continue
        citations.append(ResearchCitation(title=title, url=url, snippet=snippet))
        seen_urls.add(url)
        if len(citations) == limit:
            break
    return citations


async def research_character(client: YouSearchClient, character: TourCharacter) -> ResearchResponse:
    query = CHARACTER_QUERIES[character]
    payload = await client.search(query)
    return ResearchResponse(
        character=character,
        query=query,
        citations=normalize_citations(payload),
    )
