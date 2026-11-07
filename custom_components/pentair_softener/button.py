from __future__ import annotations

from homeassistant.components.button import ENTITY_ID_FORMAT, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import REGEN_NOW, REGEN_AT_SCHEDULED, STATUS_HOLIDAY, STATUS_REGENERATING
from .entity import PentairEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair buttons from a config entry."""
    async_add_entities(
        cls(coordinator)
        for coordinator in entry.runtime_data.coordinators
        for cls in (
            PentairSaltAddedButton,
            PentairRegenerateNowButton,
            PentairRegenerateScheduledButton,
        )
    )


class PentairBaseButton(PentairEntity, ButtonEntity):
    """Bazowa encja przycisku Pentair."""

    _entity_id_format = ENTITY_ID_FORMAT

    @property
    def available(self) -> bool:
        # Jak w aplikacji: akcje wyłączone podczas regeneracji i trybu urlopowego.
        if not super().available:
            return False
        return self._status_code not in (STATUS_REGENERATING, STATUS_HOLIDAY)


class PentairSaltAddedButton(PentairBaseButton):
    """Potwierdź dodanie soli (reset alarmu soli)."""

    _attr_translation_key = "salt_added"
    _unique_suffix = "salt_added"
    _attr_icon = "mdi:shaker-outline"

    async def async_press(self) -> None:
        await self.device.set_salt_added()
        await self.coordinator.async_refresh_after_action()


class PentairRegenerateNowButton(PentairBaseButton):
    """Uruchom regenerację teraz."""

    _attr_translation_key = "regenerate_now"
    _unique_suffix = "regenerate_now"
    _attr_icon = "mdi:refresh"

    async def async_press(self) -> None:
        await self.device.do_regeneration(REGEN_NOW)
        await self.coordinator.async_refresh_after_action()


class PentairRegenerateScheduledButton(PentairBaseButton):
    """Zaplanuj regenerację na zaplanowaną godzinę."""

    _attr_translation_key = "regenerate_scheduled"
    _unique_suffix = "regenerate_scheduled"
    _attr_icon = "mdi:clock-outline"

    async def async_press(self) -> None:
        await self.device.do_regeneration(REGEN_AT_SCHEDULED)
        await self.coordinator.async_refresh_after_action()
