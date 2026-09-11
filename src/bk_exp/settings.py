from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    one_client_id: str | None = None
    one_client_secret: str | None = None
    one_authorization_url: str | None = None
    one_token_url: str | None = None
    one_redirect_uri: str = "http://localhost:8000/auth/one/callback"
    session_secret: str | None = None

    def one_is_configured(self) -> bool:
        return all(
            (
                self.one_client_id,
                self.one_client_secret,
                self.one_authorization_url,
                self.one_token_url,
                self.session_secret,
            )
        )
