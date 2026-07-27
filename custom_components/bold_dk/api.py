"""HTTP client for Bold.dk."""

from __future__ import annotations

import asyncio

from aiohttp import ClientError, ClientSession

from .models import Story, Target
from .parser import parse_stories


class BoldApiError(Exception):
    """Raised when Bold.dk cannot be read."""


class BoldApiClient:
    """Small asynchronous Bold.dk client."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def async_get_stories(self, target: Target) -> list[Story]:
        """Fetch the newest stories for a target."""
        try:
            async with asyncio.timeout(15):
                response = await self._session.get(
                    target.url,
                    headers={"Accept": "text/html", "User-Agent": "HomeAssistant-Bold.dk/0.1"},
                )
                response.raise_for_status()
                return parse_stories(await response.text(), target.url)
        except (TimeoutError, ClientError) as err:
            raise BoldApiError(f"Could not fetch {target.url}") from err
