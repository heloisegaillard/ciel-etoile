"""
Étape 4 - Création de la BDD unifiée
Compétences : C4

Objectif : créer les 4 tables liées dans PostgreSQL
et importer les 3 sources enrichies avec leurs FK département.

MCD :
- DEPARTEMENT (code_dep PK)
- VILLE_ETOILEE (id PK, code_dep FK)
- OBSERVATION_GAN (id PK, code_dep FK)
- METEORITE (code PK, code_dep FK)
"""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import unicodedata

# ============================================================
# 1. CONNEXION
# ============================================================
load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DB_URL)
print("✅ Connexion PostgreSQL réussie")

# ============================================================
# 2. FONCTION DE NORMALISATION
# Pour faire correspondre les noms de reverse_geocoder
# avec les noms INSEE (accents, casse, préfixes...)
# ============================================================
def normaliser(texte):
    if not isinstance(texte, str):
        return ""
    texte = texte.lower().strip()
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    # Supprimer les préfixes courants
    for prefixe in ["departement du ", "departement de la ", "departement de l'",
                     "departement des ", "departement de ", "departement d'"]:
        if texte.startswith(prefixe):
            texte = texte[len(prefixe):]
            break
    return texte.strip()

# ============================================================
# 3. CHARGEMENT DES DONNÉES
# ============================================================
df_deps = pd.read_csv("data/raw/departements_insee.csv", dtype={"code": str})
df_gan = pd.read_csv("data/processed/gan_enrichi.csv")
df_villes = pd.read_csv("data/processed/villes_enrichies.csv")
df_meteorites = pd.read_csv("data/processed/meteorites_enrichies.csv")

# ============================================================
# 4. CONSTRUCTION DU DICTIONNAIRE DE CORRESPONDANCE
# nom normalisé → code INSEE
# ============================================================
dict_deps = {normaliser(row["nom"]): row["code"] for _, row in df_deps.iterrows()}

def get_code_dep(nom_dep):
    return dict_deps.get(normaliser(nom_dep), None)

# Ajout du code_dep dans les 3 datasets
df_gan["code_dep"] = df_gan["nom_dep"].apply(get_code_dep)
df_villes["code_dep"] = df_villes["nom_dep"].apply(get_code_dep)
df_meteorites["code_dep"] = df_meteorites["nom_dep"].apply(get_code_dep)

# Vérification des non-matchés
print("\n--- Non matchés GaN ---")
print(df_gan[df_gan["code_dep"].isna()]["nom_dep"].unique())
print("--- Non matchés Villes ---")
print(df_villes[df_villes["code_dep"].isna()]["nom_dep"].unique())
print("--- Non matchés Météorites ---")
print(df_meteorites[df_meteorites["code_dep"].isna()]["nom_dep"].unique())

# ============================================================
# 5. SUPPRESSION DES LIGNES HORS FRANCE MÉTROPOLITAINE/DOM
# ============================================================
df_gan = df_gan.dropna(subset=["code_dep"])
df_villes = df_villes.dropna(subset=["code_dep"])
df_meteorites = df_meteorites.dropna(subset=["code_dep"])

print(f"\nAprès nettoyage FK :")
print(f"  GaN : {len(df_gan)} observations")
print(f"  Villes : {len(df_villes)} communes")
print(f"  Météorites : {len(df_meteorites)} météorites")

# ============================================================
# 6. CRÉATION DES TABLES
# ============================================================
sql_tables = """
DROP TABLE IF EXISTS observation_gan CASCADE;
DROP TABLE IF EXISTS ville_etoilee CASCADE;
DROP TABLE IF EXISTS meteorite CASCADE;
DROP TABLE IF EXISTS departement CASCADE;

CREATE TABLE departement (
    code_dep    VARCHAR(3) PRIMARY KEY,
    nom_dep     VARCHAR(100) NOT NULL
);

CREATE TABLE ville_etoilee (
    id              SERIAL PRIMARY KEY,
    ville           VARCHAR(100),
    code_dep        VARCHAR(3) REFERENCES departement(code_dep),
    region          VARCHAR(100),
    nombre_etoiles  INTEGER,
    latitude        FLOAT,
    longitude       FLOAT
);

CREATE TABLE observation_gan (
    id              SERIAL PRIMARY KEY,
    latitude        FLOAT,
    longitude       FLOAT,
    elevation       FLOAT,
    local_date      DATE,
    local_time      TIME,
    limiting_mag    FLOAT,
    sqm_reading     FLOAT,
    cloud_cover     VARCHAR(50),
    constellation   VARCHAR(50),
    code_dep        VARCHAR(3) REFERENCES departement(code_dep)
);

CREATE TABLE meteorite (
    code        INTEGER PRIMARY KEY,
    name        VARCHAR(255),
    status      VARCHAR(50),
    fall        VARCHAR(10),
    year        FLOAT,
    place       VARCHAR(255),
    type        VARCHAR(50),
    mass        FLOAT,
    latitude    FLOAT,
    longitude   FLOAT,
    comment     TEXT,
    code_dep    VARCHAR(3) REFERENCES departement(code_dep)
);
"""

with engine.connect() as conn:
    conn.execute(text(sql_tables))
    conn.commit()
print("\n✅ Tables créées")


# Départements
df_deps_import = df_deps.rename(columns={"code": "code_dep", "nom": "nom_dep"})
df_deps_import.to_sql("departement", engine, if_exists="append", index=False)
print(f"✅ {len(df_deps_import)} départements importés")

# Villes étoilées
cols_villes = ["ville", "code_dep", "region", "nombre_etoiles", "latitude", "longitude"]
df_villes[cols_villes].to_sql("ville_etoilee", engine, if_exists="append", index=False)
print(f"✅ {len(df_villes)} villes étoilées importées")

# Observations GaN
cols_gan = ["latitude", "longitude", "elevation", "local_date", "local_time",
            "limiting_mag", "sqm_reading", "cloud_cover", "constellation", "code_dep"]
df_gan[cols_gan].to_sql("observation_gan", engine, if_exists="append", index=False)
print(f"✅ {len(df_gan)} observations GaN importées")

# Météorites
cols_met = ["code", "name", "status", "fall", "year", "place",
            "type", "mass", "latitude", "longitude", "comment", "code_dep"]
df_meteorites[cols_met].to_sql("meteorite", engine, if_exists="append", index=False)
print(f"✅ {len(df_meteorites)} météorites importées")

# ============================================================
# 8. VÉRIFICATION FINALE
# ============================================================
with engine.connect() as conn:
    for table in ["departement", "ville_etoilee", "observation_gan", "meteorite"]:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).fetchone()[0]
        print(f"  {table} : {count} enregistrements")

print("\n✅ BDD unifiée créée avec succès !")
