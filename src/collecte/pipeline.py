"""
Pipeline de collecte automatisé - C1

Objectif : automatiser l'ensemble de la collecte et du
nettoyage des données en une seule commande.

Ordre d'exécution :
1. Filtrage GaN 2017 → France
2. Collecte API Datastro
3. Agrégation et nettoyage des 3 sources
4. Enrichissement géographique (code département)
"""

import subprocess
import sys

scripts = [
    ("Filtrage GaN",              "src/collecte/filtrage_gan.py"),
    ("Collecte API Datastro",     "src/collecte/api_datastro.py"),
    ("Agrégation des sources",    "src/collecte/agregation.py"),
    ("Enrichissement départements", "src/bdd/enrichissement_geodep.py"),
]

print("Démarrage du pipeline de collecte\n")

for nom, script in scripts:
    print(f" {nom}...")
    result = subprocess.run([sys.executable, script], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur dans {script} :\n{result.stderr}")
        sys.exit(1)
    print(f" {nom} terminé\n")

print(" Pipeline terminé — données prêtes pour la BDD !")
