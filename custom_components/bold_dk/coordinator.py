"""Data coordinator for Bold.dk."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import replace
from urllib.parse import urlparse

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BoldApiClient, BoldApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import Club, ClubData, LeagueData, Story, Target

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
        entry: ConfigEntry | None = None,
    ) -> None:
        super().__init__(
            hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=DEFAULT_SCAN_INTERVAL
        )
        self.client = client
        self.league_name = league_name
        self.league_url = league_url
        self.clubs = clubs

    async def _async_update_data(self) -> LeagueData:
        try:
            league_data, club_results = await asyncio.gather(
                self.client.async_get_league_data(self.league_url),
                asyncio.gather(*(self.client.async_get_club_data(club) for club in self.clubs)),
            )
        except BoldApiError as err:
            raise UpdateFailed(str(err)) from err

        standings, scorers = league_data
        positions = {name.casefold(): position for position, name in standings}
        club_data: dict[str, ClubData] = {}
        for result in club_results:
            position = positions.get(result.club.name.casefold())
            scorer, goals = scorers.get(
                urlparse(result.club.url).path.rstrip("/").rsplit("/", 1)[-1],
                (result.top_scorer, result.top_scorer_goals),
            )
            club_data[result.club.url] = replace(
                result, position=position, top_scorer=scorer, top_scorer_goals=goals
            )
        return LeagueData(self.league_name, self.league_url, tuple(standings), club_data)


class BoldStoryCoordinator(DataUpdateCoordinator[dict[str, list[Story]]]):
    """Poll all configured targets."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: BoldApiClient,
        targets: list[Target],
        entry: ConfigEntry | None = None,
    ) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.targets = targets

    async def _async_update_data(self) -> dict[str, list[Story]]:
        results = await asyncio.gather(
            *(self.client.async_get_stories(target) for target in self.targets),
            return_exceptions=True,
        )
        data: dict[str, list[Story]] = {}
        errors: list[str] = []
        for target, result in zip(self.targets, results, strict=True):
            if isinstance(result, BoldApiError):
                errors.append(target.name)
            elif isinstance(result, BaseException):
                raise result
            else:
                data[target.url] = result
        if errors and not data:
            raise UpdateFailed(f"Could not update: {', '.join(errors)}")
        return data
