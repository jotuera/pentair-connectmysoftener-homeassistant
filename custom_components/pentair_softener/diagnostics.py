"""Diagnostyka do pobrania (Urządzenia i usługi → Pentair → ⋮ → Pobierz diagnostykę).

Plik pomaga w zgłoszeniach błędów i w ustaleniu, jakie modele są obsługiwane.
Dane osobowe i identyfikatory są zastępowane przez **REDACTED**."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_EMAIL, CONF_PASSWORD

TO_REDACT = {
    CONF_EMAIL,
    CONF_PASSWORD,
    "serial",
    "serial_number",
    "mac",
    "mac_address",
    "address",
    "street",
    "number",
    "city",
    "postal",
    "latitude",
    "longitude",
    "phone",
    "pin",
    "api_key",
    "uid",
    "access-token",
    "client",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime = getattr(entry, "runtime_data", None)
    devices: list[dict[str, Any]] = []
    for coordinator in getattr(runtime, "coordinators", []):
        devices.append(
            {
                "profile": async_redact_data(coordinator.device.profile, TO_REDACT),
                "last_update_success": coordinator.last_update_success,
                "data": async_redact_data(coordinator.data or {}, TO_REDACT),
            }
        )

    return {
        "entry": {
            "version": entry.version,
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "devices": devices,
    }
