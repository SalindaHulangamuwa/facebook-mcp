"""Bearer-token protection for the HTTP transport."""

from __future__ import annotations

import hmac

from fastmcp.server.auth import AccessToken, TokenVerifier

CLIENT_ID = "facebook-mcp-client"


class StaticBearerTokenVerifier(TokenVerifier):
    """Accepts exactly one pre-shared token, compared in constant time."""

    def __init__(self, expected_token: str) -> None:
        super().__init__()
        self._expected = expected_token.encode()

    async def verify_token(self, token: str) -> AccessToken | None:
        if not hmac.compare_digest(token.encode(), self._expected):
            return None
        return AccessToken(token=token, client_id=CLIENT_ID, scopes=[])
