# Guide personnel — mise en ligne & réponse au recruteur

## 1. Comprendre le projet AVANT de l'envoyer

Le recruteur peut te demander d'expliquer ton code en entretien. Prends 1 à 2h
pour lire ces fichiers dans l'ordre et t'assurer que tu peux les expliquer :

1. `geodata_quality/core/quality_checks.py` — le cœur. Sache expliquer :
   - pourquoi une géométrie « nœud papillon » est invalide (contour qui se recoupe) ;
   - comment tu détectes les doublons (clé WKB dans un dictionnaire) ;
   - pourquoi le contrôle de chevauchement en O(n²) doit passer à PostGIS sur gros volume.
2. `geodata_quality/core/postgis_optimizer.py` — sache expliquer :
   - ce qu'est un index GiST et pourquoi il accélère `ST_Intersects` ;
   - ce que montre `EXPLAIN (ANALYZE, BUFFERS)` : Seq Scan vs Index Scan, actual time ;
   - pourquoi `ANALYZE` après création d'index est nécessaire.
3. `geodata_quality/ui/quality_dialog.py` — sache expliquer :
   - `uic.loadUiType` charge l'interface `.ui` faite dans Qt Designer ;
   - pourquoi le traitement tourne dans un `QgsTask` (ne pas geler QGIS).

## 2. Mettre en ligne sur GitHub

```bash
cd geodata_quality
git init
git add .
git commit -m "feat: version initiale du plugin GeoData Quality & Optimization"
git branch -M main
# Crée d'abord le dépôt vide 'geodata-quality-optimization' sur github.com
git remote add origin https://github.com/kdiallo/geodata-quality-optimization.git
git push -u origin main
```

Vérifie ensuite dans l'onglet **Actions** de GitHub que la CI passe au vert (elle
lance lint + tests + build automatiquement).

## 3. Faire de VRAIS benchmarks (le point qui fait la différence)

Sur une base PostGIS de test locale :

```bash
pip install -r requirements-dev.txt
python scripts/generate_test_data.py --dsn "dbname=gis user=postgres host=localhost" --rows 10000000
python scripts/run_benchmark.py --dsn "dbname=gis user=postgres host=localhost"
```

Copie les vrais chiffres et les vrais plans dans `docs/PERFORMANCE.md`
(remplace tous les `__ à remplir __`). **N'invente aucun chiffre.**

Si tu n'as pas de PostGIS sous la main, commence avec `--rows 500000` : le
principe (Seq Scan → Index Scan) se démontre déjà très bien.

## 4. Créer une release (pour le lien ZIP propre)

```bash
git tag v1.0.0
git push origin v1.0.0
```

Le workflow `release.yml` construit le ZIP et crée automatiquement la GitHub
Release avec le fichier téléchargeable.

## 5. Honnêteté = ta meilleure protection

- Ce projet est un **projet de démonstration récent** : assume-le comme tel.
  C'est parfaitement normal et valorisant d'avoir construit un projet vitrine.
- Ne prétends pas l'avoir déployé « en production sur 10M de parcelles » si ce
  n'est pas vrai. Dis : « J'ai conçu ce plugin pour démontrer une chaîne complète,
  testée sur un jeu généré de N millions d'objets. »
- Tout ce que le projet contient, tu dois pouvoir l'expliquer et le refaire.
