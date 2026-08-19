# Performance & optimisation PostGIS

Ce document présente la méthodologie et les résultats du banc de test
d'optimisation des requêtes spatiales.

> ⚠️ **À COMPLÉTER AVEC VOS PROPRES MESURES.**
> Les tableaux ci-dessous contiennent des emplacements `__ à remplir __`.
> Exécutez `scripts/run_benchmark.py` sur votre machine et reportez les chiffres
> réels. N'inventez jamais de valeurs : un recruteur peut demander à reproduire.

## Environnement de test

| Élément | Valeur |
|---|---|
| Machine (CPU / RAM) | __ à remplir __ |
| Version PostgreSQL | __ à remplir __ |
| Version PostGIS | __ à remplir __ |
| Nombre de lignes | __ à remplir (ex. 10 000 000) __ |
| Table | `parcelles_test` (polygones, EPSG:2154) |

## Méthodologie

1. Générer le jeu de test : `python scripts/generate_test_data.py --rows 10000000`.
2. Lancer le benchmark : `python scripts/run_benchmark.py --dsn "…"`.
   Le script mesure la même requête (1) sans index puis (2) avec index GiST,
   et capture les plans via `EXPLAIN (ANALYZE, BUFFERS)`.
3. (Optionnel) Étape d'optimisation SQL supplémentaire : filtrage par bounding
   box, `ST_DWithin` au lieu de `ST_Distance`, `VACUUM ANALYZE`.

## Requête testée

```sql
SELECT COUNT(*)
FROM parcelles_test
WHERE ST_Intersects(
    geom,
    ST_MakeEnvelope(750000, 6650000, 760000, 6660000, 2154)
);
```

## Résultats

| Étape | Temps mesuré | Type de scan | Gain |
|---|---|---|---|
| Avant optimisation (sans index) | __ X s __ | Seq Scan | référence |
| Après index GiST | __ Y s __ | Index Scan | __ ×? __ |
| Après optimisation SQL | __ Z s __ | Index Scan | __ ×? __ |

## Lecture des plans EXPLAIN ANALYZE

### Sans index (attendu : Seq Scan)

```
__ coller ici la sortie réelle du plan "sans index" __
```

Points à commenter :
- présence d'un **Seq Scan** (balayage complet de la table) ;
- valeur de `actual time` et de `rows` ;
- coût élevé proportionnel au nombre total de lignes.

### Avec index GiST (attendu : Index Scan)

```
__ coller ici la sortie réelle du plan "avec index" __
```

Points à commenter :
- passage à un **Index Scan** utilisant l'index GiST ;
- forte réduction du `actual time` ;
- moins de blocs lus (`BUFFERS`) grâce à l'index.

## Enseignements

- L'opérateur `ST_Intersects` s'appuie sur l'opérateur de bounding box `&&`, qui
  n'est accéléré **que** si un index spatial GiST existe sur la colonne géométrique.
- Sans index, le coût croît linéairement avec la volumétrie ; avec index, il devient
  quasi logarithmique pour des requêtes sélectives.
- `ANALYZE` après création de l'index est indispensable : sans statistiques à jour,
  le planificateur peut ignorer l'index.
- Pour les requêtes de distance, `ST_DWithin(a, b, d)` est préférable à
  `ST_Distance(a, b) < d` car seule la première est « sargable » (utilise l'index).
