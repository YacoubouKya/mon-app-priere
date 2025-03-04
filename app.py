import streamlit as st
import requests
import streamlit_authenticator as stauth
from geopy.geocoders import Nominatim
from datetime import datetime, timedelta
import pytz
from streamlit_autorefresh import st_autorefresh
import yaml

# -------------------- CONFIGURATION --------------------

# Configuration de la page
st.set_page_config(
    page_title="Masjid Nima Bernard-Kopé - Horaires de Prière",
    page_icon="🕌",
    layout="centered"
)

# Charger la configuration de l'authentification
with open('config.yaml') as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Gestion de la connexion
try:
    auth_data = authenticator.login(
        location='sidebar',
        fields={
            'Form name': 'Connexion',
            'Username': 'Identifiant',
            'Password': 'Mot de passe',
            'Login': 'Se connecter'
        }
    )
    if auth_data:
        name, authentication_status, username = auth_data
    else:
        name, authentication_status, username = None, None, None
except TypeError:
    name, authentication_status, username = authenticator.login('Login', 'sidebar')

# Gestion des états d'authentification
if authentication_status:
    # --- Partie connectée ---
    st.sidebar.success(f"✅ Connecté en tant que {name}")
    authenticator.logout("Se déconnecter", "sidebar")

      # Ajout d'un style CSS personnalisé
    st.markdown("""
    <style>
    .prayer-card {
        padding: 1.5rem;
        margin: 1rem 0;
        border-radius: 15px;
        background: #ffffff;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .prayer-card:hover {
        transform: translateY(-5px);
    }
    .prayer-time {
        font-size: 1.4rem;
        color: #2c3e50;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)




# -------------------- CONFIGURATION DES HORAIRES --------------------

# Paramètres par défaut pour l'Iqama et les rappels
if 'iqama_offsets' not in st.session_state:
    st.session_state.iqama_offsets = {"Fajr": 10, "Dhuhr": 5, "Asr": 5, "Maghrib": 5, "Isha": 10}

if 'reminder_settings' not in st.session_state:
    st.session_state.reminder_settings = {"Fajr": 15, "Dhuhr": 10, "Asr": 10, "Maghrib": 10, "Isha": 15}

# Liens audio pour Adhan et rappels
ADHAN_SOUND = "https://cdn.pixabay.com/download/audio/2021/08/04/audio_23d5f5d2f8.mp3"
REMINDER_SOUND = "https://cdn.pixabay.com/download/audio/2022/03/15/audio_d1715f6d94.mp3"

# Fonction pour jouer un son
def play_sound(url):
    st.audio(url, format="audio/mp3")

# Fonction pour récupérer les horaires de prière via API
@st.cache_data(ttl=3600)  # Cache des données pendant 1h
def get_prayer_times(city, country):
    try:
        response = requests.get(
            f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2",
            timeout=10
        )
        if response.ok:
            return response.json()["data"]["timings"]
    except requests.RequestException as e:
        st.error(f"Erreur API : {e}")
    return None

# 🔹 Variables de localisation
city = "Lomé"
country = "Togo"

# 🔹 Fonction pour récupérer la date islamique
def get_islamic_date():
    try:
        today = datetime.today().strftime('%d-%m-%Y')
        response = requests.get(f"http://api.aladhan.com/v1/gToH?date={today}", timeout=10)
        if response.ok:
            hijri_date = response.json()["data"]["hijri"]
            return f"{hijri_date['day']} {hijri_date['month']['en']} {hijri_date['year']}H"
    except Exception as e:
        st.error(f"Erreur lors de la récupération de la date islamique : {str(e)}")
        return "Date islamique inconnue"

# 🔹 Récupération des dates
hijri_date = get_islamic_date()
gregorian_date = datetime.today().strftime('%d %B %Y')

# 🔹 Affichage du titre avec l’image de fond
st.markdown(f"""
    <style>
        .title-container {{
            text-align: center;
            padding: 50px 0;
            background: url('https://upload.wikimedia.org/wikipedia/commons/7/73/Hassan_II_Mosque.jpg');
            background-size: cover;
            background-position: center;
            color: white;
            font-weight: bold;
            border-radius: 15px;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
        }}
        .title-container h1 {{
            font-size: 2.5rem;
            margin-bottom: 5px;
        }}
        .title-container h2 {{
            font-size: 1.5rem;
            margin-top: 0;
        }}
    </style>
    <div class="title-container">
        <h1>🕌 Masjid Nima Bernard-Kopé - Horaires de Prière</h1>
        <h2>{city}, {country} - {gregorian_date} | {hijri_date}</h2>
    </div>
""", unsafe_allow_html=True)

# -------------------- INTERFACE PRINCIPALE --------------------
if authentication_status:
    st.sidebar.success(f"✅ Connecté en tant que {name}")
    authenticator.logout("Se déconnecter", "sidebar", key="logout_button")

    # Admin : Configuration des horaires Iqama et rappels
    if username == "admin":
        with st.sidebar.expander("⚙ Configuration"):
            st.write("*Décalages Iqama (minutes):*")
            for prayer in st.session_state.iqama_offsets:
                st.session_state.iqama_offsets[prayer] = st.number_input(
                    prayer, 0, 60, st.session_state.iqama_offsets[prayer], key=f"iqama_{prayer}")

            st.write("*Rappels (minutes avant):*")
            for prayer in st.session_state.reminder_settings:
                st.session_state.reminder_settings[prayer] = st.number_input(
                    prayer, 0, 60, st.session_state.reminder_settings[prayer], key=f"reminder_{prayer}")

    # Localisation
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            location_method = st.radio("Méthode:", ["📍 GPS", "🌍 Manuel"])

        city, country = "Lomé", "Togo"

        if location_method == "📍 GPS":
            lat = col2.number_input("Latitude", 6.17249, format="%.5f")
            lon = col2.number_input("Longitude", 1.23136, format="%.5f")
            try:
                geolocator = Nominatim(user_agent="prayer_app")
                location = geolocator.reverse((lat, lon), language='fr')
                if location:
                    address = location.raw.get('address', {})
                    city = address.get('city', 'Lomé')
                    country = address.get('country', 'Togo')
            except Exception as e:
                st.error(f"Erreur géolocalisation : {e}")
        else:
            city = st.text_input("Ville", "Lomé")
            country = st.text_input("Pays", "Togo")

    # Récupération des horaires
    prayer_times = get_prayer_times(city, country)
    if prayer_times:
        # Rafraîchissement automatique toutes les 60 secondes
        st_autorefresh(interval=60*1000, key="prayer_times_refresh")

        st.markdown('<div class="main-container">', unsafe_allow_html=True)

        # Affichage des horaires
        cols = st.columns(2)
        for idx, prayer in enumerate(["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]):
            with cols[idx % 2]:
                prayer_time = prayer_times[prayer]
                iqama_time = datetime.strptime(prayer_time, "%H:%M") + timedelta(minutes=st.session_state.iqama_offsets[prayer])

                st.markdown(f"""
                <div class="prayer-card">
                    <h3>{prayer}</h3>
                    <p style="font-size:1.5rem; margin:0.5rem 0;">{prayer_time} ⏳ +{st.session_state.iqama_offsets[prayer]} min</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.error("Les horaires de prière ne sont pas disponibles.")

elif authentication_status is False:
    st.error("Identifiants incorrects.")
elif authentication_status is None:
    st.warning("Veuillez vous connecter.")
st.markdown("---")
st.caption("Développé par Yacoubou KOUMAI - © 2024 | v1.0.0")
