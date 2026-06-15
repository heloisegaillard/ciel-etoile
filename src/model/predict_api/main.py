import joblib
import os
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

# Chargement du modèle et des features au démarrage
model = joblib.load("models/xgboost_model.pkl")
feature_names = joblib.load("models/feature_names.pkl")

# Clé API — en production elle viendrait d'une variable d'environnement
API_KEY = os.getenv("API_KEY", "darksky-secret-key")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

app = FastAPI(
    title="DarkSky Travel — API de prédiction de retards",
    description="Prédit si un vol sera en retard avant son départ, "
                "pour anticiper la logistique des voyages d'observation astronomique.",
    version="1.0.0",
)


def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Clé API invalide ou manquante")
    return key


class FlightInput(BaseModel):
    MONTH: int
    AIRLINE_ID: int
    ORIGIN_STATE_FIPS: int
    DEST_STATE_FIPS: int
    DEST_WAC: int
    CRS_DEP_TIME: int
    TAXI_OUT: float
    TAXI_IN: float
    CRS_ARR_TIME: int
    CRS_ELAPSED_TIME: float
    FLIGHTS: float
    DISTANCE: float
    UNIQUE_CARRIER_ENCODED: int


class PredictionOutput(BaseModel):
    retard_predit: int
    probabilite_retard: float
    interpretation: str


@app.get("/", tags=["Statut"])
def root():
    return {"statut": "API opérationnelle", "projet": "DarkSky Travel"}


@app.post("/predict", response_model=PredictionOutput, tags=["Prédiction"])
def predict(flight: FlightInput, api_key: str = Depends(verify_api_key)):
    # Reconstruction du vecteur de features dans le bon ordre
    import pandas as pd
    data = pd.DataFrame([flight.model_dump()])[feature_names]

    prediction = int(model.predict(data)[0])
    proba = float(model.predict_proba(data)[0][1])

    if prediction == 1:
        interpretation = (
            f"Vol prédit en retard (probabilité : {proba:.0%}). "
            "DarkSky Travel recommande d'anticiper la logistique client."
        )
    else:
        interpretation = (
            f"Vol prédit à l'heure (probabilité de retard : {proba:.0%}). "
            "Aucune action corrective nécessaire."
        )

    return PredictionOutput(
        retard_predit=prediction,
        probabilite_retard=round(proba, 4),
        interpretation=interpretation,
    )


@app.get("/health", tags=["Statut"])
def health(api_key: str = Depends(verify_api_key)):
    return {
        "statut": "ok",
        "modele": "XGBoost v1.0",
        "features": feature_names,
    }
