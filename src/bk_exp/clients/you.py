from dataclasses import dataclass
from typing import Any

import httpx


class YouSearchError(RuntimeError):
    """A typed, actionable failure from the You.com Search boundary."""


@dataclass(frozen=True)
class YouSearchClient:
    api_key: str
    base_url: str

    async def search(self, query: str) -> dict[str, Any]:
        headers = {"X-API-Key": self.api_key}
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                response = await client.get(self.base_url, params={"query": query}, headers=headers)
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise YouSearchError("You.com Search timed out after 15 seconds.") from error
        except httpx.HTTPStatusError as error:
            raise YouSearchError(
                f"You.com Search returned HTTP {error.response.status_code}; verify credentials and quota."
            ) from error
        except httpx.RequestError as error:
            raise YouSearchError("Unable to reach You.com Search.") from error
        return response.json()
