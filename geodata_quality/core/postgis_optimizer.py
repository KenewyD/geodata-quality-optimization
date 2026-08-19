# -*- coding: utf-8 -*-
"""
Module d'analyse et d'optimisation PostGIS.

Objectif : mesurer et améliorer les performances de requêtes spatiales sur de
gros volumes (plusieurs millions d'objets), en s'appuyant sur :
  - les index spatiaux GiST ;
  - EXPLAIN (ANALYZE, BUFFERS) pour lire les plans d'exécution réels ;
  - un banc de test (benchmark) reproductible.

IMPORTANT : ce module exécute de vraies requêtes. Les temps mesurés dépendent
de VOTRE matériel et de VOS données. Les chiffres publiés dans le README
doivent provenir de vos propres exécutions, jamais d'estimations.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    from psycopg2 import sql
except ImportError:  # pragma: no cover - psycopg2 optionnel pour les tests
    psycopg2 = None
    sql = None


@dataclass
class BenchmarkResult:
    """Résultat d'une mesure de performance sur une requête."""

    label: str
    duration_s: float
    plan: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "duration_s": round(self.duration_s, 4),
            "plan": self.plan,
        }


class PostGISConnection:
    """Enveloppe simple autour d'une connexion psycopg2.

    Utilisable comme context manager pour garantir la fermeture propre.
    """

    def __init__(self, dsn: str):
        if psycopg2 is None:
            raise RuntimeError(
                "psycopg2 est requis pour les opérations PostGIS. "
                "Installez psycopg2-binary."
            )
        self.dsn = dsn
        self._conn = None

    def __enter__(self) -> "PostGISConnection":
        self._conn = psycopg2.connect(self.dsn)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            raise RuntimeError("Connexion non ouverte. Utilisez 'with'.")
        return self._conn

    def execute(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            if cur.description:
                return cur.fetchall()
            return []


def get_execution_plan(
    connection: PostGISConnection, query: str, params: Optional[Tuple] = None
) -> str:
    """Renvoie le plan d'exécution réel via EXPLAIN (ANALYZE, BUFFERS).

    ANALYZE exécute réellement la requête et donne les temps mesurés (et pas
    seulement l'estimation du planificateur). BUFFERS montre les accès disque
    vs cache, utile pour comprendre les gains d'un index.
    """
    explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT) {query}"
    rows = connection.execute(explain_query, params)
    return "\n".join(row[0] for row in rows)


def has_spatial_index(
    connection: PostGISConnection, table: str, geom_column: str = "geom"
) -> bool:
    """Indique si un index existe déjà sur la colonne géométrique."""
    q = """
        SELECT COUNT(*)
        FROM pg_indexes
        WHERE tablename = %s
          AND indexdef ILIKE %s
    """
    rows = connection.execute(q, (table, f"%{geom_column}%"))
    return bool(rows and rows[0][0] > 0)


def create_spatial_index(
    connection: PostGISConnection,
    table: str,
    geom_column: str = "geom",
    index_name: Optional[str] = None,
) -> str:
    """Crée un index spatial GiST sur la colonne géométrique.

    GiST (Generalized Search Tree) est le type d'index utilisé par PostGIS
    pour accélérer les opérateurs spatiaux (&&, ST_Intersects, ST_DWithin...).
    Sans lui, PostgreSQL fait un balayage séquentiel (Seq Scan) de toute la
    table : catastrophique sur plusieurs millions de lignes.
    """
    index_name = index_name or f"{table}_{geom_column}_gist_idx"
    query = sql.SQL(
        "CREATE INDEX IF NOT EXISTS {idx} ON {tbl} USING GIST ({col})"
    ).format(
        idx=sql.Identifier(index_name),
        tbl=sql.Identifier(table),
        col=sql.Identifier(geom_column),
    )
    with connection.conn.cursor() as cur:
        cur.execute(query)
    connection.conn.commit()
    # ANALYZE met à jour les statistiques pour que le planificateur
    # sache qu'il peut/doit utiliser le nouvel index.
    with connection.conn.cursor() as cur:
        cur.execute(sql.SQL("ANALYZE {tbl}").format(tbl=sql.Identifier(table)))
    connection.conn.commit()
    return index_name


def drop_spatial_index(connection: PostGISConnection, index_name: str) -> None:
    """Supprime un index (utile pour mesurer le "avant" dans un benchmark)."""
    with connection.conn.cursor() as cur:
        cur.execute(
            sql.SQL("DROP INDEX IF EXISTS {idx}").format(idx=sql.Identifier(index_name))
        )
    connection.conn.commit()


def time_query(
    connection: PostGISConnection,
    query: str,
    params: Optional[Tuple] = None,
    label: str = "query",
    capture_plan: bool = True,
) -> BenchmarkResult:
    """Mesure le temps d'exécution d'une requête et capture son plan.

    On mesure le temps côté client (time.perf_counter). Pour une mesure fine
    du temps serveur seul, on lit aussi 'Execution Time' dans le plan ANALYZE.
    """
    plan = None
    if capture_plan:
        plan = get_execution_plan(connection, query, params)

    start = time.perf_counter()
    connection.execute(query, params)
    duration = time.perf_counter() - start

    return BenchmarkResult(label=label, duration_s=duration, plan=plan)


def benchmark_before_after_index(
    connection: PostGISConnection,
    table: str,
    query: str,
    geom_column: str = "geom",
    params: Optional[Tuple] = None,
) -> Dict[str, BenchmarkResult]:
    """Compare une requête sans index puis avec index GiST.

    Séquence :
      1. supprime l'index s'il existe ;
      2. mesure la requête (Seq Scan attendu) ;
      3. crée l'index GiST ;
      4. mesure de nouveau la requête (Index Scan attendu).

    Renvoie les deux BenchmarkResult pour publication/rapport.
    À n'exécuter que sur un environnement de test, pas en production.
    """
    index_name = f"{table}_{geom_column}_gist_idx"

    drop_spatial_index(connection, index_name)
    before = time_query(connection, query, params, label="sans_index")

    create_spatial_index(connection, table, geom_column, index_name)
    after = time_query(connection, query, params, label="avec_index_gist")

    return {"before": before, "after": after}
