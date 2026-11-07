from __future__ import annotations

from typing import Any

from homeassistant.components.switch import ENTITY_ID_FORMAT, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import PentairEntity, feature_supported


def _to_bool(value: Any) -> bool | None:
    """API zwraca te przełączniki jako bool, 0/1 albo '0'/'1'."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str) and value.strip() != "":
        return value.strip().lower() not in ("0", "false", "off", "no")
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Pentair switches (ustawienia z ekranu Ustawienia w aplikacji)."""
    entities: list[SwitchEntity] = []
    for coordinator in entry.runtime_data.coordinators:
        payload = (coordinator.data or {}).get("settings") or {}
        settings = payload.get("settings") or {}
        notifications = payload.get("notifications")

        if feature_supported(coordinator, "recharge_daily", "oxy_function" in settings):
            entities.append(PentairDailyRechargeSwitch(coordinator))
        if isinstance(notifications, dict):
            # Aplikacja pokazuje alarm soli zależnie od flagi, a konserwację zawsze.
            if feature_supported(
                coordinator, "salt_alarm", "salt_alarm" in notifications
            ):
                entities.append(PentairSaltAlarmNotificationSwitch(coordinator))
            if "maintenance" in notifications:
                entities.append(PentairMaintenanceNotificationSwitch(coordinator))
    async_add_entities(entities)


class PentairBaseSwitch(PentairEntity, SwitchEntity):
    """Bazowa encja przełącznika Pentair."""

    _entity_id_format = ENTITY_ID_FORMAT
    _attr_entity_category = EntityCategory.CONFIG


class PentairDailyRechargeSwitch(PentairBaseSwitch):
    """Codzienne doładowanie (oxy_function) – 'Uzupełnij codziennie' w aplikacji."""

    _attr_translation_key = "daily_recharge"
    _unique_suffix = "daily_recharge"
    _attr_icon = "mdi:calendar-sync"

    @property
    def is_on(self) -> bool | None:
        return _to_bool(self._settings.get("oxy_function"))

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.device.set_daily_recharge(True)
        await self.coordinator.async_refresh_after_action()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.device.set_daily_recharge(False)
        await self.coordinator.async_refresh_after_action()


class PentairNotificationSwitch(PentairBaseSwitch):
    """Powiadomienie z chmury Pentair (e-mail/push z aplikacji).

    API przyjmuje oba powiadomienia naraz, więc wysyłamy też bieżącą wartość
    drugiego – tak jak aplikacja."""

    _attr_icon = "mdi:bell-outline"
    key: str

    def _current(self, key: str) -> bool:
        return bool(_to_bool(self._notifications.get(key)))

    @property
    def is_on(self) -> bool | None:
        return _to_bool(self._notifications.get(self.key))

    async def _set(self, value: bool) -> None:
        values = {
            "salt_alarm": self._current("salt_alarm"),
            "maintenance": self._current("maintenance"),
        }
        values[self.key] = value
        await self.device.set_notifications(**values)
        await self.coordinator.async_refresh_after_action()

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._set(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._set(False)


class PentairSaltAlarmNotificationSwitch(PentairNotificationSwitch):
    """Powiadomienie o niskim poziomie soli."""

    _attr_translation_key = "salt_alarm_notification"
    _unique_suffix = "salt_alarm_notification"
    key = "salt_alarm"


class PentairMaintenanceNotificationSwitch(PentairNotificationSwitch):
    """Powiadomienie o wymaganej konserwacji."""

    _attr_translation_key = "maintenance_notification"
    _unique_suffix = "maintenance_notification"
    _attr_icon = "mdi:wrench-clock"
    key = "maintenance"
