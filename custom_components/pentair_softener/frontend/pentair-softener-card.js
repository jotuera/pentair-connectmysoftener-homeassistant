/*
 * Pentair ConnectMySoftener - Lovelace card
 *
 * A ready-made dashboard card for the Pentair softener integration. It finds the
 * integration's entities on their own (by platform / translation_key), so the only
 * config you need is:
 *
 *   type: custom:pentair-softener-card
 *
 * Optional:
 *   device: <device_id>   # pick one softener when you have several
 *   title:  "..."         # override the header text
 *
 * UI text follows Home Assistant's language: English is the source, with built-in
 * translations for Polish, German, French, Dutch, Spanish, Italian, Romanian,
 * Russian and Czech (9 languages). Units (L / gal, g, L/min) come straight from the
 * entities, so US and metric accounts are handled automatically.
 *
 * No build step: plain custom element, no dependencies.
 */

const T = {
  en: {
    title: "Water softener",
    remaining: "Remaining capacity",
    status: "Status",
    salt: "Salt",
    ok: "OK",
    low: "Low",
    today: "Today",
    week: "Week",
    month: "Month",
    year: "Year",
    last_regen: "Last regen.",
    regen_at: "Regeneration at",
    salt_regen: "Salt / regen.",
    btn_salt: "Salt added",
    btn_regen: "Regenerate",
    btn_night: "Night regen.",
    flow: "Flow",
    diag: "Diagnostics",
    hidden: "hidden",
    shown: "shown",
    d_today: "today",
    d_yesterday: "yesterday",
    days: "days",
    serial: "Serial number",
    software: "Software",
    total: "Total volume",
    regens: "Regenerations",
    last_service: "Last service",
    warnings: "Warnings",
    holiday: "Holiday mode",
    hardness: "Water hardness",
    devtime: "Device time",
    online: "Online",
    pending: "Pending changes",
    yes: "Yes",
    no: "No",
    st_in_service: "In service",
    st_regenerating: "Regenerating",
    st_holiday: "Holiday",
    st_standby: "Standby",
    st_offline: "Offline",
  },
  pl: {
    title: "Zmiękczacz wody", remaining: "Pozostała pojemność", status: "Status",
    salt: "Sól", ok: "OK", low: "Niski", today: "Dziś", week: "Tydzień",
    month: "Miesiąc", year: "Rok", last_regen: "Ostatnia regen.",
    regen_at: "Regeneracja o", salt_regen: "Sól / regen.", btn_salt: "Dodano sól",
    btn_regen: "Regeneruj", btn_night: "Regen. w nocy", flow: "Przepływ",
    diag: "Diagnostyka", hidden: "ukryta", shown: "widoczna", d_today: "dziś",
    d_yesterday: "wczoraj", days: "dni", serial: "Numer seryjny",
    software: "Oprogramowanie", total: "Zużycie całkowite", regens: "Regeneracje",
    last_service: "Ostatni serwis", warnings: "Ostrzeżenia", holiday: "Tryb urlopowy",
    hardness: "Twardość wody", devtime: "Czas urządzenia", online: "Online",
    pending: "Zmiany oczekujące", yes: "Tak", no: "Nie",
    st_in_service: "Czynny", st_regenerating: "Regeneracja", st_holiday: "Tryb urlopowy",
    st_standby: "Czuwanie", st_offline: "Offline",
  },
  de: {
    title: "Wasserenthärter", remaining: "Restkapazität", status: "Status",
    salt: "Salz", ok: "OK", low: "Niedrig", today: "Heute", week: "Woche",
    month: "Monat", year: "Jahr", last_regen: "Letzte Regen.",
    regen_at: "Regeneration um", salt_regen: "Salz / Regen.", btn_salt: "Salz aufgefüllt",
    btn_regen: "Regenerieren", btn_night: "Nacht-Regen.", flow: "Durchfluss",
    diag: "Diagnose", hidden: "verborgen", shown: "sichtbar", d_today: "heute",
    d_yesterday: "gestern", days: "Tage", serial: "Seriennummer",
    software: "Software", total: "Gesamtverbrauch", regens: "Regenerationen",
    last_service: "Letzter Service", warnings: "Warnungen", holiday: "Urlaubsmodus",
    hardness: "Wasserhärte", devtime: "Gerätezeit", online: "Online",
    pending: "Ausstehende Änderungen", yes: "Ja", no: "Nein",
    st_in_service: "In Betrieb", st_regenerating: "Regeneriert", st_holiday: "Urlaub",
    st_standby: "Standby", st_offline: "Offline",
  },
  fr: {
    title: "Adoucisseur d'eau", remaining: "Capacité restante", status: "Statut",
    salt: "Sel", ok: "OK", low: "Bas", today: "Aujourd'hui", week: "Semaine",
    month: "Mois", year: "Année", last_regen: "Dern. régén.",
    regen_at: "Régénération à", salt_regen: "Sel / régén.", btn_salt: "Sel ajouté",
    btn_regen: "Régénérer", btn_night: "Régén. nuit", flow: "Débit",
    diag: "Diagnostic", hidden: "masqué", shown: "affiché", d_today: "auj.",
    d_yesterday: "hier", days: "jours", serial: "Numéro de série",
    software: "Logiciel", total: "Volume total", regens: "Régénérations",
    last_service: "Dernier entretien", warnings: "Alertes", holiday: "Mode vacances",
    hardness: "Dureté de l'eau", devtime: "Heure de l'appareil", online: "En ligne",
    pending: "Modifications en attente", yes: "Oui", no: "Non",
    st_in_service: "En service", st_regenerating: "Régénération", st_holiday: "Vacances",
    st_standby: "Veille", st_offline: "Hors ligne",
  },
  nl: {
    title: "Waterontharder", remaining: "Resterende capaciteit", status: "Status",
    salt: "Zout", ok: "OK", low: "Laag", today: "Vandaag", week: "Week",
    month: "Maand", year: "Jaar", last_regen: "Laatste regen.",
    regen_at: "Regeneratie om", salt_regen: "Zout / regen.", btn_salt: "Zout bijgevuld",
    btn_regen: "Regenereren", btn_night: "Nacht-regen.", flow: "Doorstroming",
    diag: "Diagnostiek", hidden: "verborgen", shown: "zichtbaar", d_today: "vandaag",
    d_yesterday: "gisteren", days: "dagen", serial: "Serienummer",
    software: "Software", total: "Totaal volume", regens: "Regeneraties",
    last_service: "Laatste service", warnings: "Waarschuwingen", holiday: "Vakantiemodus",
    hardness: "Waterhardheid", devtime: "Apparaattijd", online: "Online",
    pending: "Openstaande wijzigingen", yes: "Ja", no: "Nee",
    st_in_service: "In bedrijf", st_regenerating: "Regenereren", st_holiday: "Vakantie",
    st_standby: "Stand-by", st_offline: "Offline",
  },
  es: {
    title: "Descalcificador", remaining: "Capacidad restante", status: "Estado",
    salt: "Sal", ok: "OK", low: "Bajo", today: "Hoy", week: "Semana",
    month: "Mes", year: "Año", last_regen: "Última regen.",
    regen_at: "Regeneración a las", salt_regen: "Sal / regen.", btn_salt: "Sal añadida",
    btn_regen: "Regenerar", btn_night: "Regen. nocturna", flow: "Caudal",
    diag: "Diagnóstico", hidden: "oculto", shown: "visible", d_today: "hoy",
    d_yesterday: "ayer", days: "días", serial: "Número de serie",
    software: "Software", total: "Volumen total", regens: "Regeneraciones",
    last_service: "Último servicio", warnings: "Advertencias", holiday: "Modo vacaciones",
    hardness: "Dureza del agua", devtime: "Hora del equipo", online: "En línea",
    pending: "Cambios pendientes", yes: "Sí", no: "No",
    st_in_service: "En servicio", st_regenerating: "Regenerando", st_holiday: "Vacaciones",
    st_standby: "En espera", st_offline: "Sin conexión",
  },
  it: {
    title: "Addolcitore", remaining: "Capacità residua", status: "Stato",
    salt: "Sale", ok: "OK", low: "Basso", today: "Oggi", week: "Settimana",
    month: "Mese", year: "Anno", last_regen: "Ultima rigen.",
    regen_at: "Rigenerazione alle", salt_regen: "Sale / rigen.", btn_salt: "Sale aggiunto",
    btn_regen: "Rigenera", btn_night: "Rigen. notturna", flow: "Flusso",
    diag: "Diagnostica", hidden: "nascosta", shown: "visibile", d_today: "oggi",
    d_yesterday: "ieri", days: "giorni", serial: "Numero di serie",
    software: "Software", total: "Volume totale", regens: "Rigenerazioni",
    last_service: "Ultima manut.", warnings: "Avvisi", holiday: "Modalità vacanza",
    hardness: "Durezza acqua", devtime: "Ora dispositivo", online: "Online",
    pending: "Modifiche in sospeso", yes: "Sì", no: "No",
    st_in_service: "In servizio", st_regenerating: "Rigenerazione", st_holiday: "Vacanza",
    st_standby: "Standby", st_offline: "Offline",
  },
  ro: {
    title: "Dedurizator de apă", remaining: "Capacitate rămasă", status: "Stare",
    salt: "Sare", ok: "OK", low: "Scăzut", today: "Azi", week: "Săptămână",
    month: "Lună", year: "An", last_regen: "Ultima regen.",
    regen_at: "Regenerare la", salt_regen: "Sare / regen.", btn_salt: "Sare adăugată",
    btn_regen: "Regenerează", btn_night: "Regen. noapte", flow: "Debit",
    diag: "Diagnostic", hidden: "ascuns", shown: "afișat", d_today: "azi",
    d_yesterday: "ieri", days: "zile", serial: "Număr de serie",
    software: "Software", total: "Volum total", regens: "Regenerări",
    last_service: "Ultima revizie", warnings: "Avertismente", holiday: "Mod vacanță",
    hardness: "Duritatea apei", devtime: "Ora aparatului", online: "Conectat",
    pending: "Modificări în așteptare", yes: "Da", no: "Nu",
    st_in_service: "În funcțiune", st_regenerating: "Se regenerează", st_holiday: "Vacanță",
    st_standby: "Standby", st_offline: "Deconectat",
  },
  ru: {
    title: "Умягчитель воды", remaining: "Остаточный ресурс", status: "Статус",
    salt: "Соль", ok: "OK", low: "Низкий", today: "Сегодня", week: "Неделя",
    month: "Месяц", year: "Год", last_regen: "Посл. регенер.",
    regen_at: "Регенерация в", salt_regen: "Соль / регенер.", btn_salt: "Соль добавлена",
    btn_regen: "Регенерация", btn_night: "Ночная регенер.", flow: "Поток",
    diag: "Диагностика", hidden: "скрыто", shown: "показано", d_today: "сегодня",
    d_yesterday: "вчера", days: "дн.", serial: "Серийный номер",
    software: "ПО", total: "Общий объём", regens: "Регенерации",
    last_service: "Последнее ТО", warnings: "Предупреждения", holiday: "Режим отпуска",
    hardness: "Жёсткость воды", devtime: "Время устройства", online: "В сети",
    pending: "Ожидающие изменения", yes: "Да", no: "Нет",
    st_in_service: "В работе", st_regenerating: "Регенерация", st_holiday: "Отпуск",
    st_standby: "Ожидание", st_offline: "Не в сети",
  },
  cs: {
    title: "Změkčovač vody", remaining: "Zbývající kapacita", status: "Stav",
    salt: "Sůl", ok: "OK", low: "Nízká", today: "Dnes", week: "Týden",
    month: "Měsíc", year: "Rok", last_regen: "Posl. regenerace",
    regen_at: "Regenerace v", salt_regen: "Sůl / regen.", btn_salt: "Sůl doplněna",
    btn_regen: "Regenerovat", btn_night: "Noční regen.", flow: "Průtok",
    diag: "Diagnostika", hidden: "skrytá", shown: "zobrazená", d_today: "dnes",
    d_yesterday: "včera", days: "dní", serial: "Sériové číslo",
    software: "Software", total: "Celkový objem", regens: "Regenerace",
    last_service: "Poslední servis", warnings: "Varování", holiday: "Režim dovolené",
    hardness: "Tvrdost vody", devtime: "Čas zařízení", online: "Online",
    pending: "Čekající změny", yes: "Ano", no: "Ne",
    st_in_service: "V provozu", st_regenerating: "Regenerace", st_holiday: "Dovolená",
    st_standby: "Pohotovost", st_offline: "Offline",
  },
};

const STATUS_KEY = {
  in_service: "st_in_service",
  regenerating: "st_regenerating",
  holiday: "st_holiday",
  standby: "st_standby",
  offline: "st_offline",
};

const STATUS_ICON = {
  in_service: "mdi:water-check",
  regenerating: "mdi:water-sync",
  holiday: "mdi:beach",
  standby: "mdi:power-standby",
  offline: "mdi:water-off",
};

const UNAVAILABLE = new Set(["unavailable", "unknown", "none", "", undefined, null]);

class PentairSoftenerCard extends HTMLElement {
  setConfig(config) {
    this._config = config || {};
    this._diag = false;
    this._root = null;
  }

  getCardSize() {
    return 6;
  }

  static getStubConfig() {
    return { type: "custom:pentair-softener-card" };
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  // ---- helpers -------------------------------------------------------------

  _lang() {
    const raw = String(
      this._hass?.locale?.language || this._hass?.language || "en"
    )
      .slice(0, 2)
      .toLowerCase();
    return T[raw] ? raw : "en";
  }

  _t(key) {
    const lang = this._lang();
    return (T[lang] && T[lang][key]) || T.en[key] || key;
  }

  // Map the integration's entities by their translation_key, so names stay
  // English and language-independent no matter the HA UI language.
  _entities() {
    const hass = this._hass;
    const map = {};
    const reg = hass.entities || {};
    const want = this._config.device;
    for (const [eid, meta] of Object.entries(reg)) {
      if (!meta || meta.platform !== "pentair_softener") continue;
      if (want && meta.device_id !== want) continue;
      let key = meta.translation_key;
      if (!key && meta.unique_id && meta.unique_id.includes("_")) {
        key = meta.unique_id.slice(meta.unique_id.indexOf("_") + 1);
      }
      if (key && !map[key]) map[key] = eid;
    }
    return map;
  }

  _state(map, key) {
    const eid = map[key];
    if (!eid) return null;
    return this._hass.states[eid] || null;
  }

  _has(map, key) {
    const s = this._state(map, key);
    return s && !UNAVAILABLE.has(String(s.state).toLowerCase());
  }

  _num(obj) {
    if (!obj) return null;
    const n = parseFloat(obj.state);
    return Number.isFinite(n) ? Math.round(n) : null;
  }

  _valUnit(map, key) {
    const obj = this._state(map, key);
    if (!obj || UNAVAILABLE.has(String(obj.state).toLowerCase())) return "—";
    const n = this._num(obj);
    const v = n === null ? obj.state : n;
    const unit = obj.attributes && obj.attributes.unit_of_measurement;
    return unit ? `${v} ${unit}` : `${v}`;
  }

  _clock(map, key) {
    const obj = this._state(map, key);
    if (!obj || UNAVAILABLE.has(String(obj.state).toLowerCase())) return "—";
    const m = String(obj.state).match(/^(\d{1,2}:\d{2})/);
    return m ? m[1] : obj.state;
  }

  _ts(map, key) {
    const obj = this._state(map, key);
    if (!obj || UNAVAILABLE.has(String(obj.state).toLowerCase())) return "—";
    const d = new Date(obj.state);
    if (isNaN(d.getTime())) return obj.state;
    const lang = this._lang();
    const now = new Date();
    const sameDay = (a, b) =>
      a.getFullYear() === b.getFullYear() &&
      a.getMonth() === b.getMonth() &&
      a.getDate() === b.getDate();
    const hm = d.toLocaleTimeString(lang, { hour: "2-digit", minute: "2-digit" });
    const y = new Date(now);
    y.setDate(now.getDate() - 1);
    if (sameDay(d, now)) return `${this._t("d_today")} ${hm}`;
    if (sameDay(d, y)) return `${this._t("d_yesterday")} ${hm}`;
    const date = d.toLocaleDateString(lang, { day: "2-digit", month: "2-digit" });
    return `${date} ${hm}`;
  }

  // ---- rendering -----------------------------------------------------------

  _render() {
    if (!this._hass || !this._config) return;
    if (!this._root) {
      const shadow = this.attachShadow({ mode: "open" });
      shadow.innerHTML = `<style>${STYLE}</style><ha-card></ha-card>`;
      this._root = shadow.querySelector("ha-card");
      this._root.addEventListener("click", (e) => this._onClick(e));
    }

    const map = this._entities();
    const statusObj = this._state(map, "status");
    const statusRaw = statusObj ? String(statusObj.state) : null;
    const statusLabel =
      statusRaw && STATUS_KEY[statusRaw]
        ? this._t(STATUS_KEY[statusRaw])
        : statusRaw || "—";
    const statusIcon = (statusRaw && STATUS_ICON[statusRaw]) || "mdi:water";

    const progress = this._num(this._state(map, "status_progress"));
    const pct = progress === null ? null : Math.max(0, Math.min(100, progress));

    // hero subtitle
    let subtitle = "";
    if (statusRaw === "regenerating") {
      subtitle = this._t("st_regenerating");
    } else {
      const parts = [];
      if (this._has(map, "remaining_capacity"))
        parts.push(this._valUnit(map, "remaining_capacity"));
      const days = this._num(this._state(map, "days_remaining"));
      if (days !== null) parts.push(`~${days} ${this._t("days")}`);
      subtitle = parts.join(" · ");
    }

    const saltLow =
      this._state(map, "salt_warning") &&
      String(this._state(map, "salt_warning").state) === "on";

    const title = this._config.title || this._t("title");

    const tiles = [];

    // status
    tiles.push(
      this._tile({
        icon: statusIcon,
        value: statusLabel,
        label: this._t("status"),
        entity: map.status,
      })
    );
    // salt warning
    if (map.salt_warning) {
      tiles.push(
        this._tile({
          icon: saltLow ? "mdi:shaker-outline" : "mdi:check-circle-outline",
          value: saltLow ? this._t("low") : this._t("ok"),
          label: this._t("salt"),
          cls: saltLow ? "warn" : "good",
          entity: map.salt_warning,
        })
      );
    }
    // water usage (optional)
    const usage = [
      ["water_used_day", "today"],
      ["water_used_week", "week"],
      ["water_used_month", "month"],
    ];
    for (const [k, lbl] of usage) {
      if (map[k]) {
        tiles.push(
          this._tile({
            icon: "mdi:water",
            value: this._valUnit(map, k),
            label: this._t(lbl),
            entity: map[k],
          })
        );
      }
    }
    // last regeneration
    if (map.last_regeneration) {
      tiles.push(
        this._tile({
          icon: "mdi:history",
          value: this._ts(map, "last_regeneration"),
          label: this._t("last_regen"),
          entity: map.last_regeneration,
        })
      );
    }
    // regeneration time
    if (map.regeneration_time) {
      tiles.push(
        this._tile({
          icon: "mdi:clock-outline",
          value: this._clock(map, "regeneration_time"),
          label: this._t("regen_at"),
          entity: map.regeneration_time,
        })
      );
    }
    // salt used / regen
    if (map.salt_used) {
      tiles.push(
        this._tile({
          icon: "mdi:shaker",
          value: this._valUnit(map, "salt_used"),
          label: this._t("salt_regen"),
          entity: map.salt_used,
        })
      );
    }

    // buttons
    const buttons = [];
    if (map.salt_added)
      buttons.push(this._btn("mdi:shaker-outline", this._t("btn_salt"), map.salt_added));
    if (map.regenerate_now)
      buttons.push(this._btn("mdi:refresh", this._t("btn_regen"), map.regenerate_now));
    if (map.regenerate_scheduled)
      buttons.push(
        this._btn("mdi:weather-night", this._t("btn_night"), map.regenerate_scheduled)
      );

    // flow + diagnostics toggle
    const bottom = [];
    if (map.current_flow) {
      bottom.push(
        this._tile({
          icon: "mdi:waves-arrow-right",
          value: this._valUnit(map, "current_flow"),
          label: this._t("flow"),
          entity: map.current_flow,
        })
      );
    }
    bottom.push(
      this._tile({
        icon: "mdi:wrench",
        value: this._diag ? this._t("shown") : this._t("hidden"),
        label: this._t("diag"),
        cls: "action",
        action: "toggle-diag",
      })
    );

    const diagHtml = this._diag ? this._diagPanel(map) : "";

    this._root.innerHTML = `
      <div class="head">
        <ha-icon icon="mdi:water-outline"></ha-icon>
        <span>${esc(title)}</span>
      </div>
      <div class="hero${saltLow ? " warn" : ""}">
        <div class="hero-top">
          <div class="hero-label">
            <ha-icon icon="mdi:water-percent"></ha-icon>
            <div>
              <div class="hero-title">${esc(this._t("remaining"))}</div>
              <div class="hero-sub">${esc(subtitle || "—")}</div>
            </div>
          </div>
          <div class="hero-pct">${pct === null ? "—" : pct + "%"}</div>
        </div>
        <div class="bar"><div class="bar-fill" style="width:${pct === null ? 0 : pct}%"></div></div>
      </div>
      <div class="grid">${tiles.join("")}</div>
      ${buttons.length ? `<div class="btns">${buttons.join("")}</div>` : ""}
      <div class="grid bottom">${bottom.join("")}</div>
      ${diagHtml}
    `;
  }

  _tile({ icon, value, label, cls = "", entity = "", action = "" }) {
    const act = action
      ? `data-action="${action}"`
      : entity
      ? `data-action="more-info" data-entity="${entity}"`
      : "";
    const clickable = act ? " clickable" : "";
    return `
      <div class="tile ${cls}${clickable}" ${act}>
        <ha-icon icon="${icon}"></ha-icon>
        <div class="tile-val">${esc(value)}</div>
        <div class="tile-lbl">${esc(label)}</div>
      </div>`;
  }

  _btn(icon, label, entity) {
    return `
      <button class="pbtn" data-action="press" data-entity="${entity}">
        <ha-icon icon="${icon}"></ha-icon>
        <span>${esc(label)}</span>
      </button>`;
  }

  _diagPanel(map) {
    const rows = [];
    const add = (label, value) =>
      rows.push(`<div class="drow"><span>${esc(label)}</span><b>${esc(value)}</b></div>`);

    if (map.serial_number) add(this._t("serial"), this._stateText(map, "serial_number"));
    if (map.software_version) add(this._t("software"), this._stateText(map, "software_version"));
    if (map.total_volume) add(this._t("total"), this._valUnit(map, "total_volume"));
    if (map.regeneration_count) add(this._t("regens"), this._stateText(map, "regeneration_count"));
    if (map.last_maintenance) add(this._t("last_service"), this._ts(map, "last_maintenance"));
    if (map.warnings) add(this._t("warnings"), this._stateText(map, "warnings"));
    if (map.holiday_mode) add(this._t("holiday"), this._valUnit(map, "holiday_mode"));
    if (map.water_hardness) add(this._t("hardness"), this._stateText(map, "water_hardness"));
    if (map.system_time) add(this._t("devtime"), this._clock(map, "system_time"));
    if (map.pending_changes) {
      const on = String(this._state(map, "pending_changes").state) === "on";
      add(this._t("pending"), on ? this._t("yes") : this._t("no"));
    }
    if (map.online) {
      const on = String(this._state(map, "online").state) === "on";
      add(this._t("online"), on ? this._t("yes") : this._t("no"));
    }
    return `<div class="diag">${rows.join("")}</div>`;
  }

  _stateText(map, key) {
    const obj = this._state(map, key);
    if (!obj || UNAVAILABLE.has(String(obj.state).toLowerCase())) return "—";
    return obj.state;
  }

  _onClick(e) {
    const el = e.target.closest("[data-action]");
    if (!el) return;
    const action = el.getAttribute("data-action");
    if (action === "toggle-diag") {
      this._diag = !this._diag;
      this._render();
      return;
    }
    const entity = el.getAttribute("data-entity");
    if (!entity) return;
    if (action === "press") {
      this._hass.callService("button", "press", { entity_id: entity });
    } else if (action === "more-info") {
      this.dispatchEvent(
        new CustomEvent("hass-more-info", {
          detail: { entityId: entity },
          bubbles: true,
          composed: true,
        })
      );
    }
  }
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])
  );
}

const STYLE = `
:host { display: block; }
ha-card { padding: 14px; }
ha-icon { --mdc-icon-size: 20px; }
.head {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.78rem; font-weight: 600; letter-spacing: 0.08em;
  text-transform: uppercase; color: var(--secondary-text-color);
  margin-bottom: 12px;
}
.head ha-icon { color: var(--primary-color); }
.hero {
  border-radius: 14px; padding: 14px 16px; margin-bottom: 12px;
  background: var(--secondary-background-color);
  border: 1px solid var(--divider-color);
}
.hero.warn { border-color: var(--warning-color, #ff9800); }
.hero-top { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.hero-label { display: flex; align-items: center; gap: 10px; min-width: 0; }
.hero-label ha-icon { color: var(--primary-color); --mdc-icon-size: 26px; flex: none; }
.hero-title { font-size: 0.82rem; color: var(--secondary-text-color); }
.hero-sub { font-size: 1.02rem; font-weight: 600; color: var(--primary-text-color); margin-top: 2px; }
.hero-pct { font-size: 2.1rem; font-weight: 700; color: var(--primary-text-color); line-height: 1; }
.bar {
  height: 10px; border-radius: 6px; margin-top: 12px; overflow: hidden;
  background: var(--divider-color);
}
.bar-fill {
  height: 100%; border-radius: 6px;
  background: linear-gradient(90deg, #2ec27e, #45d98a);
  transition: width 0.4s ease;
}
.hero.warn .bar-fill { background: linear-gradient(90deg, #f5a623, #ffb74d); }
.grid {
  display: grid; gap: 8px;
  grid-template-columns: repeat(auto-fill, minmax(96px, 1fr));
}
.grid.bottom { margin-top: 8px; }
.tile {
  background: var(--secondary-background-color);
  border: 1px solid var(--divider-color);
  border-radius: 12px; padding: 10px 8px; text-align: center;
  display: flex; flex-direction: column; align-items: center; gap: 3px;
}
.tile.clickable { cursor: pointer; transition: border-color 0.15s, transform 0.05s; }
.tile.clickable:hover { border-color: var(--primary-color); }
.tile.clickable:active { transform: scale(0.97); }
.tile ha-icon { color: var(--primary-color); }
.tile.good ha-icon { color: var(--success-color, #2ec27e); }
.tile.warn ha-icon, .tile.warn .tile-val { color: var(--warning-color, #ff9800); }
.tile.action ha-icon { color: var(--secondary-text-color); }
.tile-val { font-size: 0.95rem; font-weight: 600; color: var(--primary-text-color); line-height: 1.15; }
.tile-lbl { font-size: 0.72rem; color: var(--secondary-text-color); }
.btns { display: grid; gap: 8px; grid-template-columns: repeat(auto-fit, minmax(100px, 1fr)); margin-top: 8px; }
.pbtn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  padding: 11px 8px; border-radius: 12px; cursor: pointer;
  background: var(--secondary-background-color);
  border: 1px solid var(--divider-color);
  color: var(--primary-text-color);
  font-size: 0.8rem; font-weight: 600; letter-spacing: 0.02em;
  text-transform: uppercase; font-family: inherit;
}
.pbtn ha-icon { color: var(--primary-color); }
.pbtn:hover { border-color: var(--primary-color); }
.pbtn:active { transform: scale(0.98); }
.diag {
  margin-top: 10px; border-radius: 12px; padding: 4px 12px;
  background: var(--secondary-background-color);
  border: 1px solid var(--divider-color);
}
.drow { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; font-size: 0.86rem; }
.drow + .drow { border-top: 1px solid var(--divider-color); }
.drow span { color: var(--secondary-text-color); }
.drow b { color: var(--primary-text-color); font-weight: 600; text-align: right; }
`;

if (!customElements.get("pentair-softener-card")) {
  customElements.define("pentair-softener-card", PentairSoftenerCard);
}

window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "pentair-softener-card")) {
  window.customCards.push({
    type: "pentair-softener-card",
    name: "Pentair ConnectMySoftener",
    description: "Dashboard card for the Pentair water softener integration.",
    preview: false,
  });
}

console.info(
  "%c PENTAIR-SOFTENER-CARD %c loaded ",
  "background:#2ec27e;color:#fff;border-radius:3px 0 0 3px;padding:2px 4px",
  "background:#333;color:#fff;border-radius:0 3px 3px 0;padding:2px 4px"
);
