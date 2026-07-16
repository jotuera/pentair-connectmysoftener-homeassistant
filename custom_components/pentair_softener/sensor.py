from __future__ import annotations

import re
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    STATUS_CODES,
    UNITS_US,
    CONF_ENABLE_GRAPHS,
    DEFAULT_ENABLE_GRAPHS,
    GRAPH_INTERVALS,
)


def _first_float(value: Any) -> float | None:
    """Wyciągnij liczbę z wartości typu 12, "12", "1234 L" itp."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    match = re.search(r"-?\d+(?:[.,]\d+)?", str(value))
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", "."))
    except ValueError:
        return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair sensors from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    entities: list[SensorEntity] = [
        PentairStatusSensor(coordinator, entry, api),
        PentairStatusProgressSensor(coordinator, entry, api),
        PentairRemainingCapacitySensor(coordinator, entry, api),
        PentairDaysRemainingSensor(coordinator, entry, api),
        PentairHardnessSensor(coordinator, entry, api),
        PentairCurrentFlowSensor(coordinator, entry, api),
        PentairTotalVolumeSensor(coordinator, entry, api),
        PentairRegenerationCountSensor(coordinator, entry, api),
        PentairLastRegenerationSensor(coordinator, entry, api),
        PentairLastMaintenanceSensor(coordinator, entry, api),
        PentairWarningsSensor(coordinator, entry, api),
        PentairSerialNumberSensor(coordinator, entry, api),
        PentairSoftwareVersionSensor(coordinator, entry, api),
    ]

    if entry.options.get(CONF_ENABLE_GRAPHS, DEFAULT_ENABLE_GRAPHS):
        entities += [
            PentairWaterUsageSensor(coordinator, entry, api, interval)
            for interval in GRAPH_INTERVALS
        ]

    async_add_entities(entities)


class PentairBaseSensor(CoordinatorEntity, SensorEntity):
    """Bazowa encja sensora Pentair."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, api) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._api = api

    @property
    def _dashboard(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("dashboard") or {}

    @property
    def _status(self) -> dict[str, Any]:
        return self._dashboard.get("status") or {}

    @property
    def _meta(self) -> dict[str, Any]:
        return self._dashboard.get("meta") or {}

    @property
    def _flow(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("flow") or {}

    @property
    def _info(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("info") or {}

    @property
    def _settings(self) -> dict[str, Any]:
        # /settings zwraca {settings: {...}, notifications: {...}}
        return ((self.coordinator.data or {}).get("settings") or {}).get(
            "settings"
        ) or {}

    @property
    def _is_us_units(self) -> bool:
        return self._meta.get("units") == UNITS_US

    @property
    def device_info(self) -> dict[str, Any]:
        profile = self._api.profile or {}
        serial = profile.get("serial") or self._info.get("serial")
        return {
            "identifiers": {(DOMAIN, serial or self._entry.entry_id)},
            "name": profile.get("name") or "Pentair Softener",
            "manufacturer": "Pentair",
            "model": "ConnectMySoftener",
            "serial_number": serial,
            "sw_version": self._info.get("software"),
        }


class PentairStatusSensor(PentairBaseSensor):
    """Stan urządzenia (in_service / regenerating / holiday / standby / offline)."""

    _attr_translation_key = "status"
    _attr_icon = "mdi:water-sync"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_status"

    @property
    def native_value(self) -> str | None:
        code = self._status.get("code")
        if code is None:
            return None
        return STATUS_CODES.get(code, "unknown")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {
            "title": self._status.get("title"),
            "extra": self._status.get("extra"),
            "regen_time": self._meta.get("regen_time"),
            "holiday_mode": self._dashboard.get("holiday_mode"),
        }


class PentairStatusProgressSensor(PentairBaseSensor):
    """Pasek postępu z pulpitu (%): pozostała pojemność w trybie pracy,
    a podczas regeneracji – postęp regeneracji."""

    _attr_translation_key = "status_progress"
    _attr_native_unit_of_measurement = "%"
    _attr_icon = "mdi:gauge"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_regeneration_progress"

    @property
    def native_value(self) -> float | None:
        return _first_float(self._status.get("percentage"))


class PentairRemainingCapacitySensor(PentairBaseSensor):
    """Pozostała pojemność urządzenia (status.extra), np. 2216 L.

    W trybie regeneracji status.extra zawiera pozostały czas, nie objętość,
    więc wtedy nie raportujemy wartości liczbowej."""

    _attr_translation_key = "remaining_capacity"
    _attr_icon = "mdi:water-percent"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_remaining_capacity"

    @property
    def native_unit_of_measurement(self) -> str:
        return "gal" if self._is_us_units else "L"

    @property
    def native_value(self) -> float | None:
        # status.code 2 = regenerating -> extra to czas, nie pojemność
        if self._status.get("code") == 2:
            return None
        return _first_float(self._status.get("extra"))


class PentairDaysRemainingSensor(PentairBaseSensor):
    """Szacowana liczba dni do wyczerpania pojemności."""

    _attr_translation_key = "days_remaining"
    _attr_native_unit_of_measurement = "d"
    _attr_icon = "mdi:calendar-clock"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_days_remaining"

    @property
    def native_value(self) -> float | None:
        return _first_float(self._status.get("days_remaining"))


class PentairHardnessSensor(PentairBaseSensor):
    """Skonfigurowana twardość wody na wejściu (np. 21 °d)."""

    _attr_translation_key = "water_hardness"
    _attr_icon = "mdi:water-opacity"

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
    def native_value(self) -> float | None:
        return _first_float(self._settings.get("install_hardness"))


class PentairCurrentFlowSensor(PentairBaseSensor):
    """Chwilowy przepływ wody."""

    _attr_translation_key = "current_flow"
    _attr_icon = "mdi:water"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_current_flow"

    @property
    def native_unit_of_measurement(self) -> str:
        return "gal/min" if self._is_us_units else "L/min"

    @property
    def native_value(self) -> float | None:
        return _first_float(self._flow.get("flow"))


class PentairTotalVolumeSensor(PentairBaseSensor):
    """Całkowita objętość uzdatnionej wody od instalacji."""

    _attr_translation_key = "total_volume"
    _attr_device_class = SensorDeviceClass.WATER
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:water-pump"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_total_volume"

    @property
    def native_unit_of_measurement(self) -> str:
        return "gal" if self._is_us_units else "L"

    @property
    def native_value(self) -> float | None:
        return _first_float(self._info.get("total_volume"))


class PentairRegenerationCountSensor(PentairBaseSensor):
    """Łączna liczba regeneracji."""

    _attr_translation_key = "regeneration_count"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_regeneration_count"

    @property
    def native_value(self) -> float | None:
        return _first_float(self._info.get("nr_regenerations"))


class PentairLastRegenerationSensor(PentairBaseSensor):
    """Data ostatniej regeneracji (surowa wartość z API)."""

    _attr_translation_key = "last_regeneration"
    _attr_icon = "mdi:history"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_last_regeneration"

    @property
    def native_value(self) -> str | None:
        value = self._info.get("last_regeneration")
        return str(value) if value not in (None, "") else None


class PentairLastMaintenanceSensor(PentairBaseSensor):
    """Data ostatniej konserwacji (surowa wartość z API)."""

    _attr_translation_key = "last_maintenance"
    _attr_icon = "mdi:wrench-clock"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_last_maintenance"

    @property
    def native_value(self) -> str | None:
        value = self._info.get("last_maintenance")
        return str(value) if value not in (None, "") else None


class PentairWarningsSensor(PentairBaseSensor):
    """Liczba aktywnych ostrzeżeń; opisy dostępne w atrybucie."""

    _attr_translation_key = "warnings"
    _attr_icon = "mdi:alert"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_warnings"

    @property
    def native_value(self) -> int | None:
        warnings = self._dashboard.get("warnings")
        if warnings is None:
            return None
        return len(warnings)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        warnings = self._dashboard.get("warnings") or []
        return {
            "warnings": [
                w.get("description") for w in warnings if isinstance(w, dict)
            ],
            "types": [
                w.get("type") for w in warnings if isinstance(w, dict)
            ],
        }


class PentairWaterUsageSensor(PentairBaseSensor):
    """Zużycie wody z /graphs dla okresu day/week/month/year (jak w aplikacji).

    Aktywny tylko gdy w opcjach integracji włączono pobieranie historii zużycia."""

    _attr_icon = "mdi:chart-bar"

    def __init__(self, coordinator, entry: ConfigEntry, api, interval: str) -> None:
        super().__init__(coordinator, entry, api)
        self._interval = interval
        self._attr_translation_key = f"water_used_{interval}"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_water_used_{self._interval}"

    @property
    def native_unit_of_measurement(self) -> str:
        return "gal" if self._is_us_units else "L"

    @property
    def native_value(self) -> float | None:
        usage = (self.coordinator.data or {}).get("usage") or {}
        return usage.get(self._interval)


class PentairSerialNumberSensor(PentairBaseSensor):
    """Numer seryjny urządzenia (diagnostyka).

    API nie udostępnia osobnego pola 'model'; numer seryjny to najbliższa
    trwała informacja identyfikująca sprzęt."""

    _attr_translation_key = "serial_number"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:identifier"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_serial_number"

    @property
    def native_value(self) -> str | None:
        profile = self._api.profile or {}
        value = profile.get("serial") or self._info.get("serial")
        return str(value) if value not in (None, "") else None


class PentairSoftwareVersionSensor(PentairBaseSensor):
    """Wersja oprogramowania urządzenia (diagnostyka)."""

    _attr_translation_key = "software_version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:chip"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_software_version"

    @property
    def native_value(self) -> str | None:
        value = self._info.get("software")
        return str(value) if value not in (None, "") else None
