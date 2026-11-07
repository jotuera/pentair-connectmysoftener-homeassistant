from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT,
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import WARNING_TYPE_SALT
from .entity import PentairEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair binary sensors from a config entry."""
    async_add_entities(
        cls(coordinator)
        for coordinator in entry.runtime_data.coordinators
        for cls in (
            PentairOnlineBinarySensor,
            PentairSaltWarningBinarySensor,
            PentairPendingChangesBinarySensor,
        )
    )


class PentairBaseBinarySensor(PentairEntity, BinarySensorEntity):
    """Bazowa encja binary_sensor Pentair."""

    _entity_id_format = ENTITY_ID_FORMAT


class PentairOnlineBinarySensor(PentairBaseBinarySensor):
    """Czy urządzenie jest online (status.code != 0)."""

    _attr_translation_key = "online"
    _unique_suffix = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def is_on(self) -> bool | None:
        code = self._status_code
        if code is None:
            return None
        return code != 0


class PentairPendingChangesBinarySensor(PentairBaseBinarySensor):
    """Zmiany wysłane do urządzenia, które jeszcze do niego nie dotarły.

    Odpowiednik żółtej karty 'Oczekujące zmiany' w aplikacji: niepusta lista
    z /pending oznacza, że komenda czeka na zastosowanie."""

    _attr_translation_key = "pending_changes"
    _unique_suffix = "pending_changes"
    _attr_icon = "mdi:sync"

    @property
    def is_on(self) -> bool | None:
        pending = self._data.get("pending")
        if not isinstance(pending, list):
            return None
        return len(pending) > 0


class PentairSaltWarningBinarySensor(PentairBaseBinarySensor):
    """Ostrzeżenie o niskim poziomie soli (warning.type == 1)."""

    _attr_translation_key = "salt_warning"
    _unique_suffix = "salt_warning"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def is_on(self) -> bool | None:
        warnings = self._dashboard.get("warnings")
        if warnings is None:
            return None
        return any(
            isinstance(w, dict) and w.get("type") == WARNING_TYPE_SALT
            for w in warnings
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        warnings = self._dashboard.get("warnings") or []
        return {
            "warnings": [
                w.get("description") for w in warnings if isinstance(w, dict)
            ]
        }
