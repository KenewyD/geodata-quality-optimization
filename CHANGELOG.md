# Changelog

Toutes les modifications notables de ce projet sont documentées ici.
Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/)
et le projet applique le [versionnage sémantique](https://semver.org/lang/fr/).

## [1.0.0] - 2026-08-19

### Ajouté
- Interface Qt (Qt Designer + PyQt5) intégrée à QGIS avec sélection de couche,
  connexion PostGIS, paramétrage des contrôles, barre de progression et export.
- Module de contrôle qualité géométrique : géométries invalides, vides, doublons,
  multi-parties, auto-intersections, chevauchements, CRS, attributs obligatoires.
- Module d'analyse et d'optimisation PostGIS : index GiST, EXPLAIN ANALYZE,
  benchmark avant/après index.
- Exécution en arrière-plan via QgsTask (interface non bloquante).
- Génération de rapport HTML.
- Scripts de génération de données de test (jusqu'à 10M d'objets) et de benchmark.
- Suite de tests pytest (17 tests) et intégration continue GitHub Actions.
- Packaging ZIP installable et workflow de release automatique.
