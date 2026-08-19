# -*- coding: utf-8 -*-
"""
Exécute le benchmark de performance PostGIS et affiche des résultats RÉELS.

Compare la même requête spatiale :
  1. sans index (Seq Scan) ;
  2. avec index GiST (Index Scan).

Affiche les temps mesurés et les plans EXPLAIN ANALYZE. Copiez ces vrais
chiffres dans docs/PERFORMANCE.md — ne les inventez jamais.

Usage :
    python scripts/run_benchmark.py \
        --dsn "dbname=gis user=postgres password=postgres host=localhost"
"""

from __future__ import annotations

import argparse

# Import du module métier du plugin
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from geodata_quality.core.postgis_optimizer import (  # noqa: E402
    PostGISConnection,
    benchmark_before_after_index,
)

# Requête de test : combien de parcelles intersectent une fenêtre donnée.
# ST_Intersects utilise l'index GiST via l'opérateur && sous-jacent.
TEST_QUERY = """
    SELECT COUNT(*)
    FROM parcelles_test
    WHERE ST_Intersects(
        geom,
        ST_MakeEnvelope(750000, 6650000, 760000, 6660000, 2154)
    );
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True)
    args = parser.parse_args()

    with PostGISConnection(args.dsn) as conn:
        print("Lancement du benchmark (sans index puis avec index GiST)…\n")
        results = benchmark_before_after_index(
            conn,
            table="parcelles_test",
            query=TEST_QUERY,
            geom_column="geom",
        )

        before = results["before"]
        after = results["after"]

        print("=" * 60)
        print(f"SANS INDEX    : {before.duration_s:.4f} s")
        print(f"AVEC INDEX GiST: {after.duration_s:.4f} s")
        if after.duration_s > 0:
            speedup = before.duration_s / after.duration_s
            print(f"Gain          : x{speedup:.1f}")
        print("=" * 60)

        print("\n--- PLAN SANS INDEX ---")
        print(before.plan)
        print("\n--- PLAN AVEC INDEX GiST ---")
        print(after.plan)


if __name__ == "__main__":
    main()
