"""Config flow for Bold.dk."""

from __future__ import annotations

from urllib.parse import urlparse

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import CONF_TARGETS, DOMAIN


def parse_targets(value: str) -> list[dict[str, str]]:
    """Parse one `name | URL` target per line."""
    targets: list[dict[str, str]] = []
    for line in value.splitlines():
        if not line.strip():
            continue
        parts = [part.strip() for part in line.split("|", 1)]
        if len(parts) != 2 or not parts[0] or not _valid_url(parts[1]):
            raise ValueError
        targets.append({"name": parts[0], "url": parts[1]})
    if not targets:
        raise ValueError
    return targets


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and parsed.hostname in {"bold.dk", "www.bold.dk"}


class BoldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configure the list of followed clubs and leagues."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial configuration step."""
        errors = {}
        if user_input is not None:
            try:
                targets = parse_targets(user_input[CONF_TARGETS])
            except ValueError:
                errors[CONF_TARGETS] = "invalid_targets"
            else:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={CONF_TARGETS: targets},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Bold.dk"): str,
                vol.Required(CONF_TARGETS): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
