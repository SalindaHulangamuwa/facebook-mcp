"""Token helpers for first-time setup (used by `facebook-mcp exchange-token`)."""

from __future__ import annotations

from facebook_mcp.graph import GraphClient


async def exchange_for_long_lived_token(
    graph: GraphClient, *, app_id: str, app_secret: str, short_lived_token: str
) -> str:
    """Swap a short-lived user token (about 1 hour) for a long-lived one (about 60 days).

    Page tokens later derived from a long-lived user token do not expire.
    """
    payload = await graph.request(
        "GET",
        "oauth/access_token",
        params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_lived_token,
        },
    )
    return str(payload["access_token"])
