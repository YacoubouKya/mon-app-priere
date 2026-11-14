# Horaires de prière - Masjid Nima Bernard-Kopé

Application web Streamlit qui affiche les horaires des cinq prières du jour pour
la mosquée Nima Bernard-Kopé (Lomé, Togo), ainsi que l'heure de l'Iqama de chaque
prière.

## Fonctionnalités

- Horaires du jour (Fajr, Dhuhr, Asr, Maghrib, Isha) issus de l'API publique
  [Aladhan](https://aladhan.com/prayer-times-api), méthode de calcul ISNA.
- Heure de l'Iqama calculée à partir d'un décalage par prière.
- Date grégorienne et date hégirienne du jour.
- Localisation par coordonnées GPS (géocodage inverse via OpenStreetMap) ou
  saisie manuelle de la ville et du pays ; Lomé par défaut.
- Actualisation automatique de la page chaque minute.
- Accès protégé par identifiant et mot de passe ; le compte `admin` peut ajuster
  les décalages d'Iqama depuis le panneau latéral.

## Structure

```
app.py                         Application Streamlit
requirements.txt               Dépendances Python
config.example.yaml            Modèle de configuration locale des identifiants
.streamlit/secrets.example.toml  Modèle de secrets pour Streamlit Cloud
scripts/hash_password.py       Génération d'un hash bcrypt et d'une clé de cookie
```

## Installation locale

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration de l'authentification

Aucun identifiant n'est stocké dans le dépôt. L'application les lit, dans cet ordre :

1. dans les secrets Streamlit (`st.secrets`) ;
2. à défaut, dans un fichier `config.yaml` à la racine.

Les deux fichiers (`config.yaml` et `.streamlit/secrets.toml`) sont ignorés par git.

Étapes :

1. Générer le hash de chaque mot de passe et une clé de cookie :
   ```bash
   python scripts/hash_password.py
   ```
2. En local : copier `config.example.yaml` en `config.yaml` et y reporter les hashes.
3. Sur Streamlit Cloud : coller le contenu de `.streamlit/secrets.example.toml`,
   complété, dans *Settings > Secrets* de l'application.

## Lancement

```bash
streamlit run app.py
```

## Auteur

Yacoubou KOUMAI
