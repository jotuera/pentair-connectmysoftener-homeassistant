from __future__ import annotations

from typing import Any

from homeassistant.components.number import (
    ENTITY_ID_FORMAT,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    HOLIDAY_MODE_MAX_DAYS,
    HARDNESS_MIN,
    HARDNESS_MAX,
    OVERRIDE_MAX,
    OVERRIDE_MIN,
)
from .entity import PentairEntity, feature_supported


def _to_int(value: Any) -> int | None:
    """Liczba z API (int, float albo tekst '12' / '12,5') -> int; inaczej None."""
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return int(round(float(str(value).replace(",", "."))))
    except (TypeError, ValueError):
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair number entities from a config entry."""
    entities: list[NumberEntity] = []
    for coordinator in entry.runtime_data.coordinators:
        entities += [
            PentairHolidayModeNumber(coordinator),
            PentairHardnessNumber(coordinator),
        ]
        settings = ((coordinator.data or {}).get("settings") or {}).get(
            "settings"
        ) or {}
        for cls in (PentairRechargeIntervalNumber, PentairRechargeIntervalOxyNumber):
            if feature_supported(coordinator, cls.feature, cls.setting in settings):
                entities.append(cls(coordinator))
    async_add_entities(entities)


class PentairBaseNumber(PentairEntity, NumberEntity):
    """Bazowa encja number Pentair."""

    _entity_id_format = ENTITY_ID_FORMAT
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX


class PentairHolidayModeNumber(PentairBaseNumber):
    """Tryb urlopowy jako liczba dni: 0 = wyłączony, N = włączony na N dni."""

    _attr_translation_key = "holiday_mode"
    _unique_suffix = "holiday_mode"
    _attr_icon = "mdi:palm-tree"
    _attr_native_min_value = 0
    _attr_native_max_value = HOLIDAY_MODE_MAX_DAYS
    _attr_native_unit_of_measurement = "d"

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
        await self.device.set_holiday_mode(int(value))
        await self.coordinator.async_refresh_after_action()


class PentairHardnessNumber(PentairBaseNumber):
    """Twardość wody na wejściu – zapisywalna, jak w ustawieniach aplikacji.

    Jednostka pochodzi z hard_units (np. °d, °f, ppm)."""

    _attr_translation_key = "water_hardness"
    _unique_suffix = "water_hardness"
    _attr_icon = "mdi:water-opacity"
    _attr_native_min_value = HARDNESS_MIN
    _attr_native_max_value = HARDNESS_MAX

    @property
    def native_unit_of_measurement(self) -> str | None:
        hard_units = self._settings.get("hard_units")
        if isinstance(hard_units, dict):
            return hard_units.get("value")
        return None

    @property
    def native_value(self) -> int | None:
        return _to_int(self._settings.get("install_hardness"))

    async def async_set_native_value(self, value: float) -> None:
        await self.device.set_hardness(int(value))
        await self.coordinator.async_refresh_after_action()


class PentairOverrideNumber(PentairBaseNumber):
    """Interwał wymuszonej regeneracji/doładowania w dniach (ustawienie 'Interwał').

    Dostępność zależy od modelu – aplikacja pokazuje pole tylko gdy flaga
    funkcji jest 'available'."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_icon = "mdi:calendar-refresh"
    _attr_native_min_value = OVERRIDE_MIN
    _attr_native_max_value = OVERRIDE_MAX
    _attr_native_unit_of_measurement = "d"
    feature: str
    setting: str

    @property
    def native_value(self) -> int | None:
        return _to_int(self._settings.get(self.setting))

    async def async_set_native_value(self, value: float) -> None:
        await self.device.set_override(self.setting, int(value))
        await self.coordinator.async_refresh_after_action()


class PentairRechargeIntervalNumber(PentairOverrideNumber):
    """override_1 – flaga funkcji recharge_interval."""

    _attr_translation_key = "recharge_interval"
    _unique_suffix = "recharge_interval"
    feature = "recharge_interval"
    setting = "override_1"


class PentairRechargeIntervalOxyNumber(PentairOverrideNumber):
    """override_oxy – flaga funkcji recharge_interval_oxy."""

    _attr_translation_key = "recharge_interval_oxy"
    _unique_suffix = "recharge_interval_oxy"
    feature = "recharge_interval_oxy"
    setting = "override_oxy"
