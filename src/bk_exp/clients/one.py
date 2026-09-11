from dataclasses import dataclass

import httpx


class OneAuthError(RuntimeError):
    """An actionable failure while interacting with the configured One OAuth service."""


@dataclass(frozen=True)
class OneOAuthClient:
    client_id: str
    client_secret: str
    authorization_url: str
    token_url: str
    redirect_uri: str

    def authorization_parameters(self, state: str) -> dict[str, str]:
        return {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "state": state,
        }

    async def exchange_code(self, code: str) -> dict:
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                response = await client.post(self.token_url, data=payload)
                response.raise_for_status()
        except httpx.TimeoutException as error:
            raise OneAuthError("One token exchange timed out after 15 seconds.") from error
        except httpx.HTTPStatusError as error:
            raise OneAuthError(
                f"One token exchange returned HTTP {error.response.status_code}."
            ) from error
        except httpx.RequestError as error:
            raise OneAuthError("Unable to reach the configured One token endpoint.") from error
        return response.json()
