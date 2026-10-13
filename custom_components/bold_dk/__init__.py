"""The Bold.dk integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BoldApiClient
from .const import CONF_CLUBS, CONF_LEAGUE_NAME, CONF_LEAGUE_URL, CONF_TARGETS
from .coordinator import BoldCoordinator, BoldStoryCoordinator
from .models import Club, Target

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up league entries and retain existing news entries."""
    client = BoldApiClient(async_get_clientsession(hass))
    if CONF_TARGETS in entry.data:
        coordinator = BoldStoryCoordinator(
            hass, client, [Target(**item) for item in entry.data[CONF_TARGETS]], entry
        )
    else:
        coordinator = BoldCoordinator(
            hass,
            client,
            entry.data[CONF_LEAGUE_NAME],
            entry.data[CONF_LEAGUE_URL],
            [Club(**item) for item in entry.data[CONF_CLUBS]],
            entry,
        )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Keep version 1 news entries usable with the version 2 league flow."""
    if entry.version > 2:
        return False
    if entry.version == 1:
        hass.config_entries.async_update_entry(entry, version=2)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Bold.dk config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
