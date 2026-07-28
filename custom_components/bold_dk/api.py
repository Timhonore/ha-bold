"""HTTP client for Bold.dk."""

from __future__ import annotations

import asyncio

from aiohttp import ClientError, ClientSession

from .models import Club, ClubData
from .parser import parse_club_data, parse_clubs, parse_standings


class BoldApiError(Exception):
    """Raised when Bold.dk cannot be read or parsed."""


class BoldApiClient:
    """Asynchronous client for the public Bold.dk pages."""
from .models import Story, Target
from .parser import parse_stories


class BoldApiError(Exception):
    """Raised when Bold.dk cannot be read."""


class BoldApiClient:
    """Small asynchronous Bold.dk client."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get(self, url: str) -> str:
        try:
            async with asyncio.timeout(15):
                response = await self._session.get(
                    url,
                    headers={"Accept": "text/html", "User-Agent": "HomeAssistant-Bold.dk/0.2"},
                )
                response.raise_for_status()
                return await response.text()
        except (TimeoutError, ClientError) as err:
            raise BoldApiError(f"Could not fetch {url}") from err

    async def async_get_clubs(self, league_url: str) -> list[Club]:
        """Discover clubs on a league page."""
        clubs = parse_clubs(await self._get(league_url), league_url)
        if not clubs:
            raise BoldApiError("No clubs found on league page")
        return clubs

    async def async_get_standings(self, league_url: str) -> list[tuple[int, str]]:
        """Get league positions."""
        return parse_standings(await self._get(league_url), league_url)

    async def async_get_club_data(self, club: Club) -> ClubData:
        """Get match and scorer data for a club."""
        return parse_club_data(await self._get(club.url), club.url, club)
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
