import streamlit as st
import yaml
import requests
import streamlit_authenticator as stauth
from geopy.geocoders import Nominatim
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Masjid Nima Bernard-Kopé - Horaires de Prière",
    page_icon="🕌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
:root {
    --primary-color: #2A5F7F;
    --secondary-color: #DAA520;
    --background-color: #F8F9FA;
}

.header {
    background: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), 
                url('https://th.bing.com/th/id/OIP.rqHaFqlRNxnFnrAHD6YC3QHaE8?rs=1&pid=ImgDetMain');
    background-size: cover;
    color: white;
    padding: 4rem 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
}

.prayer-card {
    background: white;
    border-radius: 15px;
    padding: 1.5rem;
    margin: 1rem;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.3s ease;
    border-left: 5px solid var(--primary-color);
}

.prayer-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0,0,0,0.15);
}

.prayer-time {
    font-size: 1.8rem;
    color: var(--primary-color);
    font-weight: 700;
}

.prayer-name {
    color: var(--secondary-color);
    font-size: 1.2rem;
    text-transform: uppercase;
}

.location-card {
    background: white;
    padding: 2rem;
    border-radius: 15px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# Chargement de la configuration
with open('config.yaml') as file:
    config = yaml.safe_load(file)

# Initialisation de l'authentification
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
    st.sidebar.success(f"✅ Connecté en tant que {name}")
    authenticator.logout("Se déconnecter", "sidebar")

    # En-tête
    st.markdown(f"""
    <div class="header">
        <h1 style="font-size: 2.5rem;">🕌 Masjid Nima Bernard-Kopé</h1>
        <h3>Horaires des prières - {datetime.now().strftime("%d %B %Y")}</h3>
    </div>
    """, unsafe_allow_html=True)

    # Section localisation
    with st.container():
        st.markdown("""
        <div class="location-card">
            <h2 style="color: var(--primary-color);">📍 Configuration de la localisation</h2>
        """, unsafe_allow_html=True)
        
        location_method = st.radio(
            "Méthode de sélection :",
            ["🌍 Géolocalisation automatique", "✍️ Entrée manuelle"],
            horizontal=True
        )
        
        city, country = "Lomé", "Togo"
        
        if location_method == "🌍 Géolocalisation automatique":
            col1, col2 = st.columns(2)
            lat = col1.number_input("Latitude", value=6.17249, format="%.5f")
            lon = col2.number_input("Longitude", value=1.23136, format="%.5f")
            
            try:
                geolocator = Nominatim(user_agent="prayer_times_app")
                location = geolocator.reverse((lat, lon), exactly_one=True, language='fr')
                if location:
                    address = location.raw.get('address', {})
                    city = address.get('city', 'Lomé')
                    country = address.get('country', 'Togo')
            except Exception as e:
                st.error(f"Erreur de géolocalisation : {str(e)}")
        else:
            city = st.text_input("Ville", "Lomé")
            country = st.text_input("Pays", "Togo")

    # Récupération des horaires
    try:
        response = requests.get(
            f"http://api.aladhan.com/v1/timingsByCity?city={city}&country={country}&method=2",
            timeout=10
        )
        prayer_times = response.json()["data"]["timings"] if response.ok else None
    except Exception as e:
        st.error(f"Erreur API : {str(e)}")
        prayer_times = None

    # Affichage des horaires
    if prayer_times:
        st.markdown(f"""
        <div style="margin-top: 2rem;">
            <h2 style="color: var(--primary-color);">⏰ Horaires pour {city}, {country}</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1rem;">
        """, unsafe_allow_html=True)
        
        prayers = {
            "Fajr": "🌅", 
            "Dhuhr": "☀️", 
            "Asr": "⛅", 
            "Maghrib": "🌇", 
            "Isha": "🌙"
        }
        
        cols = st.columns(2)
        for i, (prayer, emoji) in enumerate(prayers.items()):
            with cols[i % 2]:
                st.markdown(f"""
                <div class="prayer-card">
                    <div class="prayer-name">{emoji} {prayer}</div>
                    <div class="prayer-time">{prayer_times.get(prayer, 'N/A')}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Section complémentaire
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div style="margin-top: 2rem;">
                <h3 style="color: var(--primary-color);">📅 Calendrier mensuel</h3>
                <img src="https://via.placeholder.com/600x200?text=Calendrier+des+prières" 
                    style="width: 100%; border-radius: 10px;">
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="margin-top: 2rem;">
                <h3 style="color: var(--primary-color);">📚 Rappels importants</h3>
                <ul style="color: var(--primary-color);">
                    <li>Arriver 10 minutes avant l'iqama</li>
                    <li>Prévoir son tapis de prière</li>
                    <li>Respect des mesures sanitaires</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

elif authentication_status is False:
    st.sidebar.error("❌ Identifiants incorrects")
    st.title("Bienvenue")
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <h3>Veuillez vous connecter</h3>
        <p>Utilisez le formulaire dans la barre latérale →</p>
    </div>
    """, unsafe_allow_html=True)

elif authentication_status is None:
    st.title("Bienvenue")
    st.markdown("""
    <div style="text-align: center; margin-top: 50px;">
        <h3>Veuillez vous connecter</h3>
        <p>Utilisez le formulaire dans la barre latérale →</p>
    </div>
    """, unsafe_allow_html=True)

# Pied de page
st.markdown("---")
st.caption("Développé par Yacoubou KOUMAI - © 2024")