"""
C5 - API REST de mise à disposition des données

Compétences : C1, C2, C3, C4, C5
Objectif : exposer les données de la BDD unifiée via une API REST
sécurisée, documentée et conforme OWASP.

Sécurité OWASP appliquée :
- Validation stricte de tous les paramètres d'entrée (type, taille, format)
- Limitation du nombre de résultats par requête (max 100)
- Headers de sécurité HTTP sur toutes les réponses
- Gestion globale des erreurs (400, 404, 422, 500)
- Authentification par clé API sur les endpoints sensibles
- CORS restreint aux méthodes GET uniquement
- Aucune donnée personnelle collectée ou exposée (RGPD)

Sources de données :
- Globe at Night 2017 (CC BY 4.0) : observations pollution lumineuse
- Villes et Villages Étoilés 2017 (Datastro / OpenDataSoft) : communes labellisées
- MetBull (Meteoritical Society) : météorites françaises, données publiques

Règles d'agrégation (C3) :
- Seules les entrées avec coordonnées GPS valides sont conservées
- Les entrées hors France métropolitaine et DOM sont exclues
- Le code département est déduit des coordonnées GPS via reverse_geocoder
- Le score d'observation combine moyenne d'étoiles (x10) et qualité ciel GaN (x5)
"""

from fastapi import FastAPI, HTTPException, Query, Depends, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os
import re

# ============================================================
# CONFIGURATION
# ============================================================
load_dotenv()

DB_URL = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
    f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

# Clé API — à stocker dans .env en production
API_KEY = os.getenv("API_KEY", "ciel-etoile-dev-key")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Connexion PostgreSQL réussie")
except SQLAlchemyError as e:
    print(f"❌ Impossible de se connecter à la BDD : {e}")
    raise

app = FastAPI(
    title="API Ciel Étoilé",
    description="""
## Présentation

API REST de mise à disposition des données sur la qualité
du ciel nocturne en France, dans le cadre du projet de certification
Développeur IA (Simplon).

## Sources de données (C2)

| Source | Organisme | Licence | Année |
|--------|-----------|---------|-------|
| Globe at Night | NOIRLab / NSF | CC BY 4.0 | 2017 |
| Villes et Villages Étoilés | Datastro / OpenDataSoft | Open Data | 2017 |
| Meteoritical Bulletin | Meteoritical Society | Publique | - |

## Règles d'agrégation appliquées (C3)

- Seules les observations avec coordonnées GPS valides sont conservées
- Les entrées hors France métropolitaine et DOM sont exclues
- Le code département est déduit des coordonnées GPS (reverse_geocoder)
- Le score d'observation = (moyenne étoiles × 10) + (qualité ciel × 5)

## RGPD

Aucune donnée personnelle n'est collectée, stockée ou exposée.
Toutes les données proviennent de sources publiques ouvertes.
L'API ne dépose aucun cookie et ne réalise aucun tracking.

## Sécurité (OWASP)

- Authentification par clé API (`X-API-Key` header)
- Validation stricte de tous les paramètres
- Limitation des résultats à 100 par requête
- Headers de sécurité HTTP sur toutes les réponses
    """,
    version="1.0.0",
    contact={
        "name": "Héloïse",
        "url": "https://github.com/heloisegaillard/ciel-etoile"
    },
    license_info={
        "name": "Données sources : CC BY 4.0 (Globe at Night)",
        "url": "https://creativecommons.org/licenses/by/4.0/"
    }
)

# ============================================================
# MIDDLEWARE CORS
# Restreint aux méthodes GET uniquement (OWASP)
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# ============================================================
# MIDDLEWARE HEADERS DE SÉCURITÉ (OWASP)
# Appliqués sur toutes les réponses
# ============================================================
@app.middleware("http")
async def ajouter_headers_securite(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["Cache-Control"] = "no-store"
    return response

# ============================================================
# GESTION GLOBALE DES ERREURS (C5)
# ============================================================
@app.exception_handler(SQLAlchemyError)
async def handler_erreur_bdd(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne de base de données. Veuillez réessayer."}
    )

@app.exception_handler(Exception)
async def handler_erreur_globale(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Erreur interne du serveur."}
    )

# ============================================================
# AUTHENTIFICATION PAR CLÉ API (OWASP)
# ============================================================
async def verifier_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(
            status_code=403,
            detail="Clé API invalide ou manquante. Fournir le header X-API-Key."
        )
    return key

# ============================================================
# VALIDATION DES PARAMÈTRES (OWASP)
# ============================================================
def valider_code_dep(code_dep: str) -> str:
    """Valide le format d'un code département INSEE (1-3 caractères alphanumériques)."""
    if not re.match(r"^[0-9A-Za-z]{1,3}$", code_dep):
        raise HTTPException(
            status_code=422,
            detail="Format de code département invalide. Exemple valide : 05, 75, 2A"
        )
    return code_dep.upper()

# ============================================================
# DÉPENDANCE : connexion BDD
# ============================================================
def get_db():
    try:
        with engine.connect() as conn:
            yield conn
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail="Connexion à la base de données impossible")

# ============================================================
# ENDPOINTS
# ============================================================

@app.get(
    "/",
    tags=["Info"],
    summary="Statut de l'API"
)
def accueil():
    """Point d'entrée — vérifie que le service est actif."""
    return {
        "status": "ok",
        "message": "API Ciel Étoilé opérationnelle",
        "version": "1.0.0",
        "documentation": "/docs",
        "rgpd": "Aucune donnée personnelle collectée ou exposée"
    }


@app.get(
    "/sources",
    tags=["Info"],
    summary="Documentation des sources de données (C2)"
)
def get_sources():
    """
    Retourne la documentation complète des 3 sources de données :
    origine, licence, année, transformations appliquées.
    """
    return {
        "sources": [
            {
                "nom": "Globe at Night 2017",
                "organisme": "NOIRLab / NSF",
                "url": "https://www.globeatnight.org/",
                "licence": "CC BY 4.0",
                "annee": 2017,
                "description": "Observations citoyennes mondiales de pollution lumineuse",
                "transformations": [
                    "Filtrage sur Country == France (426 → 425 observations)",
                    "Suppression colonnes non pertinentes (ID, UTDate, SQMSerial...)",
                    "1 entrée supprimée : coordonnées GPS hors France (Italie)"
                ]
            },
            {
                "nom": "Villes et Villages Étoilés 2017",
                "organisme": "Datastro / OpenDataSoft",
                "url": "https://datastro.aws-ec2-us-east-1.opendatasoft.com",
                "licence": "Open Data",
                "annee": 2017,
                "description": "Communes françaises labellisées pour la qualité de leur ciel nocturne",
                "transformations": [
                    "Collecte via API REST avec pagination (374 → 371 communes)",
                    "Séparation colonne geo en latitude/longitude",
                    "3 entrées supprimées : Réunion (DOM) hors périmètre"
                ]
            },
            {
                "nom": "Meteoritical Bulletin Database",
                "organisme": "Meteoritical Society",
                "url": "https://www.lpi.usra.edu/meteor/metbull.php",
                "licence": "Données publiques",
                "annee": "multiple",
                "description": "Météorites françaises répertoriées",
                "transformations": [
                    "Import CSV (94 → 92 météorites)",
                    "2 entrées supprimées : coordonnées GPS manquantes",
                    "2 entrées supprimées : hors France (Réunion, Nouvelle-Calédonie)"
                ]
            }
        ],
        "rgpd": "Aucune de ces sources ne contient de données personnelles.",
        "agregation": {
            "methode": "Lien géographique via code département INSEE",
            "outil": "reverse_geocoder (coordonnées GPS → département)",
            "score_observation": "score = (moyenne_etoiles × 10) + (qualite_ciel_gan × 5)"
        }
    }


@app.get(
    "/departements",
    tags=["Départements"],
    summary="Liste tous les départements"
)
def get_departements(
    db=Depends(get_db),
    api_key=Security(verifier_api_key)
):
    """Retourne la liste de tous les départements français disponibles dans la BDD."""
    rows = db.execute(
        text("SELECT code_dep, nom_dep FROM departement ORDER BY code_dep")
    ).fetchall()
    return [{"code_dep": r[0], "nom_dep": r[1]} for r in rows]


@app.get(
    "/departements/{code_dep}",
    tags=["Départements"],
    summary="Détail d'un département"
)
def get_departement(
    code_dep: str,
    db=Depends(get_db),
    api_key=Security(verifier_api_key)
):
    """Retourne les infos d'un département par son code INSEE (ex: 05, 75, 2A)."""
    code_dep = valider_code_dep(code_dep)
    row = db.execute(
        text("SELECT code_dep, nom_dep FROM departement WHERE code_dep = :code"),
        {"code": code_dep}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Département {code_dep} introuvable")
    return {"code_dep": row[0], "nom_dep": row[1]}


@app.get(
    "/villes",
    tags=["Villes étoilées"],
    summary="Liste les villes étoilées"
)
def get_villes(
    code_dep: str = Query(None, description="Filtrer par code département (ex: 05)"),
    nb_etoiles_min: int = Query(None, ge=1, le=5, description="Nombre d'étoiles minimum (1-5)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre de résultats (max 100)"),
    db=Depends(get_db),
    api_key=Security(verifier_api_key)
):
    """
    Retourne les villes et villages étoilés.
    Filtrables par département et nombre d'étoiles minimum.
    Résultats limités à 100 par requête.
    """
    query = """
        SELECT ville, code_dep, region, nombre_etoiles, latitude, longitude
        FROM ville_etoilee WHERE 1=1
    """
    params = {"limit": limit}

    if code_dep:
        code_dep = valider_code_dep(code_dep)
        query += " AND code_dep = :code_dep"
        params["code_dep"] = code_dep
    if nb_etoiles_min:
        query += " AND nombre_etoiles >= :nb_etoiles_min"
        params["nb_etoiles_min"] = nb_etoiles_min

    query += " ORDER BY nombre_etoiles DESC LIMIT :limit"
    rows = db.execute(text(query), params).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Aucune ville trouvée avec ces critères")

    return {
        "total": len(rows),
        "resultats": [
            {
                "ville": r[0], "code_dep": r[1], "region": r[2],
                "nombre_etoiles": r[3], "latitude": r[4], "longitude": r[5]
            }
            for r in rows
        ]
    }


@app.get(
    "/observations",
    tags=["Observations GaN"],
    summary="Liste les observations Globe at Night"
)
def get_observations(
    code_dep: str = Query(None, description="Filtrer par code département"),
    limiting_mag_min: float = Query(None, ge=1.0, le=7.0, description="Qualité ciel minimum (1-7)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre de résultats (max 100)"),
    db=Depends(get_db),
    api_key=Security(verifier_api_key)
):
    """
    Retourne les observations Globe at Night.
    Le champ limiting_mag indique la qualité du ciel :
    1 = très pollué, 7 = ciel parfait.
    """
    query = """
        SELECT id, latitude, longitude, local_date, limiting_mag,
               sqm_reading, cloud_cover, constellation, code_dep
        FROM observation_gan WHERE 1=1
    """
    params = {"limit": limit}

    if code_dep:
        code_dep = valider_code_dep(code_dep)
        query += " AND code_dep = :code_dep"
        params["code_dep"] = code_dep
    if limiting_mag_min:
        query += " AND limiting_mag >= :limiting_mag_min"
        params["limiting_mag_min"] = limiting_mag_min

    query += " ORDER BY limiting_mag DESC LIMIT :limit"
    rows = db.execute(text(query), params).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Aucune observation trouvée avec ces critères")

    return {
        "total": len(rows),
        "legende_limiting_mag": "1 = ciel très pollué, 7 = ciel parfait",
        "resultats": [
            {
                "id": r[0], "latitude": r[1], "longitude": r[2],
                "local_date": str(r[3]), "limiting_mag": r[4],
                "sqm_reading": r[5], "cloud_cover": r[6],
                "constellation": r[7], "code_dep": r[8]
            }
            for r in rows
        ]
    }


@app.get(
    "/meteorites",
    tags=["Météorites"],
    summary="Liste les météorites françaises"
)
def get_meteorites(
    code_dep: str = Query(None, description="Filtrer par code département"),
    limit: int = Query(20, ge=1, le=100, description="Nombre de résultats (max 100)"),
    db=Depends(get_db),
    api_key=Security(verifier_api_key)
):
    """Retourne les météorites françaises répertoriées dans MetBull."""
    query = """
        SELECT code, name, year, type, mass, latitude, longitude, code_dep
        FROM meteorite WHERE 1=1
    """
    params = {"limit": limit}

    if code_dep:
        code_dep = valider_code_dep(code_dep)
        query += " AND code_dep = :code_dep"
        params["code_dep"] = code_dep

    query += " ORDER BY year DESC NULLS LAST LIMIT :limit"
    rows = db.execute(text(query), params).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="Aucune météorite trouvée avec ces critères")

    return {
        "total": len(rows),
        "resultats": [
            {
                "code": r[0], "name": r[1], "year": r[2],
                "type": r[3], "mass_g": r[4],
                "latitude": r[5], "longitude": r[6], "code_dep": r[7]
            }
            for r in rows
        ]
    }


@app.get(
    "/score/{code_dep}",
    tags=["Score observation"],
    summary="Score d'observation d'un département"
)
def get_score(
    code_dep: str,
    db=Depends(get_db),
    api_key=Security(verifier_api_key)
):
    """
    Calcule le score d'observation nocturne d'un département.

    ## Règle d'agrégation (C3)
    Le score combine deux indicateurs de qualité du ciel :
    - **Moyenne des étoiles** des villes labellisées (pondération × 10)
    - **Qualité ciel moyenne** des observations GaN / limiting_mag (pondération × 5)

    `score = (moyenne_etoiles × 10) + (qualite_ciel_moy × 5)`

    Un score élevé indique un département propice à l'observation du ciel étoilé.
    """
    code_dep = valider_code_dep(code_dep)

    row = db.execute(text("""
        SELECT
            d.code_dep,
            d.nom_dep,
            COUNT(DISTINCT v.id)                            AS nb_villes,
            ROUND(AVG(v.nombre_etoiles)::numeric, 2)        AS moy_etoiles,
            ROUND(AVG(o.limiting_mag)::numeric, 2)          AS qualite_ciel,
            COUNT(DISTINCT m.code)                          AS nb_meteorites,
            ROUND((AVG(v.nombre_etoiles) * 10 +
                   AVG(o.limiting_mag) * 5)::numeric, 2)    AS score
        FROM departement d
        JOIN ville_etoilee v   ON v.code_dep = d.code_dep
        JOIN observation_gan o ON o.code_dep = d.code_dep
        LEFT JOIN meteorite m  ON m.code_dep = d.code_dep
        WHERE d.code_dep = :code_dep
        GROUP BY d.code_dep, d.nom_dep
    """), {"code_dep": code_dep}).fetchone()

    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"Aucune donnée disponible pour le département {code_dep}. "
                   f"Ce département ne contient peut-être pas de villes étoilées "
                   f"ou d'observations GaN."
        )

    return {
        "code_dep": row[0],
        "nom_dep": row[1],
        "nb_villes_etoilees": row[2],
        "moyenne_etoiles": float(row[3]),
        "qualite_ciel_moy": float(row[4]),
        "nb_meteorites": row[5],
        "score_observation": float(row[6]),
        "methode_calcul": "score = (moyenne_etoiles × 10) + (qualite_ciel_moy × 5)",
        "rgpd": "Aucune donnée personnelle dans cette réponse"
    }
