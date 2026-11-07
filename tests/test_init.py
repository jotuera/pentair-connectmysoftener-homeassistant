"""Setup, entities, multi-device, reauth and tiered refresh."""

from __future__ import annotations

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from custom_components.pentair_softener.api import PentairApiError, PentairAuthError
from custom_components.pentair_softener.const import CONF_PRIMARY_DEVICE_ID, DOMAIN

from .conftest import ENTRY_ID


def _unique_ids(hass: HomeAssistant) -> set[str]:
    registry = er.async_get(hass)
    return {
        e.unique_id
        for e in er.async_entries_for_config_entry(registry, ENTRY_ID)
    }


async def test_setup_keeps_unique_ids(hass, config_entry, mock_cloud):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED
    assert config_entry.data[CONF_PRIMARY_DEVICE_ID] == "111"

    ids = _unique_ids(hass)
    # Unique IDs from earlier versions must not change.
    for suffix in (
        "status",
        "regeneration_progress",
        "total_volume",
        "salt_warning",
        "online",
        "salt_added",
        "holiday_mode",
        "water_hardness",
        "system_time",
    ):
        assert f"{ENTRY_ID}_{suffix}" in ids
    # New, feature-gated entities.
    assert f"{ENTRY_ID}_daily_recharge" in ids
    assert f"{ENTRY_ID}_recharge_interval" in ids
    assert f"{ENTRY_ID}_salt_alarm_notification" in ids
    assert f"{ENTRY_ID}_maintenance_notification" in ids
    assert f"{ENTRY_ID}_recharge_interval_oxy" not in ids

    assert hass.states.get("sensor.softener_total_volume").state == "12345"
    assert hass.states.get("switch.softener_daily_recharge").state == "on"
    assert hass.states.get("number.softener_recharge_interval").state == "7"


async def test_multiple_devices(hass, config_entry, mock_cloud, profiles):
    profiles.append({"id": 222, "name": "Garage", "serial": "S87654321"})

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    ids = _unique_ids(hass)
    assert f"{ENTRY_ID}_status" in ids
    assert f"{ENTRY_ID}_222_status" in ids
    assert hass.states.get("sensor.garage_status") is not None
    assert len(config_entry.runtime_data.coordinators) == 2


async def test_primary_device_stays_primary(hass, config_entry, mock_cloud, profiles):
    """A new softener listed first must not take over the old unique IDs."""
    hass.config_entries.async_update_entry(
        config_entry, data={**config_entry.data, CONF_PRIMARY_DEVICE_ID: "111"}
    )
    profiles.insert(0, {"id": 222, "name": "Garage", "serial": "S87654321"})

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    registry = er.async_get(hass)
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, f"{ENTRY_ID}_status")
    assert entity_id == "sensor.softener_status"


async def test_auth_error_starts_reauth(hass, config_entry, mock_cloud):
    mock_cloud["get_devices"].side_effect = PentairAuthError("bad password")

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == SOURCE_REAUTH for f in flows)


async def test_cloud_error_retries_later(hass, config_entry, mock_cloud):
    mock_cloud["get_devices"].side_effect = PentairApiError("server down")

    assert not await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_tiered_refresh(hass, config_entry, mock_cloud):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinators[0]

    assert mock_cloud["get_dashboard"].call_count == 1
    assert mock_cloud["get_info"].call_count == 1

    # Regular poll: only live data.
    await coordinator.async_refresh()
    assert mock_cloud["get_dashboard"].call_count == 2
    assert mock_cloud["get_flow"].call_count == 2
    assert mock_cloud["get_info"].call_count == 1
    assert mock_cloud["get_settings"].call_count == 1

    # A status change (e.g. regeneration started) refreshes the slow data too.
    regenerating = {**mock_cloud["get_dashboard"].return_value}
    regenerating["status"] = {**regenerating["status"], "code": 2}
    mock_cloud["get_dashboard"].return_value = regenerating
    await coordinator.async_refresh()
    assert mock_cloud["get_info"].call_count == 2


async def test_optional_endpoint_error_keeps_previous_value(
    hass, config_entry, mock_cloud
):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinators[0]

    mock_cloud["get_info"].side_effect = PentairApiError("timeout")
    coordinator._force_slow = True
    await coordinator.async_refresh()

    assert coordinator.data["info"]["total_volume"] == "12345 L"


async def test_dashboard_auth_error_triggers_reauth(hass, config_entry, mock_cloud):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    coordinator = config_entry.runtime_data.coordinators[0]

    mock_cloud["get_dashboard"].side_effect = PentairAuthError("expired")
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert any(f["context"]["source"] == SOURCE_REAUTH for f in flows)


async def test_unload(hass, config_entry, mock_cloud):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED
