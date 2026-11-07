from __future__ import annotations

import asyncio
from datetime import datetime
import logging
from typing import Any, Awaitable, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import PentairApiError, PentairAuthError, PentairDevice
from .const import (
    CONF_ENABLE_GRAPHS,
    DEFAULT_ENABLE_GRAPHS,
    GRAPH_INTERVALS,
    GRAPH_UPDATE_INTERVAL,
    SLOW_UPDATE_INTERVAL,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class PentairCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordynator jednego zmiękczacza z odświeżaniem warstwowym.

    Co UPDATE_INTERVAL pobierane są tylko dane "na żywo" (dashboard, flow).
    Dane zmieniające się rzadko (info, settings, regenerations, pending, features)
    co SLOW_UPDATE_INTERVAL, wykresy zużycia co GRAPH_UPDATE_INTERVAL.
    Po akcji użytkownika lub zmianie statusu urządzenia wszystko jest pobierane
    od razu, żeby encje nie pokazywały nieaktualnych wartości."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        device: PentairDevice,
        unique_prefix: str,
        fallback_identifier: str,
    ) -> None:
        kwargs: dict[str, Any] = {
            "name": f"Pentair softener {device.device_id}",
            "update_interval": UPDATE_INTERVAL,
        }
        try:
            super().__init__(hass, _LOGGER, config_entry=entry, **kwargs)
        except TypeError:  # Home Assistant before 2024.11 (no config_entry argument)
            super().__init__(hass, _LOGGER, **kwargs)
        self.entry = entry
        self.device = device
        # Prefiks unique_id encji i zapasowy identyfikator urządzenia w rejestrze HA.
        self.unique_prefix = unique_prefix
        self._fallback_identifier = fallback_identifier

        self._force_slow = True
        self._next_slow: datetime | None = None
        self._next_graphs: datetime | None = None
        self._last_status: Any = None

    @property
    def serial(self) -> str | None:
        """Numer seryjny z profilu urządzenia albo z /info."""
        info = (self.data or {}).get("info") or {}
        value = self.device.profile.get("serial") or info.get("serial")
        return str(value) if value not in (None, "") else None

    @property
    def device_identifier(self) -> str:
        """Identyfikator urządzenia w rejestrze HA (numer seryjny, jak dotąd)."""
        return self.serial or self._fallback_identifier

    async def async_refresh_after_action(self) -> None:
        """Odśwież wszystko (również dane wolne) po akcji użytkownika."""
        self._force_slow = True
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        previous: dict[str, Any] = self.data or {}
        now = dt_util.utcnow()

        dashboard_result, flow = await asyncio.gather(
            self.device.get_dashboard(),
            self._safe(self.device.get_flow, "flow", previous.get("flow")),
            return_exceptions=True,
        )
        if isinstance(dashboard_result, PentairAuthError):
            raise ConfigEntryAuthFailed(str(dashboard_result)) from dashboard_result
        if isinstance(dashboard_result, PentairApiError):
            raise UpdateFailed(
                f"Error communicating with Pentair API: {dashboard_result}"
            ) from dashboard_result
        if isinstance(dashboard_result, BaseException):
            raise dashboard_result
        if isinstance(flow, BaseException):
            raise flow
        dashboard: dict[str, Any] = (
            dashboard_result if isinstance(dashboard_result, dict) else {}
        )

        # Zmiana statusu (np. koniec regeneracji) zmienia też info i historię.
        status = (dashboard.get("status") or {}).get("code")
        if self._last_status is not None and status != self._last_status:
            self._force_slow = True
        self._last_status = status

        data: dict[str, Any] = {
            **previous,
            "dashboard": dashboard,
            "flow": flow,
        }

        if self._force_slow or self._next_slow is None or now >= self._next_slow:
            info, settings, regenerations, pending, features = await asyncio.gather(
                self._safe(self.device.get_info, "info", previous.get("info")),
                self._safe(
                    self.device.get_settings, "settings", previous.get("settings")
                ),
                self._safe(
                    self.device.get_regenerations,
                    "regenerations",
                    previous.get("regenerations"),
                    empty=[],
                ),
                self._safe(
                    self.device.get_pending,
                    "pending",
                    previous.get("pending"),
                    empty=[],
                ),
                self._safe(
                    self.device.get_features, "features", previous.get("features")
                ),
            )
            data.update(
                info=info,
                settings=settings,
                regenerations=regenerations,
                pending=pending,
                features=features,
            )
            self._force_slow = False
            self._next_slow = now + SLOW_UPDATE_INTERVAL

        if self.entry.options.get(CONF_ENABLE_GRAPHS, DEFAULT_ENABLE_GRAPHS):
            if self._next_graphs is None or now >= self._next_graphs:
                data["usage"] = await self._fetch_usage(previous.get("usage") or {})
                self._next_graphs = now + GRAPH_UPDATE_INTERVAL
        else:
            data.pop("usage", None)

        return data

    async def _fetch_usage(
        self, previous: dict[str, float | None]
    ) -> dict[str, float | None]:
        """Pobierz historię zużycia wody z /graphs (day/week/month/year)."""
        tz = self.hass.config.time_zone or "UTC"
        when = dt_util.now()

        async def one(interval: str) -> float | None:
            try:
                return await self.device.get_usage(interval, when, tz)
            except PentairApiError as err:
                _LOGGER.debug("Pentair: usage %s unavailable: %s", interval, err)
                return previous.get(interval)

        values = await asyncio.gather(*(one(i) for i in GRAPH_INTERVALS))
        return dict(zip(GRAPH_INTERVALS, values))

    async def _safe(
        self,
        coro_func: Callable[[], Awaitable[Any]],
        name: str,
        previous: Any,
        empty: Any = None,
    ) -> Any:
        """Wywołaj opcjonalny endpoint.

        Przy błędzie zostaw poprzednią wartość (encja nie traci stanu przez
        chwilowy błąd chmury); gdy jej nie ma – pustą."""
        try:
            return await coro_func()
        except PentairApiError as err:
            _LOGGER.debug("Pentair: %s unavailable: %s", name, err)
            if previous is not None:
                return previous
            return {} if empty is None else empty
