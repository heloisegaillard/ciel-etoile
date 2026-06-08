"""
Étape 1 - Filtrage du dataset Globe at Night 2017
Compétences : C1, C3

Objectif : extraire uniquement les observations réalisées en France
depuis le dataset mondial GaN2017, nettoyer les colonnes inutiles
et exporter un CSV propre pour la suite du projet.

Source : Globe at Night - https://www.globeatnight.org/
"""

import pandas as pd

# ============================================================
# 1. CHARGEMENT
# ============================================================
df = pd.read_csv("data/raw/GaN2017.csv")

print(f"Dataset complet : {len(df)} lignes")
print(f"Colonnes disponibles : {df.columns.tolist()}")

# ============================================================
# 2. FILTRAGE FRANCE
# ============================================================
df_france = df[df["Country"] == "France"].copy()

print(f"\nAprès filtrage France : {len(df_france)} lignes")

# ============================================================
# 3. ANALYSE QUALITÉ DES DONNÉES
# ============================================================
print("\n--- Valeurs manquantes ---")
print(df_france.isnull().sum())

# ============================================================
# 4. NETTOYAGE
# Colonnes conservées et justification :
# - Latitude / Longitude : coordonnées GPS, indispensables
# - Elevation(m) : altitude de l'observation
# - LocalDate / LocalTime : date et heure locale de l'observation
# - LimitingMag : magnitude limite visible à l'oeil nu (mesure clé
#   de la pollution lumineuse, de 1=très pollué à 7=ciel parfait)
# - SQMReading : mesure instrumentale de la luminosité du ciel
#   (Sky Quality Meter), 116 valeurs manquantes conservées car
#   LimitingMag reste disponible comme indicateur principal
# - CloudCover : couverture nuageuse (clear / cloudy...)
# - Constellation : constellation observée
#
# Colonnes exclues :
# - ID, ObsType, UTDate, UTTime : non pertinents pour l'analyse
# - SQMSerial : numéro de série du capteur, inutile
# - SkyComment, LocationComment : commentaires libres non exploitables
# - Country : colonne de filtrage, devenue redondante
# ============================================================
colonnes_utiles = [
    "Latitude", "Longitude", "Elevation(m)",
    "LocalDate", "LocalTime", "LimitingMag",
    "SQMReading", "CloudCover", "Constellation"
]

df_france = df_france[colonnes_utiles]

# Suppression des entrées sans coordonnées GPS (inutilisables)
avant = len(df_france)
df_france = df_france.dropna(subset=["Latitude", "Longitude"])
apres = len(df_france)

print(f"\nLignes supprimées (sans GPS) : {avant - apres}")
print(f"Dataset final : {apres} lignes")
print(f"\nAperçu des données :")
print(df_france.head())

# ============================================================
# 5. EXPORT
# ============================================================
df_france.to_csv("data/processed/GaN2017_france.csv", index=False)

print("\n✅ Export réussi : data/processed/GaN2017_france.csv")
