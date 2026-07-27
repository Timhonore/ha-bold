"""League and club sensors for Bold.dk."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
"""Sensors for the Bold.dk integration."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import BoldCoordinator
from .models import Club, ClubData


@dataclass(frozen=True, kw_only=True)
class BoldClubSensorDescription(SensorEntityDescription):
    """Describe how a club value is represented."""

    value_fn: Callable[[ClubData], Any]
    attributes_fn: Callable[[ClubData], dict[str, Any]] = lambda data: {}


CLUB_SENSORS = (
    BoldClubSensorDescription(
        key="position",
        translation_key="position",
        icon="mdi:format-list-numbered",
        value_fn=lambda data: data.position,
    ),
    BoldClubSensorDescription(
        key="last_match",
        translation_key="last_match",
        icon="mdi:history",
        value_fn=lambda data: data.last_match.description if data.last_match else None,
    ),
    BoldClubSensorDescription(
        key="next_match",
        translation_key="next_match",
        icon="mdi:calendar-clock",
        value_fn=lambda data: data.next_match.description if data.next_match else None,
    ),
    BoldClubSensorDescription(
        key="top_scorer",
        translation_key="top_scorer",
        icon="mdi:soccer",
        value_fn=lambda data: data.top_scorer,
        attributes_fn=lambda data: {"goals": data.top_scorer_goals},
    ),
)
from .models import Target


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Create a league sensor and four sensors per selected club."""
    coordinator: BoldCoordinator = entry.runtime_data
    entities: list[SensorEntity] = [BoldLeagueSensor(coordinator, entry)]
    entities.extend(
        BoldClubSensor(coordinator, entry, club, description)
        for club in coordinator.clubs
        for description in CLUB_SENSORS
    )
    async_add_entities(entities)


class BoldLeagueSensor(CoordinatorEntity[BoldCoordinator], SensorEntity):
    """Represent the selected league and its current table."""

    _attr_icon = "mdi:trophy"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: BoldCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_name = entry.title
        self._attr_unique_id = f"{entry.entry_id}_league"
        self._attr_device_info = _device_info(entry.entry_id, entry.title, coordinator.league_url)

    @property
    def native_value(self) -> int:
        """Return the number of teams found in the table."""
        return len(self.coordinator.data.standings)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the complete league table."""
        return {
            "source_url": self.coordinator.league_url,
            "standings": [
                {"position": position, "club": club}
                for position, club in self.coordinator.data.standings
            ],
        }


class BoldClubSensor(CoordinatorEntity[BoldCoordinator], SensorEntity):
    """Represent one club statistic."""

    entity_description: BoldClubSensorDescription

    def __init__(
        self,
        coordinator: BoldCoordinator,
        entry: ConfigEntry,
        club: Club,
        description: BoldClubSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.club = club
        self.entity_description = description
        self._attr_has_entity_name = True
        self._attr_unique_id = f"{entry.entry_id}_{club.url}_{description.key}"
        self._attr_device_info = _device_info(club.url, club.name, club.url)

    @property
    def native_value(self) -> Any:
        """Return the statistic value."""
        return self.entity_description.value_fn(self.coordinator.data.clubs[self.club.url])

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return source and statistic-specific details."""
        data = self.coordinator.data.clubs[self.club.url]
        return {"source_url": self.club.url, **self.entity_description.attributes_fn(data)}


def _device_info(identifier: str, name: str, configuration_url: str) -> dict[str, Any]:
    return {
        "identifiers": {(DOMAIN, identifier)},
        "name": name,
        "manufacturer": "Bold.dk",
        "configuration_url": configuration_url,
    }
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
