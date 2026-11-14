"""Horaires de prière - Masjid Nima Bernard-Kopé (Lomé, Togo).

Application Streamlit publique qui affiche les horaires des cinq prières du jour
(source : API Aladhan), l'heure de l'Iqama de chaque prière et le temps restant
avant la prochaine prière. Les décalages d'Iqama se règlent dans IQAMA_OFFSETS.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------

MOSQUE_NAME = "Masjid Nima Bernard-Kopé"
APP_VERSION = "1.3.0"
DEFAULT_CITY = "Lomé"
DEFAULT_COUNTRY = "Togo"
DEFAULT_LAT, DEFAULT_LON = 6.17249, 1.23136

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
# Minutes entre l'appel à la prière (Adhan) et l'Iqama
IQAMA_OFFSETS = {"Fajr": 10, "Dhuhr": 5, "Asr": 5, "Maghrib": 5, "Isha": 10}

ALADHAN_URL = "https://api.aladhan.com/v1/timingsByCity"
CALCULATION_METHOD = 2  # Islamic Society of North America (ISNA)
REFRESH_INTERVAL_MS = 60 * 1000

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = [
    "janvier", "février", "mars", "avril", "mai", "juin",
    "juillet", "août", "septembre", "octobre", "novembre", "décembre",
]
MOIS_HEGIRIENS = [
    "Mouharram", "Safar", "Rabi al-Awwal", "Rabi ath-Thani", "Joumada al-Oula",
    "Joumada ath-Thania", "Rajab", "Chaabane", "Ramadan", "Chawwal",
    "Dhou al-Qi'da", "Dhou al-Hijja",
]

st.set_page_config(page_title=f"{MOSQUE_NAME} - Horaires de prière", layout="centered")


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def get_prayer_data(city: str, country: str) -> dict | None:
    """Récupère les horaires, les dates et le fuseau horaire de la ville."""
    try:
        response = requests.get(
            ALADHAN_URL,
            params={"city": city, "country": country, "method": CALCULATION_METHOD},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["data"]
    except (requests.RequestException, KeyError, ValueError):
        return None


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def reverse_geocode(lat: float, lon: float) -> tuple[str, str] | None:
    """Retrouve la ville et le pays à partir de coordonnées GPS."""
    try:
        location = Nominatim(user_agent="mon-app-priere").reverse((lat, lon), language="fr")
    except Exception:
        return None
    if not location:
        return None
    address = location.raw.get("address", {})
    city = address.get("city") or address.get("town") or address.get("village")
    country = address.get("country")
    return (city, country) if city and country else None


def local_now(data: dict) -> datetime:
    """Heure actuelle dans le fuseau horaire de la ville (UTC si inconnu)."""
    try:
        return datetime.now(ZoneInfo(data["meta"]["timezone"]))
    except (KeyError, ValueError, TypeError):
        return datetime.now(ZoneInfo("UTC"))


def format_gregorian(now: datetime) -> str:
    return f"{JOURS[now.weekday()].capitalize()} {now.day} {MOIS[now.month - 1]} {now.year}"


def format_hijri(data: dict) -> str:
    hijri = data["date"]["hijri"]
    month = MOIS_HEGIRIENS[int(hijri["month"]["number"]) - 1]
    return f"{int(hijri['day'])} {month} {hijri['year']} H"


def to_time(hhmm: str, now: datetime) -> datetime:
    """Convertit "HH:MM" en datetime du jour, dans le fuseau de `now`."""
    hour, minute = (int(part) for part in hhmm[:5].split(":"))
    return now.replace(hour=hour, minute=minute, second=0, microsecond=0)


def iqama_time(prayer_time: str, offset_minutes: int) -> str:
    start = datetime.strptime(prayer_time[:5], "%H:%M")
    return (start + timedelta(minutes=offset_minutes)).strftime("%H:%M")


def next_prayer(timings: dict, now: datetime) -> tuple[str, timedelta]:
    """Prochaine prière et temps restant (Fajr du lendemain après Isha)."""
    for prayer in PRAYERS:
        start = to_time(timings[prayer], now)
        if start > now:
            return prayer, start - now
    tomorrow_fajr = to_time(timings["Fajr"], now) + timedelta(days=1)
    return "Fajr", tomorrow_fajr - now


def format_delay(delta: timedelta) -> str:
    minutes = int(delta.total_seconds() // 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours} h {minutes:02d}" if hours else f"{minutes} min"


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

# Chaque bloc fixe son fond ET sa couleur de texte : l'affichage reste lisible
# quel que soit le thème (clair ou sombre) choisi par le visiteur.
CSS = """
<style>
.header {
    text-align: center;
    padding: 2.2rem 1rem;
    border-radius: 16px;
    background: linear-gradient(135deg, #0B4F3C 0%, #13795B 100%);
    color: #FFFFFF;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.25);
}
.header h1 { color: #FFFFFF; font-size: 2rem; margin: 0 0 0.4rem 0; padding: 0; }
.header .place { color: #D9F2E6; font-size: 1.05rem; margin: 0; }
.header .dates { color: #FFFFFF; font-size: 1.15rem; margin: 0.4rem 0 0 0; }
.next {
    margin: 1.2rem 0 0.4rem 0;
    padding: 0.9rem 1.2rem;
    border-radius: 12px;
    background: #FFF4D6;
    color: #5C4400;
    border-left: 6px solid #D4A017;
    font-size: 1.1rem;
}
.next strong { color: #3D2D00; }
.prayer-card {
    padding: 1.1rem 1.4rem;
    margin: 0.7rem 0;
    border-radius: 14px;
    background: #FFFFFF;
    color: #1F2D3A;
    border: 2px solid #E3E8EC;
    box-shadow: 0 3px 6px rgba(0, 0, 0, 0.08);
}
.prayer-card.is-next { border-color: #D4A017; background: #FFFBEF; }
.prayer-card h3 { color: #13795B; margin: 0 0 0.3rem 0; padding: 0; font-size: 1.25rem; }
.prayer-card .time { color: #1F2D3A; font-size: 1.7rem; font-weight: bold; margin: 0; }
.prayer-card .iqama { color: #4A5A68; font-size: 1rem; margin: 0.2rem 0 0 0; }
</style>
"""


def render_header(city: str, country: str, data: dict | None, now: datetime | None) -> None:
    dates = f"{format_gregorian(now)} | {format_hijri(data)}" if data and now else ""
    st.markdown(
        f"""
        <div class="header">
            <h1>{MOSQUE_NAME}</h1>
            <p class="place">Horaires de prière - {city}, {country}</p>
            <p class="dates">{dates}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def select_location() -> tuple[str, str]:
    """Choix du lieu dans le panneau latéral (Lomé par défaut)."""
    with st.sidebar:
        st.header("Lieu")
        method = st.radio("Localisation", ["Saisie manuelle", "Coordonnées GPS"])
        if method == "Coordonnées GPS":
            lat = st.number_input("Latitude", value=DEFAULT_LAT, format="%.5f")
            lon = st.number_input("Longitude", value=DEFAULT_LON, format="%.5f")
            found = reverse_geocode(lat, lon)
            if found is None:
                st.warning("Lieu introuvable, utilisation de Lomé.")
                return DEFAULT_CITY, DEFAULT_COUNTRY
            return found
        city = st.text_input("Ville", DEFAULT_CITY)
        country = st.text_input("Pays", DEFAULT_COUNTRY)
        return city, country


def render_next_prayer(prayer: str, delay: timedelta) -> None:
    st.markdown(
        f'<div class="next">Prochaine prière : <strong>{prayer}</strong> '
        f"dans <strong>{format_delay(delay)}</strong></div>",
        unsafe_allow_html=True,
    )


def render_prayer_times(timings: dict, upcoming: str) -> None:
    cols = st.columns(2)
    for idx, prayer in enumerate(PRAYERS):
        prayer_time = timings[prayer][:5]
        offset = IQAMA_OFFSETS[prayer]
        css_class = "prayer-card is-next" if prayer == upcoming else "prayer-card"
        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class="{css_class}">
                    <h3>{prayer}</h3>
                    <p class="time">{prayer_time}</p>
                    <p class="iqama">Iqama : {iqama_time(prayer_time, offset)} (+{offset} min)</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def main() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
    city, country = select_location()
    data = get_prayer_data(city, country)

    if data is None:
        render_header(city, country, None, None)
        st.error("Les horaires de prière ne sont pas disponibles pour ce lieu.")
        return

    now = local_now(data)
    render_header(city, country, data, now)
    st_autorefresh(interval=REFRESH_INTERVAL_MS, key="prayer_times_refresh")

    timings = data["timings"]
    upcoming, delay = next_prayer(timings, now)
    render_next_prayer(upcoming, delay)
    render_prayer_times(timings, upcoming)


main()
st.markdown("---")
st.caption(f"Développé par Yacoubou KOUMAI - v{APP_VERSION} - Horaires : API Aladhan")
