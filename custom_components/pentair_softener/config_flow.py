from __future__ import annotations

from collections.abc import Mapping
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
    """Zaloguj się i sprawdź, czy na koncie jest zmiękczacz.

    PentairAuthError = złe dane logowania, PentairApiError = brak połączenia /
    brak urządzenia na koncie."""
    session = async_get_clientsession(hass)
    api = PentairApi(session, email=email, password=password)
    await api.login()
    await api.get_devices()


async def _errors_for(hass: HomeAssistant, email: str, password: str) -> dict[str, str]:
    try:
        await _test_credentials(hass, email, password)
    except PentairAuthError:
        return {"base": "auth_failed"}
    except PentairApiError:
        return {"base": "cannot_connect"}
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unexpected error while testing Pentair credentials")
        return {"base": "unknown"}
    return {}


PASSWORD_SCHEMA = vol.Schema({vol.Required(CONF_PASSWORD): str})


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow dla Pentair softener."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].strip()
            password = user_input[CONF_PASSWORD]

            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            errors = await _errors_for(self.hass, email, password)
            if not errors:
                return self.async_create_entry(
                    title=f"Pentair softener ({email})",
                    data={CONF_EMAIL: email, CONF_PASSWORD: password},
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_EMAIL): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )

    # --- zmiana hasła: wymuszona (reauth) albo z menu (reconfigure) -----------

    def _context_entry(self) -> config_entries.ConfigEntry:
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        if entry is None:  # pragma: no cover - HA zawsze podaje entry_id
            raise RuntimeError("Config entry not found")
        return entry

    async def _async_password_step(
        self, step_id: str, reason: str, user_input: dict[str, Any] | None
    ) -> FlowResult:
        entry = self._context_entry()
        email = entry.data[CONF_EMAIL]
        errors: dict[str, str] = {}

        if user_input is not None:
            password = user_input[CONF_PASSWORD]
            errors = await _errors_for(self.hass, email, password)
            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, CONF_PASSWORD: password},
                    reason=reason,
                )

        return self.async_show_form(
            step_id=step_id,
            data_schema=PASSWORD_SCHEMA,
            errors=errors,
            description_placeholders={"email": email},
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]) -> FlowResult:
        """HA uruchamia ten krok, gdy chmura odrzuci zapisane dane logowania."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self._async_password_step(
            "reauth_confirm", "reauth_successful", user_input
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Zmiana hasła z menu integracji (⋮ → Zmień konfigurację)."""
        return await self._async_password_step(
            "reconfigure", "reconfigure_successful", user_input
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
