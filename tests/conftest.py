"""Shared fixtures: a fake ConnectMySoftener account with mocked cloud calls."""

from __future__ import annotations

import copy
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.pentair_softener.api import PentairApi, PentairDevice
from custom_components.pentair_softener.const import CONF_EMAIL, CONF_PASSWORD, DOMAIN

ENTRY_ID = "entry123"

PROFILE = {"id": 111, "name": "Softener", "serial": "S12345678"}

DASHBOARD = {
    "status": {
        "code": 1,
        "title": "In service",
        "extra": "2216 L",
        "days_remaining": 5,
        "percentage": 80,
    },
    "meta": {"regen_time": "02:00 h", "units": 2},
    "warnings": [],
    "holiday_mode": 0,
}
INFO = {
    "total_volume": "12345 L",
    "nr_regenerations": 100,
    "last_regeneration": "2026-11-01 02:00",
    "serial": "S12345678",
    "software": "1.2",
}
SETTINGS = {
    "settings": {
        "install_hardness": "20",
        "hard_units": {"value": "°d", "list": ["°d", "°f", "PPM"]},
        "system_time": "11:16",
        "oxy_function": 1,
        "override_1": 7,
    },
    "notifications": {"salt_alarm": True, "maintenance": False},
}
FEATURES = {
    "recharge_daily": "available",
    "recharge_interval": "available",
    "recharge_interval_oxy": "unavailable",
    "salt_alarm": "available",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading custom_components in every test."""
    yield


@pytest.fixture(autouse=True)
def skip_frontend(hass):
    """The card needs the real frontend/http; tests only cover the integration."""
    hass.config.components.add("frontend")
    hass.config.components.add("http")
    with patch(
        "custom_components.pentair_softener._async_register_card",
        AsyncMock(return_value=None),
    ):
        yield


@pytest.fixture
def config_entry(hass) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        entry_id=ENTRY_ID,
        unique_id="user@example.com",
        title="Pentair softener (user@example.com)",
        data={CONF_EMAIL: "user@example.com", CONF_PASSWORD: "secret"},
    )
    entry.add_to_hass(hass)
    return entry


@pytest.fixture
def profiles() -> list[dict[str, Any]]:
    return [copy.deepcopy(PROFILE)]


@pytest.fixture
def mock_cloud(profiles):
    """Patch every cloud call; returns the mocks so tests can inspect calls."""
    mocks = {
        "get_devices": AsyncMock(return_value=profiles),
        "login": AsyncMock(return_value=None),
        "get_dashboard": AsyncMock(return_value=copy.deepcopy(DASHBOARD)),
        "get_flow": AsyncMock(return_value={"flow": 0}),
        "get_info": AsyncMock(return_value=copy.deepcopy(INFO)),
        "get_settings": AsyncMock(return_value=copy.deepcopy(SETTINGS)),
        "get_features": AsyncMock(return_value=copy.deepcopy(FEATURES)),
        "get_regenerations": AsyncMock(return_value=[]),
        "get_pending": AsyncMock(return_value=[]),
        "save_settings": AsyncMock(return_value={}),
    }
    with (
        patch.object(PentairApi, "get_devices", mocks["get_devices"]),
        patch.object(PentairApi, "login", mocks["login"]),
        patch.object(PentairDevice, "get_dashboard", mocks["get_dashboard"]),
        patch.object(PentairDevice, "get_flow", mocks["get_flow"]),
        patch.object(PentairDevice, "get_info", mocks["get_info"]),
        patch.object(PentairDevice, "get_settings", mocks["get_settings"]),
        patch.object(PentairDevice, "get_features", mocks["get_features"]),
        patch.object(PentairDevice, "get_regenerations", mocks["get_regenerations"]),
        patch.object(PentairDevice, "get_pending", mocks["get_pending"]),
        patch.object(PentairDevice, "save_settings", mocks["save_settings"]),
    ):
        yield mocks
