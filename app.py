"""Horaires de prière - Masjid Nima Bernard-Kopé (Lomé, Togo).

Application Streamlit qui affiche les horaires des cinq prières du jour
(source : API Aladhan) avec l'heure de l'Iqama de chaque prière.
L'accès est protégé par une authentification ; le compte administrateur
peut ajuster les décalages d'Iqama.
"""

from __future__ import annotations

import copy
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import requests
import streamlit as st
import streamlit_authenticator as stauth
import yaml
from geopy.geocoders import Nominatim
from streamlit_autorefresh import st_autorefresh

# ---------------------------------------------------------------------------
# Paramètres
# ---------------------------------------------------------------------------

APP_TITLE = "Masjid Nima Bernard-Kopé - Horaires de prière"
APP_VERSION = "1.1.0"
DEFAULT_CITY = "Lomé"
DEFAULT_COUNTRY = "Togo"
DEFAULT_LAT, DEFAULT_LON = 6.17249, 1.23136
ADMIN_USERNAME = "admin"

PRAYERS = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
DEFAULT_IQAMA_OFFSETS = {"Fajr": 10, "Dhuhr": 5, "Asr": 5, "Maghrib": 5, "Isha": 10}

ALADHAN_URL = "https://api.aladhan.com/v1/timingsByCity"
CALCULATION_METHOD = 2  # Islamic Society of North America (ISNA)
REFRESH_INTERVAL_MS = 60 * 1000
LOCAL_CONFIG_FILE = Path(__file__).parent / "config.yaml"

st.set_page_config(page_title=APP_TITLE, layout="centered")


# ---------------------------------------------------------------------------
# Authentification
# ---------------------------------------------------------------------------

def _to_dict(obj: Any) -> Any:
    """Convertit récursivement un objet st.secrets en dict modifiable."""
    if hasattr(obj, "items"):
        return {key: _to_dict(value) for key, value in obj.items()}
    return copy.deepcopy(obj)


def load_auth_config() -> dict | None:
    """Charge les identifiants depuis st.secrets (déploiement) ou config.yaml (local).

    Aucun identifiant n'est stocké dans le dépôt : voir README, section
    "Configuration de l'authentification".
    """
    try:
        if "credentials" in st.secrets and "cookie" in st.secrets:
            return {
                "credentials": _to_dict(st.secrets["credentials"]),
                "cookie": _to_dict(st.secrets["cookie"]),
            }
    except FileNotFoundError:
        pass  # pas de secrets.toml en local

    if LOCAL_CONFIG_FILE.exists():
        with LOCAL_CONFIG_FILE.open(encoding="utf-8") as file:
            return yaml.safe_load(file)
    return None


def build_authenticator(config: dict) -> stauth.Authenticate:
    cookie = config["cookie"]
    return stauth.Authenticate(
        config["credentials"],
        cookie["name"],
        cookie["key"],
        cookie["expiry_days"],
    )


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


def render_admin_settings() -> None:
    with st.sidebar.expander("Configuration de l'Iqama"):
        st.caption("Décalage entre l'appel à la prière et l'Iqama (minutes)")
        for prayer in PRAYERS:
            st.session_state.iqama_offsets[prayer] = st.number_input(
                prayer, 0, 60, st.session_state.iqama_offsets[prayer], key=f"iqama_{prayer}"
            )


def select_location() -> tuple[str, str]:
    col1, col2 = st.columns(2)
    with col1:
        method = st.radio("Localisation", ["Coordonnées GPS", "Saisie manuelle"])
    with col2:
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
        offset = st.session_state.iqama_offsets[prayer]
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

    if "iqama_offsets" not in st.session_state:
        st.session_state.iqama_offsets = dict(DEFAULT_IQAMA_OFFSETS)

    config = load_auth_config()
    if config is None:
        render_header(DEFAULT_CITY, DEFAULT_COUNTRY, None)
        st.error(
            "Configuration d'authentification absente. Ajoutez les identifiants dans "
            "les secrets Streamlit ou dans un fichier config.yaml (voir README)."
        )
        return

    authenticator = build_authenticator(config)
    authenticator.login(
        location="sidebar",
        fields={
            "Form name": "Connexion",
            "Username": "Identifiant",
            "Password": "Mot de passe",
            "Login": "Se connecter",
        },
    )
    status = st.session_state.get("authentication_status")

    if not status:
        render_header(DEFAULT_CITY, DEFAULT_COUNTRY, None)
        if status is False:
            st.error("Identifiants incorrects.")
        else:
            st.info("Veuillez vous connecter depuis le panneau latéral.")
        return

    st.sidebar.success(f"Connecté en tant que {st.session_state.get('name')}")
    authenticator.logout("Se déconnecter", "sidebar")
    if st.session_state.get("username") == ADMIN_USERNAME:
        render_admin_settings()

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
