"""Config flow for Bold.dk."""

from __future__ import annotations

from dataclasses import asdict
from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BoldApiClient, BoldApiError
from .const import CONF_CLUBS, CONF_LEAGUE_NAME, CONF_LEAGUE_URL, DOMAIN
from .models import Club


def valid_bold_url(value: str) -> str:
    """Validate and normalize a secure Bold.dk URL."""
    value = value.strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in {"bold.dk", "www.bold.dk"}:
        raise vol.Invalid("Not a Bold.dk URL")
    return value


class BoldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Choose a league and then clubs within it."""

    VERSION = 2

    def __init__(self) -> None:
        self._league_name = ""
        self._league_url = ""
        self._clubs: list[Club] = []

    async def async_step_user(self, user_input=None):
        """Ask for the league page and discover its clubs."""
        errors = {}
        if user_input is not None:
            self._league_name = user_input[CONF_LEAGUE_NAME].strip()
            self._league_url = user_input[CONF_LEAGUE_URL]
            await self.async_set_unique_id(self._league_url)
            self._abort_if_unique_id_configured()
            try:
                client = BoldApiClient(async_get_clientsession(self.hass))
                self._clubs = await client.async_get_clubs(self._league_url)
            except BoldApiError:
                errors["base"] = "cannot_connect"
            else:
                return await self.async_step_clubs()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LEAGUE_NAME): str,
                    vol.Required(CONF_LEAGUE_URL): valid_bold_url,
                }
            ),
            errors=errors,
        )

    async def async_step_clubs(self, user_input=None):
        """Let the user select clubs discovered in the league."""
        if user_input is not None:
            selected_urls = set(user_input[CONF_CLUBS])
            selected = [asdict(club) for club in self._clubs if club.url in selected_urls]
            return self.async_create_entry(
                title=self._league_name,
                data={
                    CONF_LEAGUE_NAME: self._league_name,
                    CONF_LEAGUE_URL: self._league_url,
                    CONF_CLUBS: selected,
                },
            )

        options = {club.url: club.name for club in self._clubs}
        return self.async_show_form(
            step_id="clubs",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLUBS): cv.multi_select(options),
                }
            ),
        )
