"""
Étape 2 - Création et import de la BDD météorites
Compétences : C4

Objectif : créer la table meteorite dans PostgreSQL
et importer les données du CSV meteorite_fr.csv

Source : Meteoritical Bulletin Database
MCD : une entité METEORITE avec code comme clé primaire
"""

import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# ============================================================
# 1. CONNEXION À LA BASE DE DONNÉES
# ============================================================
load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

engine = create_engine(DB_URL)
print("✅ Connexion à PostgreSQL réussie")

# ============================================================
# 2. CRÉATION DE LA TABLE
# ============================================================
create_table_sql = """
CREATE TABLE IF NOT EXISTS meteorite (
    code        INTEGER PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    status      VARCHAR(50),
    fall        VARCHAR(10),
    year        INTEGER,
    place       VARCHAR(255),
    type        VARCHAR(50),
    mass        FLOAT,
    met_bull    INTEGER,
    antarctic   VARCHAR(10),
    latitude    FLOAT,
    longitude   FLOAT,
    comment     TEXT
);
"""

with engine.connect() as conn:
    conn.execute(text(create_table_sql))
    conn.commit()

print("✅ Table meteorite créée")

# ============================================================
# 3. CHARGEMENT ET NETTOYAGE DU CSV
# ============================================================
df = pd.read_csv("data/raw/meteorite_fr.csv")

print(f"\nDataset chargé : {len(df)} météorites")
print(f"Colonnes : {df.columns.tolist()}")

# Renommage des colonnes pour correspondre à la table SQL
df = df.rename(columns={
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

# Colonnes à importer (correspondant à la table)
colonnes_table = [
    "code", "name", "status", "fall", "year",
    "place", "type", "mass", "met_bull",
    "antarctic", "latitude", "longitude", "comment"
]
df = df[colonnes_table]

# Nettoyage des valeurs manquantes
print("\n--- Valeurs manquantes ---")
print(df.isnull().sum())

# ============================================================
# 4. IMPORT EN BASE DE DONNÉES
# ============================================================
df.to_sql(
    name="meteorite",
    con=engine,
    if_exists="replace",
    index=False
)

print(f"\n✅ Import réussi : {len(df)} météorites importées dans PostgreSQL")

# ============================================================
# 5. VÉRIFICATION
# ============================================================
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM meteorite"))
    count = result.fetchone()[0]
    print(f"✅ Vérification : {count} enregistrements dans la table")
