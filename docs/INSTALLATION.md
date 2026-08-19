# Installation

## Prérequis

- QGIS 3.28 LTR ou supérieur
- Une base PostgreSQL/PostGIS accessible (pour les modules d'optimisation)
- Python 3.10+ (fourni par QGIS)

## Installation depuis un ZIP (recommandé)

1. Téléchargez la dernière archive `geodata_quality-x.y.z.zip` depuis la page
   [Releases](https://github.com/kdiallo/geodata-quality-optimization/releases).
2. Dans QGIS : **Extensions → Installer/Gérer les extensions → Installer depuis un ZIP**.
3. Sélectionnez le fichier ZIP téléchargé, puis **Installer l'extension**.
4. Activez « GeoData Quality & Optimization » dans la liste des extensions.

L'outil apparaît dans la barre d'outils et dans le menu **Vecteur → GeoData Quality**.

## Installation manuelle (développement)

```bash
git clone https://github.com/kdiallo/geodata-quality-optimization.git
# Copiez (ou liez) le dossier du plugin dans le répertoire des extensions QGIS :
#   Linux   : ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
#   Windows : %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
#   macOS   : ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
cp -r geodata_quality <chemin_plugins_qgis>/
```

Relancez QGIS puis activez l'extension.

## Dépendances Python supplémentaires

Le cœur qualité utilise **Shapely** (généralement déjà fourni avec QGIS). Les modules
PostGIS utilisent **psycopg2**. Si nécessaire :

```bash
pip install shapely psycopg2-binary
```

## Génération de données de test et benchmark

```bash
pip install -r requirements-dev.txt
python scripts/generate_test_data.py --dsn "dbname=gis user=postgres host=localhost" --rows 10000000
python scripts/run_benchmark.py --dsn "dbname=gis user=postgres host=localhost"
```
