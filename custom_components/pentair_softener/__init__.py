from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path

from homeassistant.components import frontend
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_integration

from .api import PentairApi, PentairApiError, PentairAuthError, PentairDevice
from .const import (
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_PRIMARY_DEVICE_ID,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import PentairCoordinator

_LOGGER = logging.getLogger(__name__)

# Dashboard card served by the integration itself, so `type: custom:pentair-softener-card`
# works without adding a Lovelace resource by hand. A small loader is registered as an
# extra JS module; it imports the card bundle unless the user installed a newer copy
# as a Lovelace resource.
CARD_URL = f"/{DOMAIN}/pentair-softener-card.js"
CARD_FILE = Path(__file__).parent / "frontend" / "pentair-softener-card.js"
LOADER_URL = f"/{DOMAIN}/pentair-softener-loader.js"
LOADER_FILE = Path(__file__).parent / "frontend" / "pentair-softener-loader.js"


@dataclass
class PentairRuntimeData:
    """Dane wpisu konfiguracji: klient konta i koordynator na każde urządzenie."""

    api: PentairApi
    coordinators: list[PentairCoordinator]


PentairConfigEntry = ConfigEntry  # ConfigEntry[PentairRuntimeData] w nowszych HA


async def _async_register_card(hass: HomeAssistant, version: str | None) -> None:
    """Serve the card bundle and loader once per Home Assistant run."""
    if (
        hass.data.get(f"{DOMAIN}_card")
        or not CARD_FILE.is_file()
        or not LOADER_FILE.is_file()
    ):
        return
    hass.data[f"{DOMAIN}_card"] = True
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [
                StaticPathConfig(CARD_URL, str(CARD_FILE), False),
                StaticPathConfig(LOADER_URL, str(LOADER_FILE), False),
            ]
        )
    except ImportError:  # Home Assistant before 2024.7
        hass.http.register_static_path(CARD_URL, str(CARD_FILE), False)
        hass.http.register_static_path(LOADER_URL, str(LOADER_FILE), False)
    frontend.add_extra_js_url(hass, f"{LOADER_URL}?v={version or '0'}")


async def async_setup_entry(hass: HomeAssistant, entry: PentairConfigEntry) -> bool:
    """Set up Pentair softener(s) from a config entry."""
    session = async_get_clientsession(hass)
    api = PentairApi(
        session, email=entry.data[CONF_EMAIL], password=entry.data[CONF_PASSWORD]
    )

    try:
        profiles = await api.get_devices()
    except PentairAuthError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except PentairApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    # Urządzenie obsługiwane przed wersją z wieloma zmiękczaczami zachowuje
    # dotychczasowe unique_id encji i identyfikator w rejestrze urządzeń.
    primary_id = entry.data.get(CONF_PRIMARY_DEVICE_ID)
    if primary_id is None:
        primary_id = str(profiles[0]["id"])
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, CONF_PRIMARY_DEVICE_ID: primary_id}
        )

    coordinators: list[PentairCoordinator] = []
    for profile in profiles:
        device = PentairDevice(api, profile)
        if device.device_id == primary_id:
            prefix = entry.entry_id
        else:
            prefix = f"{entry.entry_id}_{device.device_id}"
        coordinators.append(
            PentairCoordinator(
                hass, entry, device, unique_prefix=prefix, fallback_identifier=prefix
            )
        )

    await asyncio.gather(
        *(c.async_config_entry_first_refresh() for c in coordinators)
    )

    integration = await async_get_integration(hass, DOMAIN)
    version = str(integration.version) if integration.version else None
    await _async_register_card(hass, version)

    entry.runtime_data = PentairRuntimeData(api=api, coordinators=coordinators)

    # Przeładuj wpis po zmianie opcji (np. włączenie historii zużycia).
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when its options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: PentairConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: PentairConfigEntry, device_entry: dr.DeviceEntry
) -> bool:
    """Pozwól usunąć urządzenie, którego nie ma już na koncie ConnectMySoftener."""
    runtime: PentairRuntimeData | None = getattr(entry, "runtime_data", None)
    if runtime is None:
        return True
    active = {(DOMAIN, c.device_identifier) for c in runtime.coordinators}
    return not (device_entry.identifiers & active)
