"""
Étape 4 - Enrichissement des datasets avec le code département
Compétences : C4

Objectif : ajouter le code département à chaque ligne des 3 datasets
en utilisant les coordonnées GPS et reverse_geocoder,
afin de créer des liens FK vers la table departement.
"""

import pandas as pd
from reverse_geocoder import search as rg_search

# ============================================================
# 1. CHARGEMENT DES 3 SOURCES NETTOYÉES
# ============================================================
df_gan = pd.read_csv("data/processed/gan_clean.csv")
df_villes = pd.read_csv("data/processed/villes_clean.csv")
df_meteorites = pd.read_csv("data/processed/meteorites_clean.csv")

print(f"GaN : {len(df_gan)} lignes")
print(f"Villes : {len(df_villes)} lignes")
print(f"Météorites : {len(df_meteorites)} lignes")

# ============================================================
# 2. FONCTION D'ENRICHISSEMENT
# reverse_geocoder retourne un dict avec 'admin2' = département
# ============================================================
def ajouter_code_dep(df):
    coords = list(zip(df["latitude"], df["longitude"]))
    resultats = rg_search(coords)
    df = df.copy()
    df["nom_dep"] = [r["admin2"] for r in resultats]
    return df

print("\nEnrichissement en cours...")

df_gan = ajouter_code_dep(df_gan)
df_villes = ajouter_code_dep(df_villes)
df_meteorites = ajouter_code_dep(df_meteorites)

# ============================================================
# 3. VÉRIFICATION
# ============================================================
print("\n--- Aperçu GaN ---")
print(df_gan[["latitude", "longitude", "nom_dep"]].head())

print("\n--- Aperçu Villes ---")
print(df_villes[["ville", "latitude", "longitude", "nom_dep"]].head())

print("\n--- Aperçu Météorites ---")
print(df_meteorites[["name", "latitude", "longitude", "nom_dep"]].head())

# ============================================================
# 4. EXPORT
# ============================================================
df_gan.to_csv("data/processed/gan_enrichi.csv", index=False)
df_villes.to_csv("data/processed/villes_enrichies.csv", index=False)
df_meteorites.to_csv("data/processed/meteorites_enrichies.csv", index=False)

print("\n✅ Export réussi :")
print("  - data/processed/gan_enrichi.csv")
print("  - data/processed/villes_enrichies.csv")
print("  - data/processed/meteorites_enrichies.csv")
