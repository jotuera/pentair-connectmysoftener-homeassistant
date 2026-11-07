from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import PentairDevice
from .const import DOMAIN, FEATURE_AVAILABLE, UNITS_US
from .coordinator import PentairCoordinator


class PentairEntity(CoordinatorEntity[PentairCoordinator]):
    """Wspólna baza encji Pentair: urządzenie, unique_id, entity_id i dane.

    Podklasa ustawia _attr_translation_key oraz _unique_suffix (część unique_id
    po prefiksie – zachowana z poprzednich wersji, żeby nie zmieniać encji)."""

    _attr_has_entity_name = True
    _unique_suffix: str
    # ENTITY_ID_FORMAT platformy (np. "sensor.{}"), ustawiany w klasach platform.
    _entity_id_format: str

    def __init__(self, coordinator: PentairCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.unique_prefix}_{self._unique_suffix}"
        self.entity_id = self._build_entity_id()

    def _build_entity_id(self) -> str | None:
        """Zbuduj entity_id z angielskiego klucza, niezależnie od języka HA.

        Domyślnie HA generuje entity_id z *przetłumaczonej* nazwy encji, więc w polskim
        Home Assistancie powstałoby np. sensor.<device>_objetosc_calkowita zamiast
        sensor.<device>_total_volume. entity_id ma być stabilnym identyfikatorem, a nie
        tekstem dla użytkownika – tłumaczymy tylko nazwę wyświetlaną (translation_key).
        Encje już zarejestrowane zachowują swoje entity_id (decyduje rejestr)."""
        key = self.translation_key
        if not key:
            return None
        return async_generate_entity_id(
            self._entity_id_format,
            f"{self.device_name} {key}",
            hass=self.coordinator.hass,
        )

    @property
    def device(self) -> PentairDevice:
        return self.coordinator.device

    @property
    def device_name(self) -> str:
        return self.device.profile.get("name") or "Pentair Softener"

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self.coordinator.device_identifier)},
            "name": self.device_name,
            "manufacturer": "Pentair",
            "model": "ConnectMySoftener",
            "serial_number": self.coordinator.serial,
            "sw_version": self._info.get("software"),
        }

    # --- dane z koordynatora -------------------------------------------------

    @property
    def _data(self) -> dict[str, Any]:
        return self.coordinator.data or {}

    @property
    def _dashboard(self) -> dict[str, Any]:
        return self._data.get("dashboard") or {}

    @property
    def _status(self) -> dict[str, Any]:
        return self._dashboard.get("status") or {}

    @property
    def _status_code(self) -> int | None:
        return self._status.get("code")

    @property
    def _meta(self) -> dict[str, Any]:
        return self._dashboard.get("meta") or {}

    @property
    def _flow(self) -> dict[str, Any]:
        return self._data.get("flow") or {}

    @property
    def _info(self) -> dict[str, Any]:
        return self._data.get("info") or {}

    @property
    def _settings_payload(self) -> dict[str, Any]:
        # /settings zwraca {settings: {...}, notifications: {...}}
        return self._data.get("settings") or {}

    @property
    def _settings(self) -> dict[str, Any]:
        return self._settings_payload.get("settings") or {}

    @property
    def _notifications(self) -> dict[str, Any]:
        return self._settings_payload.get("notifications") or {}

    @property
    def _is_us_units(self) -> bool:
        return self._meta.get("units") == UNITS_US


def feature_supported(
    coordinator: PentairCoordinator, feature: str, present: bool
) -> bool:
    """Czy utworzyć encję dla ustawienia zależnego od modelu.

    Gdy znamy flagi funkcji (/features), decyduje flaga == 'available' – tak jak
    w aplikacji. Gdy flag nie udało się pobrać, tworzymy encję tylko wtedy, gdy
    ustawienie występuje w odpowiedzi /settings (present)."""
    features = (coordinator.data or {}).get("features") or {}
    if features:
        return features.get(feature) == FEATURE_AVAILABLE
    return present
