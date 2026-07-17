from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import asyncio
import logging

from aiohttp import ClientSession, ClientError

from .const import API_BASE_URL, APP_VERSION, DEFAULT_LANGUAGE

_LOGGER = logging.getLogger(__name__)


@dataclass
class PentairAuthHeaders:
    """Nagłówki auth zwracane przez devise_token_auth (Rails)."""

    access_token: str
    client: str
    expiry: str
    uid: str
    token_type: str = "Bearer"

    @classmethod
    def from_response_headers(cls, headers: Dict[str, str]) -> "PentairAuthHeaders":
        """Utwórz obiekt z nagłówków odpowiedzi /auth/sign_in."""
        return cls(
            access_token=headers.get("Access-Token", ""),
            client=headers.get("Client", ""),
            expiry=headers.get("Expiry", ""),
            uid=headers.get("Uid", ""),
            token_type=headers.get("Token-Type", "Bearer"),
        )

    def to_request_headers(self) -> Dict[str, str]:
        """Zamień na nagłówki żądania (małe litery jak w appce)."""
        return {
            "access-token": self.access_token,
            "client": self.client,
            "expiry": self.expiry,
            "uid": self.uid,
            "token-type": self.token_type,
        }


class PentairApiError(Exception):
    """Generic error from Pentair API."""


class PentairAuthError(PentairApiError):
    """Authentication failed or expired."""


class PentairApi:
    """Klient API ConnectMySoftener / Pentair (erieapp v1)."""

    def __init__(
        self,
        session: ClientSession,
        email: str,
        password: str,
        language: str = DEFAULT_LANGUAGE,
        app_version: str = APP_VERSION,
    ) -> None:
        self._session = session
        self._email = email
        self._password = password
        self._language = language
        self._app_version = app_version
        self._auth: Optional[PentairAuthHeaders] = None
        self._device_id: Optional[str] = None
        self._profile: Dict[str, Any] = {}

    @property
    def device_id(self) -> Optional[str]:
        return self._device_id

    @property
    def profile(self) -> Dict[str, Any]:
        """Profil urządzenia (id, name, serial, ...) z /water_softeners."""
        return self._profile

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: Dict[str, Any] | None = None,
        auth_required: bool = True,
        _retry: bool = True,
    ) -> Any:
        """Wspólna metoda HTTP z obsługą auth, błędów i pojedynczego retry na 401."""

        url = f"{API_BASE_URL}{path}"

        headers: Dict[str, str] = {
            "language": self._language,
            "app_version": self._app_version,
        }

        if auth_required:
            if not self._auth:
                await self.login()
            if not self._auth:
                raise PentairAuthError("No auth after login")
            headers.update(self._auth.to_request_headers())

        try:
            async with self._session.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=15,
            ) as resp:
                if resp.status == 401:
                    _LOGGER.warning("Pentair: 401 Unauthorized on %s %s", method, path)
                    if auth_required and _retry:
                        # token wygasł – jednorazowa próba ponownego logowania
                        self._auth = None
                        await self.login()
                        return await self._request(
                            method,
                            path,
                            json=json,
                            params=params,
                            auth_required=True,
                            _retry=False,
                        )
                    raise PentairAuthError("Unauthorized (401)")

                if resp.status == 426:
                    text = await resp.text()
                    _LOGGER.error("Pentair: update required (426): %s", text)
                    raise PentairApiError("API requires app update (426)")

                if resp.status >= 400:
                    text = await resp.text()
                    raise PentairApiError(
                        f"HTTP {resp.status} for {method} {path}: {text}"
                    )

                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()

        except ClientError as err:
            raise PentairApiError(f"HTTP error: {err}") from err
        except asyncio.TimeoutError as err:
            raise PentairApiError("Request timeout") from err

    async def login(self) -> None:
        """Zaloguj użytkownika (POST /auth/sign_in) i zapisz nagłówki tokenu."""
        payload = {"email": self._email, "password": self._password}

        url = f"{API_BASE_URL}/auth/sign_in"
        headers = {"language": self._language}

        try:
            async with self._session.post(
                url, json=payload, headers=headers, timeout=15
            ) as resp:
                if resp.status >= 400:
                    text = await resp.text()
                    raise PentairAuthError(f"Login failed ({resp.status}): {text}")

                auth_headers = PentairAuthHeaders.from_response_headers(
                    dict(resp.headers)
                )
                if not auth_headers.access_token:
                    raise PentairAuthError("Missing auth headers in login response")

                self._auth = auth_headers
                _LOGGER.info("Pentair: login successful for %s", self._email)

        except ClientError as err:
            raise PentairAuthError(f"Login HTTP error: {err}") from err

        # Po zalogowaniu ustal device_id z listy zmiękczaczy.
        await self.ensure_device_id()

    async def ensure_device_id(self) -> None:
        """Ustal device_id na podstawie /water_softeners (id = profile.id)."""
        if self._device_id:
            return

        devices = await self._request("GET", "/water_softeners", auth_required=True)
        if not isinstance(devices, list) or not devices:
            raise PentairApiError("No water softeners found for account")

        first = devices[0]
        profile = first.get("profile") if isinstance(first, dict) else None
        if not isinstance(profile, dict) or "id" not in profile:
            raise PentairApiError("Unexpected devices payload, missing profile.id")

        self._profile = profile
        self._device_id = str(profile["id"])
        _LOGGER.debug(
            "Pentair: using device_id=%s (%s)",
            self._device_id,
            profile.get("name"),
        )

    async def get_dashboard(self) -> dict[str, Any]:
        """Dane dashboardu: status, meta (jednostki), warnings, holiday_mode."""
        await self.ensure_device_id()
        return await self._request(
            "GET", f"/water_softeners/{self._device_id}/dashboard"
        )

    async def get_flow(self) -> dict[str, Any]:
        """Chwilowy przepływ: {'flow': <L/min lub GPM>}."""
        await self.ensure_device_id()
        return await self._request(
            "GET", f"/water_softeners/{self._device_id}/flow"
        )

    async def get_info(self) -> dict[str, Any]:
        """Informacje: total_volume, nr_regenerations, last_regeneration, software..."""
        await self.ensure_device_id()
        return await self._request(
            "GET", f"/water_softeners/{self._device_id}/info"
        )

    async def get_settings(self) -> dict[str, Any]:
        """Ustawienia: settings{install_hardness, hard_units, language, ...}, notifications."""
        await self.ensure_device_id()
        return await self._request(
            "GET", f"/water_softeners/{self._device_id}/settings"
        )

    async def get_regenerations(self) -> list[dict[str, Any]]:
        """Historia regeneracji: [{datetime, salt_used (gramy), percentage}, ...].

        Zwracana lista jest posortowana malejąco po dacie, jak w aplikacji."""
        await self.ensure_device_id()
        result = await self._request(
            "GET", f"/water_softeners/{self._device_id}/regenerations"
        )
        if not isinstance(result, list):
            return []
        items = [item for item in result if isinstance(item, dict)]
        items.sort(key=lambda item: str(item.get("datetime") or ""), reverse=True)
        return items

    async def get_pending(self) -> list[Any]:
        """Zmiany wysłane do urządzenia, które jeszcze nie zostały zastosowane.

        Aplikacja traktuje niepustą listę jako 'są oczekujące zmiany'."""
        await self.ensure_device_id()
        result = await self._request(
            "GET", f"/water_softeners/{self._device_id}/pending"
        )
        return result if isinstance(result, list) else []

    async def save_settings(self, data: Dict[str, Any]) -> Any:
        """Zapis ustawień/akcji przez PUT /water_softeners/{id}/stats."""
        await self.ensure_device_id()
        return await self._request(
            "PUT", f"/water_softeners/{self._device_id}/stats", json=data
        )

    async def set_salt_added(self) -> Any:
        """Potwierdź dodanie soli (reset alarmu)."""
        return await self.save_settings({"salt_added": True})

    async def do_regeneration(self, regen_type: int) -> Any:
        """Uruchom regenerację: 1 = teraz, 2 = o zaplanowanej godzinie."""
        return await self.save_settings({"regenerate": regen_type})

    async def set_holiday_mode(self, days: int) -> Any:
        """Ustaw tryb urlopowy: 0 = wył., N = liczba dni (1-40)."""
        return await self.save_settings({"holiday_mode": days})

    async def set_hardness(self, value: int) -> Any:
        """Ustaw twardość wody na wejściu (jednostka wg hard_units)."""
        return await self.save_settings({"install_hardness": value})

    async def set_system_time(self, value: str) -> Any:
        """Ustaw zegar urządzenia. Aplikacja wysyła czysty 'HH:MM' (24h)."""
        return await self.save_settings({"system_time": value})

    async def get_graph(
        self, interval: str, when: datetime, timezone: str
    ) -> dict[str, Any]:
        """Dane wykresu zużycia wody dla interwału day/week/month/year.

        Odwzorowanie zapytań aplikacji: GET /water_softeners/{id}/graphs/{interval}
        z parametrami year/month/day/week + timezone."""
        await self.ensure_device_id()
        il = interval.lower()
        params: Dict[str, str] = {"year": str(when.year), "timezone": timezone}
        if il == "day":
            params["month"] = str(when.month)
            params["day"] = str(when.day)
        elif il == "week":
            params["week"] = str(when.isocalendar()[1])
        elif il == "month":
            params["month"] = str(when.month)
        # "year" -> tylko parametr year
        return await self._request(
            "GET", f"/water_softeners/{self._device_id}/graphs/{il}", params=params
        )

    async def get_usage(
        self, interval: str, when: datetime, timezone: str
    ) -> float | None:
        """Suma zużycia wody w danym okresie (suma 'y' z wykresu)."""
        data = await self.get_graph(interval, when, timezone)
        graph = data.get("graph") if isinstance(data, dict) else None
        if not isinstance(graph, list):
            return None
        total = 0.0
        found = False
        for point in graph:
            y = point.get("y") if isinstance(point, dict) else None
            if isinstance(y, (int, float)):
                total += y
                found = True
        return round(total, 2) if found else None
