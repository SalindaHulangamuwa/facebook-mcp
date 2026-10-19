"""Thin async HTTP client for the Facebook Graph API.

`GraphClient` owns transport concerns only: base URL, versioning, timeouts,
connection pooling, `appsecret_proof` signing and error translation. It is not
bound to a token, so one pooled connection serves every Page; `bind(token)`
returns a lightweight `BoundGraph` that services use without ever touching
credentials.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

import httpx

from facebook_mcp.config import FacebookSettings
from facebook_mcp.graph.errors import GraphConnectionError, error_from_response

JSON = dict[str, Any]
Params = dict[str, Any]


def compute_appsecret_proof(access_token: str, app_secret: str) -> str:
    """HMAC-SHA256 of the token keyed by the app secret, as Meta requires."""
    return hmac.new(app_secret.encode(), access_token.encode(), hashlib.sha256).hexdigest()


class GraphClient:
    def __init__(
        self,
        *,
        api_version: str,
        base_url: str = "https://graph.facebook.com",
        app_secret: str | None = None,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._app_secret = app_secret
        self._http_options: dict[str, Any] = {
            "base_url": f"{base_url.rstrip('/')}/{api_version}/",
            "timeout": timeout,
            "transport": transport,
        }
        self._http: httpx.AsyncClient | None = None

    @classmethod
    def from_settings(
        cls, settings: FacebookSettings, *, transport: httpx.AsyncBaseTransport | None = None
    ) -> GraphClient:
        return cls(
            api_version=settings.graph_api_version,
            base_url=settings.graph_base_url,
            app_secret=settings.app_secret.get_secret_value() if settings.app_secret else None,
            timeout=settings.request_timeout_seconds,
            transport=transport,
        )

    def bind(self, access_token: str) -> BoundGraph:
        return BoundGraph(self, access_token)

    async def request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: Params | None = None,
        data: Params | None = None,
    ) -> JSON:
        try:
            response = await self._connection().request(
                method,
                path.lstrip("/"),
                params={**_drop_none(params), **self._proof_params(token)},
                data=_drop_none(data),
                headers=_auth_headers(token),
            )
        except httpx.HTTPError as exc:
            raise GraphConnectionError(str(exc) or type(exc).__name__) from exc
        if response.is_error:
            raise error_from_response(response)
        payload: JSON = response.json()
        return payload

    async def upload(self, url: str, *, token: str, content: bytes, headers: dict[str, str]) -> JSON:
        """POST raw bytes to an absolute upload URL (e.g. rupload.facebook.com for Reels)."""
        try:
            response = await self._connection().post(
                url, content=content, headers={"Authorization": f"OAuth {token}", **headers}
            )
        except httpx.HTTPError as exc:
            raise GraphConnectionError(str(exc) or type(exc).__name__) from exc
        if response.is_error:
            raise error_from_response(response)
        payload: JSON = response.json()
        return payload

    async def aclose(self) -> None:
        """Release pooled connections. The client reopens lazily if used again."""
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def __aenter__(self) -> GraphClient:
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    def _connection(self) -> httpx.AsyncClient:
        if self._http is None or self._http.is_closed:
            self._http = httpx.AsyncClient(**self._http_options)
        return self._http

    def _proof_params(self, token: str | None) -> Params:
        if not (token and self._app_secret):
            return {}
        return {"appsecret_proof": compute_appsecret_proof(token, self._app_secret)}


class BoundGraph:
    """A `GraphClient` view that authenticates every call with one access token."""

    def __init__(self, client: GraphClient, access_token: str) -> None:
        self._client = client
        self._token = access_token

    async def get(self, path: str, params: Params | None = None) -> JSON:
        return await self._client.request("GET", path, token=self._token, params=params)

    async def post(self, path: str, data: Params | None = None) -> JSON:
        return await self._client.request("POST", path, token=self._token, data=data)

    async def delete(self, path: str) -> JSON:
        return await self._client.request("DELETE", path, token=self._token)

    async def upload(self, url: str, content: bytes, headers: dict[str, str]) -> JSON:
        return await self._client.upload(url, token=self._token, content=content, headers=headers)

    def __repr__(self) -> str:  # never leak the token into logs or tracebacks
        return "BoundGraph(token=***)"


def _auth_headers(token: str | None) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def _drop_none(values: Params | None) -> Params:
    """Graph rejects literal 'None' strings, so omit unset optional parameters."""
    return {key: value for key, value in (values or {}).items() if value is not None}
