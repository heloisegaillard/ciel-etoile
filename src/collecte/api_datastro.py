"""
Étape 3 - Collecte des villes étoilées via API Datastro
Compétences : C1

Objectif : récupérer les 374 communes labellisées "Villes et Villages
Étoilés" 2017 depuis l'API OpenDataSoft Datastro, et exporter
le résultat en CSV propre.

Source : https://datastro.aws-ec2-us-east-1.opendatasoft.com
Dataset : communes-etoilees-2017
"""

import requests
import pandas as pd

# ============================================================
# 1. CONFIGURATION DE L'API
# ============================================================
BASE_URL = (
    "https://datastro.aws-ec2-us-east-1.opendatasoft.com"
    "/api/explore/v2.1/catalog/datasets"
    "/communes-etoilees-2017/records"
)

PARAMS = {
    "limit": 100,           # maximum autorisé par l'API
    "order_by": "nombre_d_etoiles desc",
}

# ============================================================
# 2. APPEL API AVEC PAGINATION
# Le dataset contient 374 enregistrements.
# Avec limit=100, on a besoin de 4 pages.
# ============================================================
tous_les_records = []
offset = 0

print("Démarrage de la collecte...")

while True:
    PARAMS["offset"] = offset
    response = requests.get(BASE_URL, params=PARAMS)

    # Vérification du statut HTTP
    if response.status_code != 200:
        print(f"❌ Erreur HTTP {response.status_code}")
        break

    data = response.json()
    records = data.get("results", [])

    # Si plus aucun résultat, on arrête
    if not records:
        break

    tous_les_records.extend(records)
    print(f"  Page offset={offset} → {len(records)} enregistrements récupérés")
    offset += 100

print(f"\nTotal récupéré : {len(tous_les_records)} communes")

# ============================================================
# 3. MISE EN FORME
# ============================================================

df = pd.DataFrame(tous_les_records)

print(f"\nColonnes disponibles : {df.columns.tolist()}")

# Séparation de la colonne geo en latitude / longitude
df["latitude"] = df["geo"].apply(lambda x: x["lat"] if isinstance(x, dict) else None)
df["longitude"] = df["geo"].apply(lambda x: x["lon"] if isinstance(x, dict) else None)
df = df.drop(columns=["geo"])

print(f"\nAperçu :")
print(df.head())
# ============================================================
# 4. EXPORT
# ============================================================
df.to_csv("data/processed/villes_etoilees_api.csv", index=False)

print("\n✅ Export réussi : data/processed/villes_etoilees_api.csv")
