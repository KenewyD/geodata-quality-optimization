# -*- coding: utf-8 -*-
"""Logique métier découplée de QGIS (contrôles qualité + optimisation PostGIS)."""

from .quality_checks import (
    Feature,
    Issue,
    run_all_checks,
)

__all__ = ["Feature", "Issue", "run_all_checks"]
