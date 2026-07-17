from __future__ import annotations

from typing import Any

from homeassistant.components.button import ENTITY_ID_FORMAT, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .helpers import build_entity_id
from .const import DOMAIN, REGEN_NOW, REGEN_AT_SCHEDULED


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair buttons from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    api = data["api"]

    async_add_entities(
        [
            PentairSaltAddedButton(coordinator, entry, api),
            PentairRegenerateNowButton(coordinator, entry, api),
            PentairRegenerateScheduledButton(coordinator, entry, api),
        ]
    )


class PentairBaseButton(CoordinatorEntity, ButtonEntity):
    """Bazowa encja przycisku Pentair."""

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
    def _status_code(self) -> int | None:
        return (self._dashboard.get("status") or {}).get("code")

    @property
    def _info(self) -> dict[str, Any]:
        return (self.coordinator.data or {}).get("info") or {}

    @property
    def available(self) -> bool:
        # Jak w aplikacji: akcje wyłączone podczas regeneracji (2) i trybu urlopowego (3).
        if not self.coordinator.last_update_success:
            return False
        return self._status_code not in (2, 3)

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


class PentairSaltAddedButton(PentairBaseButton):
    """Potwierdź dodanie soli (reset alarmu soli)."""

    _attr_translation_key = "salt_added"
    _attr_icon = "mdi:shaker-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_salt_added"

    async def async_press(self) -> None:
        await self._api.set_salt_added()
        await self.coordinator.async_request_refresh()


class PentairRegenerateNowButton(PentairBaseButton):
    """Uruchom regenerację teraz."""

    _attr_translation_key = "regenerate_now"
    _attr_icon = "mdi:refresh"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_regenerate_now"

    async def async_press(self) -> None:
        await self._api.do_regeneration(REGEN_NOW)
        await self.coordinator.async_request_refresh()


class PentairRegenerateScheduledButton(PentairBaseButton):
    """Zaplanuj regenerację na zaplanowaną godzinę."""

    _attr_translation_key = "regenerate_scheduled"
    _attr_icon = "mdi:clock-outline"

    @property
    def unique_id(self) -> str:
        return f"{self._entry.entry_id}_regenerate_scheduled"

    async def async_press(self) -> None:
        await self._api.do_regeneration(REGEN_AT_SCHEDULED)
        await self.coordinator.async_request_refresh()
