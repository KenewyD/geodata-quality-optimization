# -*- coding: utf-8 -*-
"""
Tests du module d'optimisation PostGIS.

On ne dispose pas forcément d'une base PostGIS en CI ; on teste donc la logique
avec une connexion simulée (fake). Les tests d'intégration réels contre une
vraie base sont dans test_postgis_integration.py et ne s'exécutent que si la
variable d'environnement TEST_DSN est définie.
"""

from geodata_quality.core.postgis_optimizer import BenchmarkResult


class FakeConnection:
    """Simule PostGISConnection pour vérifier la logique sans vraie base."""

    def __init__(self, rows_by_query=None):
        self.rows_by_query = rows_by_query or {}
        self.executed = []

    def execute(self, query, params=None):
        self.executed.append(query.strip())
        for key, rows in self.rows_by_query.items():
            if key in query:
                return rows
        return []


def test_benchmark_result_as_dict_rounds_duration():
    res = BenchmarkResult(label="test", duration_s=1.234567, plan="PLAN")
    d = res.as_dict()
    assert d["label"] == "test"
    assert d["duration_s"] == 1.2346
    assert d["plan"] == "PLAN"


def test_has_spatial_index_true():
    from geodata_quality.core.postgis_optimizer import has_spatial_index

    conn = FakeConnection(rows_by_query={"pg_indexes": [(1,)]})
    assert has_spatial_index(conn, "parcelles_test", "geom") is True


def test_has_spatial_index_false():
    from geodata_quality.core.postgis_optimizer import has_spatial_index

    conn = FakeConnection(rows_by_query={"pg_indexes": [(0,)]})
    assert has_spatial_index(conn, "parcelles_test", "geom") is False


def test_get_execution_plan_joins_rows():
    from geodata_quality.core.postgis_optimizer import get_execution_plan

    conn = FakeConnection(rows_by_query={"EXPLAIN": [("Seq Scan",), ("  rows=100",)]})
    plan = get_execution_plan(conn, "SELECT 1")
    assert "Seq Scan" in plan
    assert "rows=100" in plan
