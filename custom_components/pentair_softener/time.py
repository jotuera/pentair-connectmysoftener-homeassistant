from __future__ import annotations

from datetime import datetime, time
import logging
from typing import Any

from homeassistant.components.time import ENTITY_ID_FORMAT, TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PentairEntity

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
    async_add_entities(
        PentairSystemTime(coordinator)
        for coordinator in entry.runtime_data.coordinators
    )


class PentairSystemTime(PentairEntity, TimeEntity):
    """Zegar urządzenia – pozwala sprawdzić, czy nie rozjechał się z realnym czasem.

    Aplikacja wysyła czysty 'HH:MM' (24h), więc tak samo zapisujemy."""

    _entity_id_format = ENTITY_ID_FORMAT
    _attr_translation_key = "system_time"
    _unique_suffix = "system_time"
    _attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> time | None:
        return _parse_time(self._settings.get("system_time"))

    async def async_set_value(self, value: time) -> None:
        await self.device.set_system_time(value.strftime("%H:%M"))
        await self.coordinator.async_refresh_after_action()
