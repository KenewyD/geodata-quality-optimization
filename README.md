# GeoData Quality & Optimization Platform

Plugin QGIS professionnel de **contrôle qualité géométrique** et d'**optimisation de
requêtes spatiales PostGIS** sur de gros volumes (plusieurs millions d'objets, type
parcelles cadastrales).

[![CI](https://github.com/kdiallo/geodata-quality-optimization/actions/workflows/ci.yml/badge.svg)](https://github.com/kdiallo/geodata-quality-optimization/actions)

---

## Pourquoi ce projet

Une collectivité gérant plusieurs millions de parcelles a besoin de (1) garantir la
**qualité** de ses données géographiques et (2) que les analyses spatiales restent
**rapides**. Ce plugin répond aux deux : il audite les géométries et fournit un banc
de mesure démontrant l'impact des index spatiaux GiST et de l'optimisation SQL.

## Fonctionnalités

**1. Interface Qt (Qt Designer + PyQt5)**
Fenêtre intégrée à QGIS : sélection de couche (widget QGIS natif), choix de la
connexion PostGIS, paramétrage des contrôles, barre de progression, affichage et
export des résultats. Les traitements longs tournent dans un `QgsTask` (thread de
fond) pour ne jamais geler l'interface.

**2. Contrôle qualité géométrique**
Géométries invalides · vides · doublons · multi-parties · auto-intersections ·
chevauchements · problèmes de CRS · attributs obligatoires manquants. La logique est
en Python pur (Shapely/GEOS), **découplée de QGIS** et entièrement testée.

**3. Analyse & optimisation PostGIS**
Génération d'un jeu de test de plusieurs millions d'objets, requêtes spatiales
(`ST_Intersects`, `ST_DWithin`, `ST_Within`), création d'index **GiST**, lecture des
plans via `EXPLAIN (ANALYZE, BUFFERS)` et **benchmark avant/après** reproductible.

**4. Tests + CI/CD**
Tests unitaires `pytest` (logique géométrique et optimiseur mocké). Pipeline GitHub
Actions : lint (`flake8`), formatage (`black`), tests multi-versions Python, puis
build automatique du plugin à chaque `push`.

**5. Packaging / maintenance**
Plugin installable en ZIP, `metadata.txt` conforme, versionnage sémantique,
`CHANGELOG`, publication via **GitHub Releases**, gestion d'erreurs et logs QGIS.

## Architecture

```
geodata_quality/
├── __init__.py            # classFactory (point d'entrée QGIS)
├── plugin.py              # intégration menu / barre d'outils
├── metadata.txt           # métadonnées du plugin
├── ui/
│   ├── quality_dialog.ui  # interface Qt Designer
│   └── quality_dialog.py  # chargement UI + connexions signaux
├── core/                  # logique métier (testable sans QGIS)
│   ├── quality_checks.py  # contrôles géométriques (Shapely)
│   ├── postgis_optimizer.py  # index, EXPLAIN ANALYZE, benchmark
│   ├── analysis_task.py   # QgsTask d'exécution en arrière-plan
│   └── report.py          # génération de rapport HTML
tests/                     # pytest (17 tests)
scripts/                   # génération de données + benchmark + build
docs/                      # installation, performance, changelog
.github/workflows/         # CI + Release
```

Le principe directeur : **séparer la logique métier de l'UI QGIS**. Tout le cœur
(`core/`) se teste sans lancer QGIS, ce qui rend la CI simple et fiable.

## Installation

Voir [docs/INSTALLATION.md](docs/INSTALLATION.md). En résumé : téléchargez le ZIP
depuis les [Releases](https://github.com/kdiallo/geodata-quality-optimization/releases),
puis dans QGIS → Extensions → Installer depuis un ZIP.

## Performance

Le module d'optimisation mesure l'impact réel des index spatiaux. Voir
[docs/PERFORMANCE.md](docs/PERFORMANCE.md) pour la méthodologie et les résultats
mesurés (avant index / après index GiST / après optimisation SQL), plans
`EXPLAIN ANALYZE` à l'appui.

> Les chiffres publiés proviennent d'exécutions réelles via `scripts/run_benchmark.py`.

## Développement

```bash
pip install -r requirements-dev.txt
pytest tests/ -v            # tests
flake8 geodata_quality      # lint
black geodata_quality       # formatage
bash scripts/build_plugin.sh  # construire le ZIP
```

## Licence

GPL-2.0-or-later (compatible avec l'écosystème QGIS).

## Auteur

Kenewy Diallo — Géomaticienne Développeuse (Python, PyQGIS, PostGIS).
