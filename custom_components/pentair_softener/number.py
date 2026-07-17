from __future__ import annotations

from typing import Any

from homeassistant.components.number import (
    ENTITY_ID_FORMAT,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import build_entity_id
from .const import DOMAIN, HOLIDAY_MODE_MAX_DAYS, HARDNESS_MIN, HARDNESS_MAX


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair number entities from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        [
            PentairHolidayModeNumber(coordinator, entry, api),
            PentairHardnessNumber(coordinator, entry, api),
        ]
    )


class PentairBaseNumber(CoordinatorEntity, NumberEntity):
    """Bazowa encja number Pentair."""

    _attr_has_entity_name = True
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX

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
    def _settings(self) -> dict[str, Any]:
        return ((self.coordinator.data or {}).get("settings") or {}).get(
            "settings"
        ) or {}

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


class PentairHolidayModeNumber(PentairBaseNumber):
    """Tryb urlopowy jako liczba dni: 0 = wyłączony, N = włączony na N dni."""

    _attr_translation_key = "holiday_mode"
    _attr_icon = "mdi:palm-tree"
    _attr_native_min_value = 0
    _attr_native_max_value = HOLIDAY_MODE_MAX_DAYS
    _attr_native_unit_of_measurement = "d"

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


class PentairHardnessNumber(PentairBaseNumber):
    """Twardość wody na wejściu – zapisywalna, jak w ustawieniach aplikacji.

    Jednostka pochodzi z hard_units (np. °d, °f, ppm)."""

    _attr_translation_key = "water_hardness"
    _attr_icon = "mdi:water-opacity"
    _attr_native_min_value = HARDNESS_MIN
    _attr_native_max_value = HARDNESS_MAX

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_water_hardness"

    @property
    def native_unit_of_measurement(self) -> str | None:
        hard_units = self._settings.get("hard_units")
        if isinstance(hard_units, dict):
            return hard_units.get("value")
        return None

    @property
    def native_value(self) -> int | None:
        value = self._settings.get("install_hardness")
        if isinstance(value, bool) or value in (None, ""):
            return None
        try:
            return int(round(float(str(value).replace(",", "."))))
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self._api.set_hardness(int(value))
        await self.coordinator.async_request_refresh()
