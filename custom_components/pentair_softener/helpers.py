from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import async_generate_entity_id


def build_entity_id(
    entity_id_format: str, coordinator: Any, api: Any, key: str | None
) -> str | None:
    """Zbuduj entity_id z angielskiego klucza, niezależnie od języka HA.

    Domyślnie HA generuje entity_id z *przetłumaczonej* nazwy encji, więc w polskim
    Home Assistancie powstałoby np. sensor.<device>_objetosc_calkowita zamiast
    sensor.<device>_total_volume. entity_id ma być stabilnym identyfikatorem, a nie
    tekstem dla użytkownika – tłumaczymy tylko nazwę wyświetlaną (translation_key).

    Ustawienie entity_id przez integrację przed dodaniem encji jest wspieraną drogą:
    HA wyprowadza z niego internal_integration_suggested_object_id.
    """
    if not key:
        return None
    device = (api.profile or {}).get("name") or "Pentair Softener"
    return async_generate_entity_id(
        entity_id_format, f"{device} {key}", hass=coordinator.hass
    )
