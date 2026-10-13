"""Exercise the flow, coordinators and sensors against real Home Assistant APIs."""

import asyncio
import importlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

pytest.importorskip("homeassistant")

from homeassistant.core import HomeAssistant  # noqa: E402

from custom_components.bold_dk.config_flow import BoldConfigFlow  # noqa: E402
from custom_components.bold_dk.coordinator import (  # noqa: E402
    BoldCoordinator,
    BoldStoryCoordinator,
)
from custom_components.bold_dk.models import Club, ClubData, Match, Story  # noqa: E402
from custom_components.bold_dk.sensor import async_setup_entry as setup_sensors  # noqa: E402

integration = importlib.import_module("custom_components.bold_dk.__init__")


def test_league_flow_and_sensor_setup(tmp_path):
    async def scenario():
        hass = HomeAssistant(str(tmp_path))
        hass.config_entries = Mock()
        hass.config_entries.async_entries.return_value = []
        hass.config_entries.flow.async_progress_by_handler.return_value = []
        hass.config_entries.async_entry_for_domain_unique_id.return_value = None
        club = Club("Randers FC", "https://bold.dk/fodbold/klubber/randers-fc")
        client = Mock()
        client.async_get_clubs = AsyncMock(return_value=[club])
        client.async_get_league_data = AsyncMock(
            return_value=([(4, club.name)], {"randers-fc": ("Test Spiller", 3)})
        )
        client.async_get_club_data = AsyncMock(
            return_value=ClubData(club, next_match=Match("Randers FC", "AGF", "2026-10-16 19:00"))
        )
        flow = BoldConfigFlow()
        flow.hass = hass
        flow.context = {}
        with (
            patch("custom_components.bold_dk.config_flow.async_get_clientsession"),
            patch("custom_components.bold_dk.config_flow.BoldApiClient", return_value=client),
        ):
            form = await flow.async_step_user()
            assert form["step_id"] == "user"
            assert set(form["data_schema"].schema) == {"league_name", "league_url"}
            form = await flow.async_step_user(
                {
                    "league_name": "Superligaen",
                    "league_url": "https://bold.dk/fodbold/stillinger/superligaen",
                }
            )
            assert form["step_id"] == "clubs"
            created = await flow.async_step_clubs({"clubs": [club.url]})
        assert created["data"]["clubs"] == [{"name": club.name, "url": club.url}]
        coordinator = BoldCoordinator(
            hass, client, "Superligaen", created["data"]["league_url"], [club]
        )
        coordinator.data = await coordinator._async_update_data()
        coordinator.last_update_success = True
        entry = SimpleNamespace(
            entry_id="league", title="Superligaen", data=created["data"], runtime_data=coordinator
        )
        entities = []
        await setup_sensors(hass, entry, lambda values: entities.extend(values))
        assert len(entities) == 5
        assert entities[0].native_value == 1
        assert entities[1].native_value == 4
        assert "2026-10-16 19:00" in entities[3].native_value
        assert entities[4].native_value == "Test Spiller"
        assert entities[4].extra_state_attributes["goals"] == 3

    asyncio.run(scenario())


@pytest.mark.parametrize("legacy", [False, True], ids=["league", "existing_news"])
def test_entry_setup_and_migration(tmp_path, legacy):
    async def scenario():
        hass = HomeAssistant(str(tmp_path))
        hass.config_entries = Mock()
        hass.config_entries.async_forward_entry_setups = AsyncMock()
        data = (
            {
                "targets": [
                    {"name": "Randers FC", "url": "https://bold.dk/fodbold/klubber/randers-fc"}
                ]
            }
            if legacy
            else {
                "league_name": "Superligaen",
                "league_url": "https://bold.dk/fodbold/stillinger/superligaen",
                "clubs": [
                    {"name": "Randers FC", "url": "https://bold.dk/fodbold/klubber/randers-fc"}
                ],
            }
        )
        entry = SimpleNamespace(
            version=1,
            data=data,
            title="Bold.dk",
            entry_id="test",
            runtime_data=None,
            async_on_unload=Mock(),
        )
        with (
            patch.object(integration, "async_get_clientsession"),
            patch.object(BoldCoordinator, "async_config_entry_first_refresh", new=AsyncMock()),
            patch.object(BoldStoryCoordinator, "async_config_entry_first_refresh", new=AsyncMock()),
        ):
            assert await integration.async_migrate_entry(hass, entry)
            hass.config_entries.async_update_entry.assert_called_once_with(entry, version=2)
            assert await integration.async_setup_entry(hass, entry)
        expected = BoldStoryCoordinator if legacy else BoldCoordinator
        assert isinstance(entry.runtime_data, expected)
        hass.config_entries.async_forward_entry_setups.assert_awaited_once_with(entry, ["sensor"])
        if legacy:
            entry.runtime_data.data = {
                data["targets"][0]["url"]: [
                    Story("En nyhed", "https://bold.dk/fodbold/nyheder/test")
                ]
            }
            entry.runtime_data.last_update_success = True
            entities = []
            await setup_sensors(hass, entry, lambda values: entities.extend(values))
            assert len(entities) == 1
            assert entities[0].native_value == "En nyhed"

    asyncio.run(scenario())
