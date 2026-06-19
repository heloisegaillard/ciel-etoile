import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/predict"
API_KEY = "darksky-secret-key"

st.set_page_config(page_title="AeroPlan Voyages — Vérification de retard", page_icon="✈️")

st.title(" AeroPlan Voyages")
st.subheader("Vérification du risque de retard avant réservation")

st.markdown(
    "Renseignez les informations du vol pour estimer la probabilité de retard "
    "avant de confirmer la réservation auprès du client."
)

# Dictionnaires de correspondance pour des champs plus lisibles côté conseiller
ETATS_FIPS = {
    "Californie": 6,
    "New York": 36,
    "Texas": 48,
    "Floride": 12,
    "Illinois": 17,
}

with st.form("formulaire_vol"):
    col1, col2 = st.columns(2)

    with col1:
        mois = st.selectbox(
            "Mois du vol",
            options=list(range(1, 13)),
            format_func=lambda m: [
                "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"
            ][m - 1],
            help="Mois prévu du départ",
        )
        origine = st.selectbox("État d'origine", options=list(ETATS_FIPS.keys()))
        destination = st.selectbox("État de destination", options=list(ETATS_FIPS.keys()), index=1)
        heure_depart = st.number_input(
            "Heure de départ programmée (format HHMM)",
            min_value=0, max_value=2359, value=800,
            help="Exemple : 800 pour 8h00, 1430 pour 14h30",
        )
        heure_arrivee = st.number_input(
            "Heure d'arrivée programmée (format HHMM)",
            min_value=0, max_value=2359, value=1130,
        )
        distance = st.number_input("Distance du vol (en miles)", min_value=0.0, value=1500.0)

    with col2:
        duree_vol = st.number_input("Durée de vol estimée (minutes)", min_value=0.0, value=210.0)
        taxi_out = st.number_input("Temps de roulage au départ (minutes)", min_value=0.0, value=15.0)
        taxi_in = st.number_input("Temps de roulage à l'arrivée (minutes)", min_value=0.0, value=8.0)
        compagnie_encoded = st.slider(
            "Identifiant compagnie (encodage interne)",
            min_value=0, max_value=20, value=3,
            help="Correspond à l'encodage utilisé lors de l'entraînement du modèle",
        )

    submitted = st.form_submit_button("Vérifier le risque de retard")

if submitted:
    payload = {
        "MONTH": mois,
        "AIRLINE_ID": 19805,
        "ORIGIN_STATE_FIPS": ETATS_FIPS[origine],
        "DEST_STATE_FIPS": ETATS_FIPS[destination],
        "DEST_WAC": 22,
        "CRS_DEP_TIME": int(heure_depart),
        "TAXI_OUT": taxi_out,
        "TAXI_IN": taxi_in,
        "CRS_ARR_TIME": int(heure_arrivee),
        "CRS_ELAPSED_TIME": duree_vol,
        "FLIGHTS": 1.0,
        "DISTANCE": distance,
        "UNIQUE_CARRIER_ENCODED": compagnie_encoded,
    }

    try:
        response = requests.post(API_URL, json=payload, headers={"X-API-Key": API_KEY}, timeout=5)
    except requests.exceptions.ConnectionError:
        st.error("Impossible de contacter l'API de prédiction. Vérifiez qu'elle est bien lancée.")
        st.stop()

    if response.status_code == 200:
        data = response.json()
        proba = data["probabilite_retard"]

        st.divider()

        if proba < 0.30:
            st.success(f"🟢 Risque faible — {proba:.0%} de probabilité de retard")
        elif proba < 0.55:
            st.warning(f"🟠 Risque modéré — {proba:.0%} de probabilité de retard")
        else:
            st.error(f"🔴 Risque élevé — {proba:.0%} de probabilité de retard")

        st.write(data["interpretation"])

    elif response.status_code == 403:
        st.error("Authentification refusée. Vérifiez la clé API.")
    elif response.status_code == 422:
        st.error("Données du formulaire invalides. Vérifiez les champs saisis.")
    else:
        st.error(f"Erreur inattendue ({response.status_code})")
