
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_ENABLE_GRAPHS,
    DEFAULT_ENABLE_GRAPHS,
)
from .api import PentairApi, PentairApiError, PentairAuthError

_LOGGER = logging.getLogger(__name__)


async def _test_credentials(hass: HomeAssistant, email: str, password: str) -> None:
    """Sprawdź, czy dane logowania działają."""
    session = async_get_clientsession(hass)
    api = PentairApi(session, email=email, password=password)
    await api.login()  # podniesie PentairAuthError gdy coś nie tak


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow dla Pentair softener."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input[CONF_PASSWORD]

            try:
                await _test_credentials(self.hass, email, password)
            except PentairAuthError:
                errors["base"] = "auth_failed"
            except PentairApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error while testing Pentair credentials")
                errors["base"] = "unknown"

            if not errors:
                await self.async_set_unique_id(email.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Pentair softener ({email})",
                    data={
                        CONF_EMAIL: email,
                        CONF_PASSWORD: password,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "OptionsFlowHandler":
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Opcje integracji Pentair (m.in. historia zużycia wody)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._entry.options.get(
            CONF_ENABLE_GRAPHS, DEFAULT_ENABLE_GRAPHS
        )
        schema = vol.Schema(
            {vol.Optional(CONF_ENABLE_GRAPHS, default=current): bool}
        )
        return self.async_show_form(step_id="init", data_schema=schema)
