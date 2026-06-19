import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/predict"
API_KEY = "darksky-secret-key"

st.title("AeroPlan Voyages — Vérification de retard")

# Valeurs fixes pour le test de connexion
vol_test = {
    "MONTH": 10,
    "AIRLINE_ID": 19805,
    "ORIGIN_STATE_FIPS": 6,
    "DEST_STATE_FIPS": 36,
    "DEST_WAC": 22,
    "CRS_DEP_TIME": 800,
    "TAXI_OUT": 15.0,
    "TAXI_IN": 8.0,
    "CRS_ARR_TIME": 1130,
    "CRS_ELAPSED_TIME": 210.0,
    "FLIGHTS": 1.0,
    "DISTANCE": 1500.0,
    "UNIQUE_CARRIER_ENCODED": 3,
}

if st.button("Tester la connexion à l'API"):
    response = requests.post(
        API_URL,
        json=vol_test,
        headers={"X-API-Key": API_KEY},
    )
    if response.status_code == 200:
        st.success("Connexion réussie")
        st.json(response.json())
    else:
        st.error(f"Erreur {response.status_code} : {response.text}")
