"""
Étape C3 - Agrégation des 3 sources de données
Compétences : C3

Objectif : charger les 3 sources, vérifier et homogénéiser
les formats, supprimer les entrées corrompues, et préparer
les données pour l'import dans la BDD unifiée.

Sources :
- data/processed/GaN2017_france.csv (Globe at Night)
- data/processed/villes_etoilees_api.csv (API Datastro)
- data/raw/meteorite_fr.csv (MetBull)
"""

import pandas as pd

# ============================================================
# 1. CHARGEMENT DES 3 SOURCES
# ============================================================
print("=== CHARGEMENT DES SOURCES ===\n")

df_gan = pd.read_csv("data/processed/GaN2017_france.csv")
df_villes = pd.read_csv("data/processed/villes_etoilees_api.csv")
df_meteorites = pd.read_csv("data/raw/meteorite_fr.csv")

print(f"GaN France       : {len(df_gan)} lignes, colonnes : {df_gan.columns.tolist()}")
print(f"Villes étoilées  : {len(df_villes)} lignes, colonnes : {df_villes.columns.tolist()}")
print(f"Météorites       : {len(df_meteorites)} lignes, colonnes : {df_meteorites.columns.tolist()}")

# ============================================================
# 2. HOMOGÉNÉISATION DES FORMATS
# ============================================================
print("\n=== HOMOGÉNÉISATION DES FORMATS ===\n")

# --- GaN ---
# Renommage pour cohérence
df_gan = df_gan.rename(columns={
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Elevation(m)": "elevation",
    "LocalDate": "local_date",
    "LocalTime": "local_time",
    "LimitingMag": "limiting_mag",
    "SQMReading": "sqm_reading",
    "CloudCover": "cloud_cover",
    "Constellation": "constellation"
})
# Format date
df_gan["local_date"] = pd.to_datetime(df_gan["local_date"], errors="coerce")
print(f"GaN - local_date format : {df_gan['local_date'].dtype}")

# --- Villes étoilées ---
# Renommage pour cohérence
df_villes = df_villes.rename(columns={
    "ville": "ville",
    "departement": "departement",
    "region": "region",
    "nombre_d_etoiles": "nombre_etoiles",
    "latitude": "latitude",
    "longitude": "longitude"
})
# nombre_etoiles en entier
df_villes["nombre_etoiles"] = pd.to_numeric(df_villes["nombre_etoiles"], errors="coerce")
print(f"Villes - nombre_etoiles format : {df_villes['nombre_etoiles'].dtype}")

# --- Météorites ---
df_meteorites = df_meteorites.rename(columns={
    "Code": "code",
    "Name": "name",
    "Abbrev": "abbrev",
    "Status": "status",
    "Fall": "fall",
    "Year": "year",
    "Place": "place",
    "Type": "type",
    "Mass": "mass",
    "MetBull": "met_bull",
    "Antarctic": "antarctic",
    "Lat": "latitude",
    "Long": "longitude",
    "Comment": "comment"
})
# year en entier
df_meteorites["year"] = pd.to_numeric(df_meteorites["year"], errors="coerce")
print(f"Météorites - year format : {df_meteorites['year'].dtype}")

# ============================================================
# 3. SUPPRESSION DES ENTRÉES CORROMPUES
# ============================================================
print("\n=== SUPPRESSION DES ENTRÉES CORROMPUES ===\n")

# Règle : toute entrée sans coordonnées GPS est inutilisable
# car la géolocalisation est au cœur du projet

# GaN
avant = len(df_gan)
df_gan = df_gan.dropna(subset=["latitude", "longitude"])
print(f"GaN - supprimées (sans GPS) : {avant - len(df_gan)} lignes")

# Villes
avant = len(df_villes)
df_villes = df_villes.dropna(subset=["latitude", "longitude"])
print(f"Villes - supprimées (sans GPS) : {avant - len(df_villes)} lignes")

# Météorites
avant = len(df_meteorites)
df_meteorites = df_meteorites.dropna(subset=["latitude", "longitude"])
print(f"Météorites - supprimées (sans GPS) : {avant - len(df_meteorites)} lignes")

# ============================================================
# 4. RÉSUMÉ FINAL
# ============================================================
print("\n=== RÉSUMÉ FINAL ===\n")
print(f"GaN France      : {len(df_gan)} observations")
print(f"Villes étoilées : {len(df_villes)} communes")
print(f"Météorites      : {len(df_meteorites)} météorites")

# ============================================================
# 5. EXPORT DES 3 SOURCES NETTOYÉES
# ============================================================
df_gan.to_csv("data/processed/gan_clean.csv", index=False)
df_villes.to_csv("data/processed/villes_clean.csv", index=False)
df_meteorites.to_csv("data/processed/meteorites_clean.csv", index=False)

print("\n✅ Export réussi :")
print("  - data/processed/gan_clean.csv")
print("  - data/processed/villes_clean.csv")
print("  - data/processed/meteorites_clean.csv")
