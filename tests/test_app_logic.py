import sys
import os

sys.path.insert(0, os.path.abspath("src/app"))

from logic import ETATS_FIPS, heure_vers_hhmm, construire_payload, niveau_risque


# --- tests de heure_vers_hhmm ---

def test_heure_vers_hhmm_matin():
    # 8h00 doit donner 800
    assert heure_vers_hhmm(8, 0) == 800


def test_heure_vers_hhmm_soir():
    # 22h30 doit donner 2230
    assert heure_vers_hhmm(22, 30) == 2230


def test_heure_vers_hhmm_minuit():
    # minuit doit donner 0
    assert heure_vers_hhmm(0, 0) == 0


def test_heure_vers_hhmm_limite_journee():
    # 23h59 doit donner 2359, la valeur maximale du format HHMM
    assert heure_vers_hhmm(23, 59) == 2359


# --- tests de construire_payload ---

def test_construire_payload_contient_tous_les_champs():
    payload = construire_payload(
        mois=10, origine="Californie", destination="New York",
        heure_depart=800, heure_arrivee=1130,
        taxi_out=15, taxi_in=8, duree_vol=210, distance=1500,
        compagnie_encoded=3,
    )
    champs_attendus = [
        "MONTH", "AIRLINE_ID", "ORIGIN_STATE_FIPS", "DEST_STATE_FIPS",
        "DEST_WAC", "CRS_DEP_TIME", "TAXI_OUT", "TAXI_IN", "CRS_ARR_TIME",
        "CRS_ELAPSED_TIME", "FLIGHTS", "DISTANCE", "UNIQUE_CARRIER_ENCODED"
    ]
    for champ in champs_attendus:
        assert champ in payload


def test_construire_payload_convertit_etats_en_fips():
    # les noms d'états doivent être traduits en codes FIPS numériques
    payload = construire_payload(
        mois=10, origine="Texas", destination="Floride",
        heure_depart=800, heure_arrivee=1130,
        taxi_out=15, taxi_in=8, duree_vol=210, distance=1500,
        compagnie_encoded=3,
    )
    assert payload["ORIGIN_STATE_FIPS"] == ETATS_FIPS["Texas"]
    assert payload["DEST_STATE_FIPS"] == ETATS_FIPS["Floride"]


def test_construire_payload_types_numeriques_sont_float():
    # les quatre champs numériques continus doivent être des float, pas des int
    payload = construire_payload(
        mois=10, origine="Californie", destination="New York",
        heure_depart=800, heure_arrivee=1130,
        taxi_out=15, taxi_in=8, duree_vol=210, distance=1500,
        compagnie_encoded=3,
    )
    assert isinstance(payload["TAXI_OUT"], float)
    assert isinstance(payload["TAXI_IN"], float)
    assert isinstance(payload["CRS_ELAPSED_TIME"], float)
    assert isinstance(payload["DISTANCE"], float)


# --- tests de niveau_risque ---

def test_niveau_risque_faible():
    assert niveau_risque(0.10) == "faible"


def test_niveau_risque_limite_basse_faible():
    # juste en dessous du seuil de 0.30
    assert niveau_risque(0.29) == "faible"


def test_niveau_risque_modere():
    assert niveau_risque(0.40) == "modere"


def test_niveau_risque_limite_haute_modere():
    # juste en dessous du seuil de 0.55
    assert niveau_risque(0.54) == "modere"


def test_niveau_risque_eleve():
    assert niveau_risque(0.80) == "eleve"


def test_niveau_risque_valeur_extreme_zero():
    assert niveau_risque(0.0) == "faible"


def test_niveau_risque_valeur_extreme_un():
    assert niveau_risque(1.0) == "eleve"
