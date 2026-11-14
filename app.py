"""Horaires de prière - Masjid Nima Bernard-Kopé (Lomé, Togo).

Application Streamlit publique qui affiche les horaires des cinq prières du jour
(source : API Aladhan) avec l'heure de l'Iqama de chaque prière.
Les décalages d'Iqama se règlent dans IQAMA_OFFSETS.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import requests
import streamlit as st
from geopy.geocoders import Nominatim
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------

APP_TITLE = "Masjid Nima Bernard-Kopé - Horaires de prière"
APP_VERSION = "1.2.0"
DEFAULT_CITY = "Lomé"
DEFAULT_COUNTRY = "Togo"
DEFAULT_LAT, DEFAULT_LON = 6.17249, 1.23136

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
# Minutes entre l'appel à la prière (Adhan) et l'Iqama
IQAMA_OFFSETS = {"Fajr": 10, "Dhuhr": 5, "Asr": 5, "Maghrib": 5, "Isha": 10}

ALADHAN_URL = "https://api.aladhan.com/v1/timingsByCity"
CALCULATION_METHOD = 2  # Islamic Society of North America (ISNA)
REFRESH_INTERVAL_MS = 60 * 1000

st.set_page_config(page_title=APP_TITLE, layout="centered")


# ---------------------------------------------------------------------------
# Données
# ---------------------------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def get_prayer_data(city: str, country: str) -> dict | None:
    """Récupère les horaires, la date hégirienne et le fuseau horaire de la ville."""
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


def format_hijri(data: dict) -> str:
    hijri = data["date"]["hijri"]
    return f"{hijri['day']} {hijri['month']['en']} {hijri['year']} H"


def format_gregorian(data: dict) -> str:
    gregorian = data["date"]["gregorian"]
    return f"{gregorian['day']} {gregorian['month']['en']} {gregorian['year']}"


def iqama_time(prayer_time: str, offset_minutes: int) -> str:
    start = datetime.strptime(prayer_time[:5], "%H:%M")
    return (start + timedelta(minutes=offset_minutes)).strftime("%H:%M")


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------

CSS = """
<style>
.title-container {
    text-align: center;
    padding: 50px 0;
    background: url('https://upload.wikimedia.org/wikipedia/commons/7/73/Hassan_II_Mosque.jpg');
    background-size: cover;
    background-position: center;
    color: white;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}
.title-container h1 { font-size: 2.3rem; margin-bottom: 5px; }
.title-container h2 { font-size: 1.3rem; margin-top: 0; font-weight: normal; }
.prayer-card {
    padding: 1.2rem 1.5rem;
    margin: 0.8rem 0;
    border-radius: 15px;
    background: #ffffff;
    color: #2c3e50;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.prayer-card h3 { margin: 0 0 0.4rem 0; color: #2c3e50; }
.prayer-card .time { font-size: 1.5rem; font-weight: bold; margin: 0; }
.prayer-card .iqama { font-size: 1rem; color: #5d6d7e; margin: 0.2rem 0 0 0; }
</style>
"""


def render_header(city: str, country: str, data: dict | None) -> None:
    dates = f" - {format_gregorian(data)} | {format_hijri(data)}" if data else ""
    st.markdown(
        f"""
        <div class="title-container">
            <h1>{APP_TITLE}</h1>
            <h2>{city}, {country}{dates}</h2>
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


def render_prayer_times(timings: dict) -> None:
    cols = st.columns(2)
    for idx, prayer in enumerate(PRAYERS):
        prayer_time = timings[prayer][:5]
        offset = IQAMA_OFFSETS[prayer]
        with cols[idx % 2]:
            st.markdown(
                f"""
                <div class="prayer-card">
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
    render_header(city, country, data)

    if data is None:
        st.error("Les horaires de prière ne sont pas disponibles pour ce lieu.")
        return

    st_autorefresh(interval=REFRESH_INTERVAL_MS, key="prayer_times_refresh")
    render_prayer_times(data["timings"])


main()
st.markdown("---")
st.caption(f"Développé par Yacoubou KOUMAI - v{APP_VERSION}")
