from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_ENABLE_GRAPHS,
    DEFAULT_ENABLE_GRAPHS,
    GRAPH_INTERVALS,
    PLATFORMS,
)
from .api import PentairApi, PentairApiError, PentairAuthError

_LOGGER = logging.getLogger(__name__)


class PentairCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Koordynator pobierający dane ze zmiękczacza Pentair."""

    def __init__(
        self, hass: HomeAssistant, api: PentairApi, entry: ConfigEntry
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Pentair softener coordinator",
            update_interval=timedelta(seconds=90),
        )
        self.api = api
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        """Pobierz najnowsze dane z API.

        Krytyczny jest tylko dashboard (potrzebny m.in. do device_id). Pozostałe
        endpointy (flow/info/settings/graphs) są opcjonalne — ich brak nie może
        blokować utworzenia urządzenia ani całego odświeżania."""
        try:
            dashboard = await self.api.get_dashboard()
        except (PentairApiError, PentairAuthError) as err:
            raise UpdateFailed(f"Error communicating with Pentair API: {err}") from err

        data: dict[str, Any] = {
            "dashboard": dashboard,
            "flow": await self._safe(self.api.get_flow, "flow"),
            "info": await self._safe(self.api.get_info, "info"),
            "settings": await self._safe(self.api.get_settings, "settings"),
            "regenerations": await self._safe(
                self.api.get_regenerations, "regenerations", default=[]
            ),
            "pending": await self._safe(self.api.get_pending, "pending", default=[]),
        }

        if self.entry.options.get(CONF_ENABLE_GRAPHS, DEFAULT_ENABLE_GRAPHS):
            data["usage"] = await self._fetch_usage()

        return data

    async def _fetch_usage(self) -> dict[str, float | None]:
        """Pobierz historię zużycia wody z /graphs (day/week/month/year)."""
        tz = self.hass.config.time_zone or "UTC"
        now = dt_util.now()
        usage: dict[str, float | None] = {}
        for interval in GRAPH_INTERVALS:
            try:
                usage[interval] = await self.api.get_usage(interval, now, tz)
            except (PentairApiError, PentairAuthError) as err:
                _LOGGER.debug("Pentair: usage %s unavailable: %s", interval, err)
                usage[interval] = None
        return usage

    async def _safe(self, coro_func, name: str, default: Any = None) -> Any:
        """Wywołaj opcjonalny endpoint; przy błędzie zaloguj i zwróć wartość domyślną."""
        try:
            return await coro_func()
        except (PentairApiError, PentairAuthError) as err:
            _LOGGER.debug("Pentair: %s unavailable: %s", name, err)
            return {} if default is None else default


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Pentair softener from a config entry."""
    session = async_get_clientsession(hass)

    email: str = entry.data[CONF_EMAIL]
    password: str = entry.data[CONF_PASSWORD]

    api = PentairApi(session, email=email, password=password)

    coordinator = PentairCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "api": api,
        "coordinator": coordinator,
    }

    # Przeładuj wpis po zmianie opcji (np. włączenie historii zużycia).
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
