"""Root of the project's exception hierarchy.

Every error we understand derives from `FacebookMCPError` and carries a
`user_message` that is safe and useful to show an AI client. Anything else is
treated as an unexpected bug and masked by the server.
"""

from __future__ import annotations


class FacebookMCPError(Exception):
    """An anticipated failure with an actionable, client-safe message."""

    @property
    def user_message(self) -> str:
        return str(self)


class ConfigurationError(FacebookMCPError):
    """The server was started with missing or contradictory settings."""
