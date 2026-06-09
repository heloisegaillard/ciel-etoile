"""
C2 - Requêtes SQL d'extraction sur la BDD unifiée
Compétences : C2

Objectif : extraire des données utiles au projet via des requêtes
SQL complexes avec JOIN sur les 4 tables de la BDD unifiée.
"""

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pandas as pd

# ============================================================
# CONNEXION
# ============================================================
load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
engine = create_engine(DB_URL)

# ============================================================
# REQUÊTE 1 - Départements avec le plus de villes étoilées
# et leur qualité moyenne de ciel (limiting_mag moyen)
# JOIN : departement + ville_etoilee + observation_gan
# ============================================================
requete_1 = """
SELECT
    d.code_dep,
    d.nom_dep,
    COUNT(DISTINCT v.id)        AS nb_villes_etoilees,
    COUNT(DISTINCT o.id)        AS nb_observations_gan,
    ROUND(AVG(o.limiting_mag)::numeric, 2) AS qualite_ciel_moy
FROM departement d
JOIN ville_etoilee v   ON v.code_dep = d.code_dep
JOIN observation_gan o ON o.code_dep = d.code_dep
GROUP BY d.code_dep, d.nom_dep
ORDER BY nb_villes_etoilees DESC, qualite_ciel_moy DESC
LIMIT 10;
"""

# ============================================================
# REQUÊTE 2 - Villes étoilées avec observations GaN
# et météorites dans le même département
# JOIN : les 4 tables
# ============================================================
requete_2 = """
SELECT
    v.ville,
    d.nom_dep,
    v.nombre_etoiles,
    COUNT(DISTINCT o.id)    AS nb_observations,
    ROUND(AVG(o.limiting_mag)::numeric, 2) AS limiting_mag_moy,
    COUNT(DISTINCT m.code)  AS nb_meteorites
FROM ville_etoilee v
JOIN departement d      ON v.code_dep = d.code_dep
JOIN observation_gan o  ON o.code_dep = d.code_dep
JOIN meteorite m        ON m.code_dep = d.code_dep
GROUP BY v.ville, d.nom_dep, v.nombre_etoiles
ORDER BY v.nombre_etoiles DESC, limiting_mag_moy DESC
LIMIT 10;
"""

# ============================================================
# REQUÊTE 3 - Meilleurs départements pour observer le ciel
# Score combiné : étoiles + qualité GaN + présence météorites
# JOIN : les 4 tables
# ============================================================
requete_3 = """
SELECT
    d.code_dep,
    d.nom_dep,
    COUNT(DISTINCT v.id)                            AS nb_villes_etoilees,
    ROUND(AVG(v.nombre_etoiles)::numeric, 2)        AS moy_etoiles,
    ROUND(AVG(o.limiting_mag)::numeric, 2)          AS qualite_ciel_moy,
    COUNT(DISTINCT m.code)                          AS nb_meteorites,
    ROUND((AVG(v.nombre_etoiles) * 10 +
           AVG(o.limiting_mag) * 5)::numeric, 2)    AS score_observation
FROM departement d
JOIN ville_etoilee v   ON v.code_dep = d.code_dep
JOIN observation_gan o ON o.code_dep = d.code_dep
LEFT JOIN meteorite m  ON m.code_dep = d.code_dep
GROUP BY d.code_dep, d.nom_dep
ORDER BY score_observation DESC
LIMIT 10;
"""

# ============================================================
# EXÉCUTION ET AFFICHAGE
# ============================================================
with engine.connect() as conn:
    print("=== REQUÊTE 1 : Top départements villes étoilées + qualité ciel ===\n")
    df1 = pd.read_sql(text(requete_1), conn)
    print(df1.to_string(index=False))

    print("\n=== REQUÊTE 2 : Villes étoilées avec observations et météorites ===\n")
    df2 = pd.read_sql(text(requete_2), conn)
    print(df2.to_string(index=False))

    print("\n=== REQUÊTE 3 : Score meilleurs départements pour observer ===\n")
    df3 = pd.read_sql(text(requete_3), conn)
    print(df3.to_string(index=False))

print("\n✅ Requêtes C2 exécutées avec succès !")
