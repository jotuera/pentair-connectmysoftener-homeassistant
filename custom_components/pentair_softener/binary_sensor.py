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
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import build_entity_id
from .const import DOMAIN, WARNING_TYPE_SALT


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair binary sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        [
            PentairOnlineBinarySensor(coordinator, entry, api),
            PentairSaltWarningBinarySensor(coordinator, entry, api),
            PentairPendingChangesBinarySensor(coordinator, entry, api),
        ]
    )


class PentairBaseBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Bazowa encja binary_sensor Pentair."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, api) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api
        self.entity_id = build_entity_id(
            ENTITY_ID_FORMAT, coordinator, api, self.translation_key
        )

    @property
    def _dashboard(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("dashboard") or {}

    @property
    def _info(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("info") or {}

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


class PentairOnlineBinarySensor(PentairBaseBinarySensor):
    """Czy urządzenie jest online (status.code != 0)."""

    _attr_translation_key = "online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_online"

    @property
    def is_on(self) -> bool | None:
        status = self._dashboard.get("status") or {}
        code = status.get("code")
        if code is None:
            return None
        return code != 0


class PentairPendingChangesBinarySensor(PentairBaseBinarySensor):
    """Zmiany wysłane do urządzenia, które jeszcze do niego nie dotarły.

    Odpowiednik żółtej karty 'Oczekujące zmiany' w aplikacji: niepusta lista
    z /pending oznacza, że komenda czeka na zastosowanie."""

    _attr_translation_key = "pending_changes"
    _attr_icon = "mdi:sync"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_pending_changes"

    @property
    def is_on(self) -> bool | None:
        pending = (self.coordinator.data or {}).get("pending")
        if not isinstance(pending, list):
            return None
        return len(pending) > 0


class PentairSaltWarningBinarySensor(PentairBaseBinarySensor):
    """Ostrzeżenie o niskim poziomie soli (warning.type == 1)."""

    _attr_translation_key = "salt_warning"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_salt_warning"

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
