# -*- coding: utf-8 -*-
"""
Génère un jeu de test volumineux dans PostGIS pour les benchmarks.

Crée une table de N polygones (par défaut 10 millions) simulant des parcelles
cadastrales réparties sur une emprise. Utilise generate_series côté serveur
pour rester rapide et éviter des millions d'INSERT côté client.

Usage :
    python scripts/generate_test_data.py \
        --dsn "dbname=gis user=postgres password=postgres host=localhost" \
        --rows 10000000

ATTENTION : à exécuter sur une base de TEST. Consomme de l'espace disque.
"""

from __future__ import annotations

import argparse
import time

import psycopg2

DDL = """
DROP TABLE IF EXISTS parcelles_test;
CREATE TABLE parcelles_test (
    id      bigserial PRIMARY KEY,
    code    text,
    surface double precision,
    geom    geometry(Polygon, 2154)
);
"""

# Génère des petits carrés répartis sur une grille dans l'emprise Lambert-93.
# On construit la géométrie côté serveur : bien plus rapide que côté client.
INSERT = """
INSERT INTO parcelles_test (code, surface, geom)
SELECT
    'P' || g,
    100.0 + (g %% 900),
    ST_SetSRID(
        ST_MakeEnvelope(
            x, y, x + 20, y + 20
        ),
        2154
    )
FROM generate_series(1, %(rows)s) AS g,
LATERAL (
    SELECT
        700000 + ((g * 23) %% 400000) AS x,
        6600000 + ((g * 37) %% 400000) AS y
) AS coords;
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dsn", required=True, help="Chaîne de connexion psycopg2")
    parser.add_argument("--rows", type=int, default=10_000_000)
    args = parser.parse_args()

    conn = psycopg2.connect(args.dsn)
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            print("Création de l'extension PostGIS si nécessaire…")
            cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            print("Création de la table…")
            cur.execute(DDL)
            print(
                f"Insertion de {args.rows:,} lignes (peut prendre plusieurs minutes)…"
            )
            start = time.perf_counter()
            cur.execute(INSERT, {"rows": args.rows})
            elapsed = time.perf_counter() - start
            print(f"Terminé en {elapsed:.1f} s.")
            cur.execute("SELECT COUNT(*) FROM parcelles_test;")
            print("Lignes réelles :", cur.fetchone()[0])
    finally:
        conn.close()


if __name__ == "__main__":
    main()
