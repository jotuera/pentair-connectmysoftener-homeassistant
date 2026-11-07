"""Config flow: sign-in, reauth and reconfigure (password change)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.pentair_softener.api import PentairApiError, PentairAuthError
from custom_components.pentair_softener.const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

TEST = "custom_components.pentair_softener.config_flow._test_credentials"


async def test_user_flow_creates_entry(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    with (
        patch(TEST, AsyncMock(return_value=None)),
        patch(
            "custom_components.pentair_softener.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: " User@Example.com ", CONF_PASSWORD: "secret"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_EMAIL: "User@Example.com", CONF_PASSWORD: "secret"}
    assert result["result"].unique_id == "user@example.com"


async def test_user_flow_errors(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    for error, key in (
        (PentairAuthError("x"), "auth_failed"),
        (PentairApiError("x"), "cannot_connect"),
        (RuntimeError("x"), "unknown"),
    ):
        with patch(TEST, AsyncMock(side_effect=error)):
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_EMAIL: "user@example.com", CONF_PASSWORD: "bad"},
            )
        assert result["type"] is FlowResultType.FORM
        assert result["errors"] == {"base": key}


async def test_duplicate_account_aborts(hass, config_entry):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(TEST, AsyncMock(return_value=None)):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_EMAIL: "USER@example.com", CONF_PASSWORD: "secret"},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def _start(hass, config_entry, source: str):
    return await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": source, "entry_id": config_entry.entry_id},
        data=config_entry.data,
    )


async def test_reauth_updates_password(hass, config_entry):
    result = await _start(hass, config_entry, config_entries.SOURCE_REAUTH)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(TEST, AsyncMock(side_effect=PentairAuthError("x"))):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "still-wrong"}
        )
    assert result["errors"] == {"base": "auth_failed"}

    with (
        patch(TEST, AsyncMock(return_value=None)),
        patch(
            "custom_components.pentair_softener.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "new-secret"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[CONF_PASSWORD] == "new-secret"


async def test_reconfigure_updates_password(hass, config_entry):
    result = await _start(hass, config_entry, config_entries.SOURCE_RECONFIGURE)
    assert result["step_id"] == "reconfigure"

    with (
        patch(TEST, AsyncMock(return_value=None)),
        patch(
            "custom_components.pentair_softener.async_setup_entry",
            AsyncMock(return_value=True),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_PASSWORD: "changed"}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_PASSWORD] == "changed"
