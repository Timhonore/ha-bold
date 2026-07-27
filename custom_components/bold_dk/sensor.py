"""Sensors for the Bold.dk integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BoldCoordinator
from .models import Target


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one sensor per followed target."""
    coordinator: BoldCoordinator = entry.runtime_data
    async_add_entities(BoldSensor(coordinator, entry, target) for target in coordinator.targets)


class BoldSensor(CoordinatorEntity[BoldCoordinator], SensorEntity):
    """Show the latest Bold.dk story for a club or league."""

    _attr_icon = "mdi:soccer"

    def __init__(self, coordinator: BoldCoordinator, entry: ConfigEntry, target: Target) -> None:
        super().__init__(coordinator)
        self.target = target
        self._attr_name = target.name
        self._attr_unique_id = f"{entry.entry_id}_{target.url}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Bold.dk",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> str | None:
        """Return the latest headline."""
        stories = self.coordinator.data.get(self.target.url, [])
        return stories[0].title if stories else None

    @property
    def extra_state_attributes(self):
        """Return links and recent headlines for dashboards and automations."""
        stories = self.coordinator.data.get(self.target.url, [])
        return {
            "source_url": self.target.url,
            "latest_url": stories[0].url if stories else None,
            "stories": [
                {"title": story.title, "url": story.url, "published": story.published}
                for story in stories
            ],
        }
