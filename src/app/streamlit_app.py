import streamlit as st
import requests
import os
import datetime
from dotenv import load_dotenv
from logic import ETATS_FIPS, heure_vers_hhmm, construire_payload, niveau_risque

load_dotenv()

API_URL = "http://127.0.0.1:8000/predict"
API_KEY = os.getenv("PREDICT_API_KEY")

if not API_KEY:
    st.error("Clé API non configurée. Vérifiez le fichier .env (variable PREDICT_API_KEY).")
    st.stop()

st.set_page_config(page_title="AeroPlan Voyages — Vérification de retard", page_icon="✈️")

st.title(" AeroPlan Voyages")
st.subheader("Vérification du risque de retard avant réservation")

st.markdown(
    "Renseignez les informations du vol pour estimer la probabilité de retard "
    "avant de confirmer la réservation auprès du client."
)




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
        heure_depart_input = st.time_input(
            "Heure de départ programmée (format HHMM)",
            value=datetime.time(8, 0),
        )
        heure_arrivee_input = st.time_input(
            "Heure d'arrivée programmée (format HHMM)",
            value=datetime.time(11, 30),
        )
        # Conversion au format HHMM attendu par le modèle

        heure_depart = heure_vers_hhmm(heure_depart_input.hour, heure_depart_input.minute)
        heure_arrivee = heure_vers_hhmm(heure_arrivee_input.hour, heure_arrivee_input.minute)
        distance = st.number_input("Distance du vol (en miles)", min_value=0, value=1500, step=1)

    with col2:
        duree_vol = st.number_input("Durée de vol estimée (minutes)", min_value=0, value=210, step=1)
        taxi_out = st.number_input("Temps de roulage au départ (minutes)", min_value=0, value=15, step=1)
        taxi_in = st.number_input("Temps de roulage à l'arrivée (minutes)", min_value=0, value=8, step=1)
        compagnie_encoded = st.slider(
            "Identifiant compagnie (encodage interne)",
            min_value=0, max_value=20, value=3,
            help="Correspond à l'encodage utilisé lors de l'entraînement du modèle",
        )

    submitted = st.form_submit_button("Vérifier le risque de retard")

if submitted:
    payload = construire_payload(
        mois, origine, destination, heure_depart, heure_arrivee,
        taxi_out, taxi_in, duree_vol, distance, compagnie_encoded
    )


    try:
        response = requests.post(API_URL, json=payload, headers={"X-API-Key": API_KEY}, timeout=5)
    except requests.exceptions.ConnectionError:
        st.error("Impossible de contacter l'API de prédiction. Vérifiez qu'elle est bien lancée.")
        st.stop()

    if response.status_code == 200:
        data = response.json()
        proba = data["probabilite_retard"]

        st.divider()

        niveau = niveau_risque(proba)
        if niveau == "faible":
            st.success(f"🟢 Risque faible — {proba:.0%} de probabilité de retard")
        elif niveau == "modere":
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
