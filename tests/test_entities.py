"""Writable entities send the same payloads as the ConnectMySoftener app."""

from __future__ import annotations

async def _setup(hass, config_entry):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()


async def test_daily_recharge_switch(hass, config_entry, mock_cloud):
    await _setup(hass, config_entry)

    await hass.services.async_call(
        "switch",
        "turn_off",
        {"entity_id": "switch.softener_daily_recharge"},
        blocking=True,
    )
    mock_cloud["save_settings"].assert_awaited_with({"oxy_function": 0})


async def test_notification_switch_sends_both_values(hass, config_entry, mock_cloud):
    await _setup(hass, config_entry)

    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.softener_maintenance_notification"},
        blocking=True,
    )
    mock_cloud["save_settings"].assert_awaited_with(
        {"salt_alarm": True, "maintenance": True}
    )


async def test_recharge_interval_number(hass, config_entry, mock_cloud):
    await _setup(hass, config_entry)

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.softener_recharge_interval", "value": 10},
        blocking=True,
    )
    mock_cloud["save_settings"].assert_awaited_with({"override_1": 10})


async def test_regenerate_button_refreshes_slow_data(hass, config_entry, mock_cloud):
    await _setup(hass, config_entry)
    info_calls = mock_cloud["get_info"].call_count

    await hass.services.async_call(
        "button",
        "press",
        {"entity_id": "button.softener_regenerate_now"},
        blocking=True,
    )
    await hass.async_block_till_done()

    mock_cloud["save_settings"].assert_awaited_with({"regenerate": 1})
    assert mock_cloud["get_info"].call_count == info_calls + 1


async def test_features_unknown_falls_back_to_settings(
    hass, config_entry, mock_cloud
):
    """Without /features, an entity exists only if its setting is in /settings."""
    mock_cloud["get_features"].return_value = {}
    await _setup(hass, config_entry)

    assert hass.states.get("switch.softener_daily_recharge") is not None
    assert hass.states.get("number.softener_recharge_interval") is not None
    assert hass.states.get("number.softener_recharge_interval_oxy") is None
