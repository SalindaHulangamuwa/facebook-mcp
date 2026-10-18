"""Typed configuration loaded from environment variables and an optional `.env` file.

Two credential modes are supported:

* **Multi-page**: `FB_USER_ACCESS_TOKEN`. Every Page the user manages is
  discovered through `/me/accounts`, each with its own Page token.
* **Single page**: `FB_PAGE_ID` + `FB_PAGE_ACCESS_TOKEN`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from facebook_mcp.exceptions import ConfigurationError

TransportName = Literal["stdio", "http"]

_ENV_FILE_CONFIG = SettingsConfigDict(
    env_file=".env", env_file_encoding="utf-8", env_ignore_empty=True, extra="ignore"
)

_MISSING_CREDENTIALS = (
    "No Facebook credentials found. Set FB_USER_ACCESS_TOKEN to manage all your Pages, "
    "or FB_PAGE_ID and FB_PAGE_ACCESS_TOKEN to manage a single Page."
)
_CONFLICTING_CREDENTIALS = (
    "Set either FB_USER_ACCESS_TOKEN or FB_PAGE_ID + FB_PAGE_ACCESS_TOKEN, not both."
)


class FacebookSettings(BaseSettings):
    """Credentials and Graph API options."""

    model_config = _ENV_FILE_CONFIG

    user_access_token: SecretStr | None = Field(
        default=None, validation_alias="FB_USER_ACCESS_TOKEN"
    )
    page_id: str | None = Field(default=None, validation_alias="FB_PAGE_ID")
    page_access_token: SecretStr | None = Field(
        default=None, validation_alias="FB_PAGE_ACCESS_TOKEN"
    )
    default_page: str | None = Field(default=None, validation_alias="FB_DEFAULT_PAGE")
    app_secret: SecretStr | None = Field(
        default=None, validation_alias=AliasChoices("FB_APP_SECRET", "APP_SECRET")
    )
    graph_api_version: str = Field(default="v26.0", validation_alias="FB_GRAPH_API_VERSION")
    graph_base_url: str = Field(
        default="https://graph.facebook.com", validation_alias="FB_GRAPH_BASE_URL"
    )
    request_timeout_seconds: float = Field(default=30.0, gt=0, validation_alias="FB_TIMEOUT")

    @model_validator(mode="after")
    def _exactly_one_credential_mode(self) -> FacebookSettings:
        has_single_page_fields = self.page_id is not None or self.page_access_token is not None
        if self.user_access_token and has_single_page_fields:
            raise ValueError(_CONFLICTING_CREDENTIALS)
        if not (self.user_access_token or (self.page_id and self.page_access_token)):
            raise ValueError(_MISSING_CREDENTIALS)
        return self

    def single_page_credentials(self) -> tuple[str, str]:
        if not (self.page_id and self.page_access_token):
            raise ConfigurationError(_MISSING_CREDENTIALS)
        return self.page_id, self.page_access_token.get_secret_value()


class ServerSettings(BaseSettings):
    """How the MCP server is exposed to clients."""

    model_config = SettingsConfigDict(**_ENV_FILE_CONFIG, env_prefix="MCP_")

    transport: TransportName = "stdio"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    path: str = "/mcp"
    auth_token: SecretStr | None = None
    read_only: bool = False
    log_level: str = "INFO"
