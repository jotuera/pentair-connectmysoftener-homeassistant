from __future__ import annotations

DOMAIN = "pentair_softener"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

# Opcja (options flow): pobieranie historii zużycia wody z /graphs
CONF_ENABLE_GRAPHS = "enable_graphs"
DEFAULT_ENABLE_GRAPHS = False
GRAPH_INTERVALS = ["day", "week", "month", "year"]

API_BASE_URL = "https://connectmysoftenerapi.pentair.eu/api/erieapp/v1"
DEFAULT_LANGUAGE = "en"

# Wysyłamy wysoką wersję, żeby backend nie zwrócił 426 "update required".
# Prawdziwa aplikacja wysyła swój numer wersji w nagłówku app_version.
APP_VERSION = "9.9.9"

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

# warning.type z dashboard.warnings
WARNING_TYPE_SALT = 1

# regenerate: typ operacji wysyłany do PUT /stats
REGEN_NOW = 1
REGEN_AT_SCHEDULED = 2

# Tryb urlopowy: dozwolony zakres liczby dni (0 = wyłączony)
HOLIDAY_MODE_MAX_DAYS = 40

# Ile wpisów historii regeneracji trzymać w atrybutach sensora
REGEN_HISTORY_LIMIT = 20

PLATFORMS: list[str] = ["sensor", "binary_sensor", "button", "number"]
