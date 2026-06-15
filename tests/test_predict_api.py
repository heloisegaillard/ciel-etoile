from fastapi.testclient import TestClient
from src.model.predict_api.main import app
import pandas as pd
import joblib

client = TestClient(app)

HEADERS = {"X-API-Key": "darksky-secret-key"}

SAMPLE_FLIGHT = {
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


# --- C9 : tests de l'API REST exposant le modèle ---

def test_root_is_accessible():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["statut"] == "API opérationnelle"


def test_predict_without_api_key_returns_403():
    response = client.post("/predict", json=SAMPLE_FLIGHT)
    assert response.status_code == 403


def test_predict_with_invalid_api_key_returns_403():
    response = client.post(
        "/predict",
        json=SAMPLE_FLIGHT,
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 403


def test_predict_with_valid_key_returns_200():
    response = client.post("/predict", json=SAMPLE_FLIGHT, headers=HEADERS)
    assert response.status_code == 200


def test_predict_response_has_correct_fields():
    response = client.post("/predict", json=SAMPLE_FLIGHT, headers=HEADERS)
    data = response.json()
    assert "retard_predit" in data
    assert "probabilite_retard" in data
    assert "interpretation" in data


def test_health_endpoint_returns_model_info():
    response = client.get("/health", headers=HEADERS)
    assert response.status_code == 200
    assert "modele" in response.json()
    assert "features" in response.json()


def test_health_without_api_key_returns_403():
    response = client.get("/health")
    assert response.status_code == 403


# --- C12 : tests automatisés du modèle IA ---

def test_prediction_is_binary():
    # la sortie du modèle doit être 0 ou 1
    response = client.post("/predict", json=SAMPLE_FLIGHT, headers=HEADERS)
    assert response.json()["retard_predit"] in [0, 1]


def test_probability_is_between_0_and_1():
    # la probabilité doit toujours rester dans l'intervalle valide
    response = client.post("/predict", json=SAMPLE_FLIGHT, headers=HEADERS)
    proba = response.json()["probabilite_retard"]
    assert 0.0 <= proba <= 1.0


def test_missing_field_returns_422():
    # un champ manquant doit déclencher une erreur de validation Pydantic
    incomplete_flight = {k: v for k, v in SAMPLE_FLIGHT.items() if k != "MONTH"}
    response = client.post("/predict", json=incomplete_flight, headers=HEADERS)
    assert response.status_code == 422


def test_invalid_field_type_returns_422():
    # un type incorrect sur un champ numérique doit être rejeté
    bad_flight = SAMPLE_FLIGHT.copy()
    bad_flight["MONTH"] = "octobre"
    response = client.post("/predict", json=bad_flight, headers=HEADERS)
    assert response.status_code == 422


def test_model_file_exists():
    # le fichier modèle sérialisé doit être présent sur le disque
    import os
    assert os.path.exists("models/xgboost_model.pkl")


def test_feature_names_file_exists():
    # la liste des features doit également être sauvegardée
    import os
    assert os.path.exists("models/feature_names.pkl")


def test_model_loads_correctly():
    # le modèle doit se charger sans erreur et être utilisable
    model = joblib.load("models/xgboost_model.pkl")
    assert model is not None


def test_feature_names_match_expected():
    # les features sauvegardées doivent correspondre aux 13 colonnes attendues
    feature_names = joblib.load("models/feature_names.pkl")
    expected = [
        'MONTH', 'AIRLINE_ID', 'ORIGIN_STATE_FIPS', 'DEST_STATE_FIPS',
        'DEST_WAC', 'CRS_DEP_TIME', 'TAXI_OUT', 'TAXI_IN', 'CRS_ARR_TIME',
        'CRS_ELAPSED_TIME', 'FLIGHTS', 'DISTANCE', 'UNIQUE_CARRIER_ENCODED'
    ]
    assert feature_names == expected


def test_model_predicts_on_valid_dataframe():
    # le modèle doit produire une prédiction sur un DataFrame bien formé
    model = joblib.load("models/xgboost_model.pkl")
    feature_names = joblib.load("models/feature_names.pkl")
    data = pd.DataFrame([SAMPLE_FLIGHT])[feature_names]
    prediction = model.predict(data)
    assert prediction[0] in [0, 1]


def test_model_returns_probabilities():
    # predict_proba doit retourner deux colonnes (classe 0 et classe 1)
    model = joblib.load("models/xgboost_model.pkl")
    feature_names = joblib.load("models/feature_names.pkl")
    data = pd.DataFrame([SAMPLE_FLIGHT])[feature_names]
    proba = model.predict_proba(data)
    assert proba.shape[1] == 2
    assert abs(proba[0][0] + proba[0][1] - 1.0) < 1e-6
