ETATS_FIPS = {
    "Californie": 6,
    "New York": 36,
    "Texas": 48,
    "Floride": 12,
    "Illinois": 17,
}


def heure_vers_hhmm(heure, minute):
    # convertit une heure et des minutes en format HHMM attendu par le modèle
    return heure * 100 + minute


def construire_payload(mois, origine, destination, heure_depart, heure_arrivee,
                        taxi_out, taxi_in, duree_vol, distance, compagnie_encoded):
    # construit le dictionnaire envoyé à l'API à partir des champs du formulaire
    return {
        "MONTH": mois,
        "AIRLINE_ID": 19805,
        "ORIGIN_STATE_FIPS": ETATS_FIPS[origine],
        "DEST_STATE_FIPS": ETATS_FIPS[destination],
        "DEST_WAC": 22,
        "CRS_DEP_TIME": heure_depart,
        "TAXI_OUT": float(taxi_out),
        "TAXI_IN": float(taxi_in),
        "CRS_ARR_TIME": heure_arrivee,
        "CRS_ELAPSED_TIME": float(duree_vol),
        "FLIGHTS": 1.0,
        "DISTANCE": float(distance),
        "UNIQUE_CARRIER_ENCODED": compagnie_encoded,
    }


def niveau_risque(probabilite):
    # détermine le niveau de risque affiché à partir de la probabilité de retard
    if probabilite < 0.30:
        return "faible"
    elif probabilite < 0.55:
        return "modere"
    else:
        return "eleve"
