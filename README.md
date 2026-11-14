# Horaires de prière - Masjid Nima Bernard-Kopé

Application web Streamlit, en accès libre, qui affiche les horaires des cinq prières
du jour pour la mosquée Nima Bernard-Kopé (Lomé, Togo), ainsi que l'heure de l'Iqama
de chaque prière.

## Fonctionnalités

- Horaires du jour (Fajr, Dhuhr, Asr, Maghrib, Isha) issus de l'API publique
  [Aladhan](https://aladhan.com/prayer-times-api), méthode de calcul de la Ligue islamique mondiale (`CALCULATION_METHOD` dans `app.py`).
- Heure de l'Iqama calculée à partir d'un décalage fixe par prière.
- Prochaine prière mise en évidence, avec le temps restant (heure locale de la ville).
- Date grégorienne et date hégirienne du jour, en français.
- Couleurs fixes pour chaque bloc : affichage lisible en thème clair comme en thème sombre.
- Choix du lieu dans le panneau latéral : saisie de la ville et du pays, ou coordonnées
  GPS (géocodage inverse via OpenStreetMap) ; Lomé par défaut.
- Actualisation automatique de la page chaque minute.

## Réglage des décalages d'Iqama

Les décalages, en minutes après l'appel à la prière, sont définis en tête de `app.py` :

```python
IQAMA_OFFSETS = {"Fajr": 10, "Dhuhr": 5, "Asr": 5, "Maghrib": 5, "Isha": 10}
```

## Installation locale

```bash
python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Auteur

Yacoubou KOUMAI
