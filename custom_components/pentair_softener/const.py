from __future__ import annotations

from datetime import timedelta

DOMAIN = "pentair_softener"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Opcja (options flow): pobieranie historii zużycia wody z /graphs
CONF_ENABLE_GRAPHS = "enable_graphs"
DEFAULT_ENABLE_GRAPHS = False
GRAPH_INTERVALS = ["day", "week", "month", "year"]

# Urządzenie, które było obsługiwane przed dodaniem obsługi wielu zmiękczaczy.
# Jego encje zachowują dotychczasowe unique_id ({entry_id}_{klucz}); kolejne
# urządzenia na koncie dostają {entry_id}_{device_id}_{klucz}.
CONF_PRIMARY_DEVICE_ID = "primary_device_id"

API_BASE_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"
DEFAULT_LANGUAGE = "en"
REQUEST_TIMEOUT = 15

# Wysyłamy wysoką wersję, żeby backend nie zwrócił 426 "update required".
# Prawdziwa aplikacja wysyła swój numer wersji w nagłówku app_version.
APP_VERSION = "9.9.9"

# Odświeżanie warstwowe – ogranicza liczbę zapytań do chmury.
# Co UPDATE_INTERVAL: dashboard + flow (dane "na żywo").
# Co SLOW_UPDATE_INTERVAL: info, settings, regenerations, pending, features.
# Co GRAPH_UPDATE_INTERVAL: wykresy zużycia (tylko gdy włączone w opcjach).
# Po każdej akcji (przycisk, zmiana ustawienia) i po zmianie statusu urządzenia
# dane wolne są pobierane od razu.
UPDATE_INTERVAL = timedelta(seconds=90)
SLOW_UPDATE_INTERVAL = timedelta(minutes=10)
GRAPH_UPDATE_INTERVAL = timedelta(minutes=30)

# meta.units w odpowiedzi /dashboard: 1 = US (gal), 2 = metryczne (litry)
UNITS_US = 1
UNITS_METRIC = 2

# status.code z /dashboard
STATUS_CODES = {
    0: "offline",
    1: "in_service",
    2: "regenerating",
    3: "holiday",
    4: "standby",
}
STATUS_REGENERATING = 2
STATUS_HOLIDAY = 3

# warning.type z dashboard.warnings
WARNING_TYPE_SALT = 1

# regenerate: typ operacji wysyłany do PUT /stats
REGEN_NOW = 1
REGEN_AT_SCHEDULED = 2

# Tryb urlopowy: dozwolony zakres liczby dni (0 = wyłączony)
HOLIDAY_MODE_MAX_DAYS = 40

# Ile wpisów historii regeneracji trzymać w atrybutach sensora
REGEN_HISTORY_LIMIT = 20

# Twardość wody na wejściu – zakres jak w aplikacji (input min/max)
HARDNESS_MIN = 1
HARDNESS_MAX = 99

# Interwał wymuszonej regeneracji / doładowania (override_1, override_oxy), w dniach.
# Aplikacja nie ogranicza pola; 0 = wyłączone.
OVERRIDE_MIN = 0
OVERRIDE_MAX = 99

# Flagi funkcji z GET /water_softeners/{id}/features ({"feature": {...}}).
# Aplikacja pokazuje dane ustawienie tylko gdy flaga == "available".
FEATURE_AVAILABLE = "available"

PLATFORMS: list[str] = ["sensor", "binary_sensor", "button", "number", "switch", "time"]
