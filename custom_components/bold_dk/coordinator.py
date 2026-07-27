"""Data coordinator for Bold.dk."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BoldApiClient, BoldApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import Story, Target

_LOGGER = logging.getLogger(__name__)


class BoldCoordinator(DataUpdateCoordinator[dict[str, list[Story]]]):
    """Poll all configured targets."""

    def __init__(self, hass: HomeAssistant, client: BoldApiClient, targets: list[Target]) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
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
