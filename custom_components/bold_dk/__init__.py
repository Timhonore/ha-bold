"""The Bold.dk integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BoldApiClient
from .const import CONF_CLUBS, CONF_LEAGUE_NAME, CONF_LEAGUE_URL
from .coordinator import BoldCoordinator
from .models import Club

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bold.dk from a config entry."""
    coordinator = BoldCoordinator(
        hass,
        BoldApiClient(async_get_clientsession(hass)),
        entry.data[CONF_LEAGUE_NAME],
        entry.data[CONF_LEAGUE_URL],
        [Club(**item) for item in entry.data[CONF_CLUBS]],
    )
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Bold.dk config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
