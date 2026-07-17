from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, HOLIDAY_MODE_MAX_DAYS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair number entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities([PentairHolidayModeNumber(coordinator, entry, api)])


class PentairHolidayModeNumber(CoordinatorEntity, NumberEntity):
    """Tryb urlopowy jako liczba dni: 0 = wyłączony, N = włączony na N dni."""

    _attr_has_entity_name = True
    _attr_translation_key = "holiday_mode"
    _attr_icon = "mdi:palm-tree"
    _attr_native_min_value = 0
    _attr_native_max_value = HOLIDAY_MODE_MAX_DAYS
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "d"
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator, entry: ConfigEntry, api) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api

    @property
    def _dashboard(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("dashboard") or {}

    @property
    def _info(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("info") or {}

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_holiday_mode"

    @property
    def native_value(self) -> int | None:
        value = self._dashboard.get("holiday_mode")
        # API bywa bool (wł./wył.) albo liczba dni – normalizujemy do pełnych dni.
        if isinstance(value, bool):
            return 1 if value else 0
        if isinstance(value, (int, float)):
            return int(round(value))
        return None

    async def async_set_native_value(self, value: float) -> None:
        await self._api.set_holiday_mode(int(value))
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
