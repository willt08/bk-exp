"""CrewAI AMP REST integration for the deployed BK-EXP crew."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urljoin

import httpx


class CrewAmpError(RuntimeError):
    """An actionable failure returned by the deployed CrewAI AMP service."""


@dataclass(frozen=True)
class CrewAmpClient:
    base_url: str
    bearer_token: str

    def _url(self, path: str) -> str:
        return urljoin(f"{self.base_url.rstrip('/')}/", path.lstrip("/"))

    @property
    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.bearer_token}"}

    async def inputs(self) -> dict[str, Any]:
        return await self._get("inputs")

    async def kickoff(self, inputs: dict[str, Any]) -> dict[str, Any]:
        return await self._post("kickoff", {"inputs": inputs})

    async def status(self, kickoff_id: str) -> dict[str, Any]:
        return await self._get(f"status/{kickoff_id}")

    async def _get(self, path: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.get(self._url(path), headers=self._headers)
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise CrewAmpError("CrewAI AMP request timed out after 30 seconds.") from error
        except httpx.HTTPStatusError as error:
            raise CrewAmpError(self._http_error_message(error.response, path)) from error
        except httpx.RequestError as error:
            raise CrewAmpError("Unable to reach the configured CrewAI AMP endpoint.") from error
        return self._json_object(response, path)

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
                response = await client.post(self._url(path), headers=self._headers, json=payload)
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise CrewAmpError("CrewAI AMP request timed out after 30 seconds.") from error
        except httpx.HTTPStatusError as error:
            raise CrewAmpError(self._http_error_message(error.response, path)) from error
        except httpx.RequestError as error:
            raise CrewAmpError("Unable to reach the configured CrewAI AMP endpoint.") from error
        return self._json_object(response, path)

    @staticmethod
    def _json_object(response: httpx.Response, endpoint: str) -> dict[str, Any]:
        try:
            payload = response.json()
        except ValueError as error:
            raise CrewAmpError(f"CrewAI AMP returned invalid JSON for {endpoint}.") from error
        if not isinstance(payload, dict):
            raise CrewAmpError(f"CrewAI AMP returned a non-object JSON response for {endpoint}.")
        return payload

    @staticmethod
    def _http_error_message(response: httpx.Response, endpoint: str) -> str:
        message = f"CrewAI AMP returned HTTP {response.status_code} for {endpoint}."
        if response.status_code != 422:
            return message
        try:
            payload = response.json()
        except ValueError:
            return message
        detail = payload.get("detail") if isinstance(payload, dict) else None
        if isinstance(detail, str) and detail.strip():
            return f"{message} Validation detail: {detail.strip()}"
        return message
