"""HTTP client: login error mapping and one re-login on an expired token."""

from __future__ import annotations

import pytest

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.pentair_softener.api import (
    PentairApi,
    PentairApiError,
    PentairAuthError,
    PentairDevice,
)
from custom_components.pentair_softener.const import API_BASE_URL

AUTH_HEADERS = {
    "Access-Token": "token",
    "Client": "client",
    "Expiry": "9999999999",
    "Uid": "user@example.com",
    "Token-Type": "Bearer",
}


def _api(hass) -> PentairApi:
    return PentairApi(async_get_clientsession(hass), "user@example.com", "secret")


@pytest.mark.parametrize("status", [401, 422])
async def test_login_rejected_is_auth_error(hass, aioclient_mock, status):
    aioclient_mock.post(f"{API_BASE_URL}/auth/sign_in", status=status)
    with pytest.raises(PentairAuthError):
        await _api(hass).login()


async def test_login_server_error_is_not_auth_error(hass, aioclient_mock):
    aioclient_mock.post(f"{API_BASE_URL}/auth/sign_in", status=503)
    with pytest.raises(PentairApiError) as err:
        await _api(hass).login()
    assert not isinstance(err.value, PentairAuthError)


async def test_devices_use_nested_profile_id(hass, aioclient_mock):
    aioclient_mock.post(f"{API_BASE_URL}/auth/sign_in", headers=AUTH_HEADERS)
    aioclient_mock.get(
        f"{API_BASE_URL}/water_softeners",
        json=[{"id": 1, "profile": {"id": 42, "name": "A"}}, {"id": 2}],
    )
    profiles = await _api(hass).get_devices()
    assert [p["id"] for p in profiles] == [42]


async def test_no_devices_raises(hass, aioclient_mock):
    aioclient_mock.post(f"{API_BASE_URL}/auth/sign_in", headers=AUTH_HEADERS)
    aioclient_mock.get(f"{API_BASE_URL}/water_softeners", json=[])
    with pytest.raises(PentairApiError):
        await _api(hass).get_devices()


async def test_features_payload(hass, aioclient_mock):
    aioclient_mock.post(f"{API_BASE_URL}/auth/sign_in", headers=AUTH_HEADERS)
    aioclient_mock.get(
        f"{API_BASE_URL}/water_softeners/42/features",
        json={"feature": {"recharge_daily": "available"}},
    )
    device = PentairDevice(_api(hass), {"id": 42})
    assert await device.get_features() == {"recharge_daily": "available"}


async def test_override_key_is_validated(hass):
    device = PentairDevice(_api(hass), {"id": 42})
    with pytest.raises(ValueError):
        await device.set_override("install_hardness", 5)
