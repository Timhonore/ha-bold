"""Data coordinator for Bold.dk."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BoldApiClient, BoldApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import Club, ClubData, LeagueData

_LOGGER = logging.getLogger(__name__)


class BoldCoordinator(DataUpdateCoordinator[LeagueData]):
    """Poll the selected league and clubs."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BoldApiClient,
        league_name: str,
        league_url: str,
        clubs: list[Club],
    ) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL)
        self.client = client
        self.league_name = league_name
        self.league_url = league_url
        self.clubs = clubs

    async def _async_update_data(self) -> LeagueData:
        try:
            standings, club_results = await asyncio.gather(
                self.client.async_get_standings(self.league_url),
                asyncio.gather(*(self.client.async_get_club_data(club) for club in self.clubs)),
            )
        except BoldApiError as err:
            raise UpdateFailed(str(err)) from err

        positions = {name.casefold(): position for position, name in standings}
        club_data: dict[str, ClubData] = {}
        for result in club_results:
            position = positions.get(result.club.name.casefold())
            club_data[result.club.url] = replace(result, position=position)
        return LeagueData(self.league_name, self.league_url, tuple(standings), club_data)
