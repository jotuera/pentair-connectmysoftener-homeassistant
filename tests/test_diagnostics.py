"""Diagnostics must not leak credentials or identifiers."""

from __future__ import annotations

import json

from custom_components.pentair_softener.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redacts_private_data(hass, config_entry, mock_cloud):
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await async_get_config_entry_diagnostics(hass, config_entry)
    text = json.dumps(result)

    assert "secret" not in text
    assert "user@example.com" not in text
    assert "S12345678" not in text
    assert result["entry"]["data"]["password"] == "**REDACTED**"
    assert result["devices"][0]["data"]["dashboard"]["status"]["code"] == 1
