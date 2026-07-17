from __future__ import annotations

from datetime import datetime, time
import logging
from typing import Any

from homeassistant.components.time import ENTITY_ID_FORMAT, TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import build_entity_id
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _parse_time(value: Any) -> time | None:
    """Parsuj zegar urządzenia: '11:16' (24h) lub '11:16 AM' (US)."""
    if value in (None, ""):
        return None
    text = str(value).strip()
    for fmt in ("%H:%M", "%I:%M %p", "%H:%M:%S", "%I:%M:%S %p"):
        try:
            return datetime.strptime(text, fmt).time()
        except ValueError:
            continue
    _LOGGER.debug("Pentair: cannot parse system_time %r", value)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair time entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([PentairSystemTime(coordinator, entry, api)])


class PentairSystemTime(CoordinatorEntity, TimeEntity):
    """Zegar urządzenia – pozwala sprawdzić, czy nie rozjechał się z realnym czasem.

    Aplikacja wysyła czysty 'HH:MM' (24h), więc tak samo zapisujemy."""

    _attr_has_entity_name = True
    _attr_translation_key = "system_time"
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator, entry: ConfigEntry, api) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self.entity_id = build_entity_id(
            ENTITY_ID_FORMAT, coordinator, api, self.translation_key
        )

    @property
    def _info(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("info") or {}

    @property
    def _settings(self) -> dict[str, Any]:
        return ((self.coordinator.data or {}).get("settings") or {}).get(
            "settings"
        ) or {}

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_system_time"

    @property
    def native_value(self) -> time | None:
        return _parse_time(self._settings.get("system_time"))

    async def async_set_value(self, value: time) -> None:
        await self._api.set_system_time(value.strftime("%H:%M"))
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self) -> dict[str, Any]:
        profile = self._api.profile or {}
        serial = profile.get("serial") or self._info.get("serial")
        return {
            "identifiers": {(DOMAIN, serial or self._entry.entry_id)},
            "name": profile.get("name") or "Pentair Softener",
            "manufacturer": "Pentair",
            "model": "ConnectMySoftener",
        }
