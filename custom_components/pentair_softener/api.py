from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

import asyncio
import logging

from aiohttp import ClientSession, ClientError

from .const import API_BASE_URL, APP_VERSION, DEFAULT_LANGUAGE, REQUEST_TIMEOUT

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
    """Generic error from Pentair API (network, server, unexpected payload)."""


class PentairAuthError(PentairApiError):
    """Credentials rejected – the user has to sign in again."""


class PentairApi:
    """Klient konta ConnectMySoftener / Pentair (erieapp v1).

    Odpowiada za logowanie i wspólne zapytania HTTP. Operacje na konkretnym
    zmiękczaczu udostępnia PentairDevice (jeden obiekt na urządzenie)."""

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
        # Zapytania idą równolegle – blokada pilnuje, żeby po wygaśnięciu tokenu
        # logować się tylko raz, a nie osobno dla każdego zapytania.
        self._login_lock = asyncio.Lock()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: Any | None = None,
        params: Dict[str, Any] | None = None,
        _retry: bool = True,
    ) -> Any:
        """Wspólna metoda HTTP z obsługą auth, błędów i pojedynczego retry na 401."""

        url = f"{API_BASE_URL}{path}"

        auth = self._auth
        if auth is None:
            await self.login()
            auth = self._auth
        if auth is None:
            raise PentairAuthError("No auth after login")

        headers: Dict[str, str] = {
            "language": self._language,
            "app_version": self._app_version,
            **auth.to_request_headers(),
        }

        try:
            async with self._session.request(
                method,
                url,
                json=json,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            ) as resp:
                if resp.status == 401:
                    _LOGGER.debug("Pentair: 401 Unauthorized on %s %s", method, path)
                    if _retry:
                        # Token wygasł – jednorazowo logujemy się ponownie (chyba
                        # że inne zapytanie zdążyło już to zrobić).
                        await self.login(stale=auth)
                        return await self._request(
                            method, path, json=json, params=params, _retry=False
                        )
                    raise PentairAuthError("Unauthorized (401)")

                if resp.status == 426:
                    text = await resp.text()
                    _LOGGER.error("Pentair: update required (426): %s", text)
                    raise PentairApiError("API requires app update (426)")

                if resp.status >= 400:
                    text = await resp.text()
                    raise PentairApiError(
                        f"HTTP {resp.status} for {method} {path}: {text[:200]}"
                    )

                if resp.content_type == "application/json":
                    return await resp.json()
                return await resp.text()

        except ClientError as err:
            raise PentairApiError(f"HTTP error: {err}") from err
        except asyncio.TimeoutError as err:
            raise PentairApiError("Request timeout") from err

    async def login(self, stale: PentairAuthHeaders | None = None) -> None:
        """Zaloguj użytkownika (POST /auth/sign_in) i zapisz nagłówki tokenu.

        stale: token, który okazał się nieważny. Jeśli w międzyczasie inne
        zapytanie już się zalogowało (token się zmienił), nie logujemy się drugi raz.

        Złe dane logowania -> PentairAuthError (HA poprosi o ponowne logowanie).
        Problemy z siecią / serwerem -> PentairApiError (HA spróbuje później)."""
        async with self._login_lock:
            if stale is not None and self._auth is not None and self._auth is not stale:
                return
            self._auth = None

            payload = {"email": self._email, "password": self._password}
            url = f"{API_BASE_URL}/auth/sign_in"
            headers = {"language": self._language}

            try:
                async with self._session.post(
                    url, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
                ) as resp:
                    if resp.status in (401, 403, 422):
                        raise PentairAuthError(f"Login rejected ({resp.status})")
                    if resp.status >= 400:
                        text = await resp.text()
                        raise PentairApiError(
                            f"Login failed ({resp.status}): {text[:200]}"
                        )

                    auth_headers = PentairAuthHeaders.from_response_headers(
                        dict(resp.headers)
                    )
                    if not auth_headers.access_token:
                        raise PentairApiError("Missing auth headers in login response")

                    self._auth = auth_headers
                    _LOGGER.debug("Pentair: login successful")

            except ClientError as err:
                raise PentairApiError(f"Login HTTP error: {err}") from err
            except asyncio.TimeoutError as err:
                raise PentairApiError("Login timeout") from err

    async def get_devices(self) -> list[dict[str, Any]]:
        """Lista zmiękczaczy na koncie: profile z /water_softeners (id = profile.id)."""
        devices = await self._request("GET", "/water_softeners")
        if not isinstance(devices, list):
            raise PentairApiError("Unexpected devices payload")

        profiles: list[dict[str, Any]] = []
        for item in devices:
            profile = item.get("profile") if isinstance(item, dict) else None
            if isinstance(profile, dict) and profile.get("id") is not None:
                profiles.append(profile)
        if not profiles:
            raise PentairApiError("No water softeners found for account")
        return profiles


class PentairDevice:
    """Operacje na jednym zmiękczaczu (device_id = profile.id)."""

    def __init__(self, api: PentairApi, profile: dict[str, Any]) -> None:
        self._api = api
        self._profile = profile
        self._device_id = str(profile["id"])

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def profile(self) -> Dict[str, Any]:
        """Profil urządzenia (id, name, serial, ...) z /water_softeners."""
        return self._profile

    def _path(self, suffix: str) -> str:
        return f"/water_softeners/{self._device_id}/{suffix}"

    async def get_dashboard(self) -> dict[str, Any]:
        """Dane dashboardu: status, meta (jednostki), warnings, holiday_mode."""
        return await self._api._request("GET", self._path("dashboard"))

    async def get_flow(self) -> dict[str, Any]:
        """Chwilowy przepływ: {'flow': <L/min lub GPM>}."""
        return await self._api._request("GET", self._path("flow"))

    async def get_info(self) -> dict[str, Any]:
        """Informacje: total_volume, nr_regenerations, last_regeneration, software..."""
        return await self._api._request("GET", self._path("info"))

    async def get_settings(self) -> dict[str, Any]:
        """Ustawienia: settings{install_hardness, hard_units, ...}, notifications{...}."""
        return await self._api._request("GET", self._path("settings"))

    async def get_features(self) -> dict[str, Any]:
        """Flagi funkcji urządzenia: {'recharge_daily': 'available', ...}.

        Aplikacja pokazuje dane ustawienie tylko, gdy flaga == 'available'."""
        result = await self._api._request("GET", self._path("features"))
        features = result.get("feature") if isinstance(result, dict) else None
        return features if isinstance(features, dict) else {}

    async def get_regenerations(self) -> list[dict[str, Any]]:
        """Historia regeneracji: [{datetime, salt_used (gramy), percentage}, ...].

        Zwracana lista jest posortowana malejąco po dacie, jak w aplikacji."""
        result = await self._api._request("GET", self._path("regenerations"))
        if not isinstance(result, list):
            return []
        items = [item for item in result if isinstance(item, dict)]
        items.sort(key=lambda item: str(item.get("datetime") or ""), reverse=True)
        return items

    async def get_pending(self) -> list[Any]:
        """Zmiany wysłane do urządzenia, które jeszcze nie zostały zastosowane.

        Aplikacja traktuje niepustą listę jako 'są oczekujące zmiany'."""
        result = await self._api._request("GET", self._path("pending"))
        return result if isinstance(result, list) else []

    async def save_settings(self, data: Dict[str, Any]) -> Any:
        """Zapis ustawień/akcji przez PUT /water_softeners/{id}/stats."""
        return await self._api._request("PUT", self._path("stats"), json=data)

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

    async def set_daily_recharge(self, enabled: bool) -> Any:
        """Codzienne doładowanie (oxy_function). Aplikacja wysyła 1 / 0."""
        return await self.save_settings({"oxy_function": 1 if enabled else 0})

    async def set_override(self, key: str, value: int) -> Any:
        """Interwał wymuszonej regeneracji: key = 'override_1' lub 'override_oxy'."""
        if key not in ("override_1", "override_oxy"):
            raise ValueError(f"Unsupported override key: {key}")
        return await self.save_settings({key: value})

    async def set_notifications(self, salt_alarm: bool, maintenance: bool) -> Any:
        """Powiadomienia e-mail/push. Aplikacja zawsze wysyła oba pola naraz."""
        return await self.save_settings(
            {"salt_alarm": salt_alarm, "maintenance": maintenance}
        )

    async def get_graph(
        self, interval: str, when: datetime, timezone: str
    ) -> dict[str, Any]:
        """Dane wykresu zużycia wody dla interwału day/week/month/year.

        Odwzorowanie zapytań aplikacji: GET /water_softeners/{id}/graphs/{interval}
        z parametrami year/month/day/week + timezone."""
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
        return await self._api._request(
            "GET", self._path(f"graphs/{il}"), params=params
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
