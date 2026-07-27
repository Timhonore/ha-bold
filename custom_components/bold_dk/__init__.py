"""The Bold.dk integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BoldApiClient
from .const import CONF_TARGETS
from .coordinator import BoldCoordinator
from .models import Target

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bold.dk from a config entry."""
    targets = [Target(**item) for item in entry.data[CONF_TARGETS]]
    coordinator = BoldCoordinator(hass, BoldApiClient(async_get_clientsession(hass)), targets)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Bold.dk config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
