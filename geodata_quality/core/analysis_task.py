# -*- coding: utf-8 -*-
"""
Tâche d'analyse exécutée en arrière-plan via QgsTask.

QgsTask permet d'exécuter un traitement long dans un thread séparé sans geler
l'interface de QGIS, tout en remontant la progression. C'est la bonne pratique
recommandée par la documentation QGIS pour tout traitement non instantané.

Ce module dépend de QGIS ; il n'est donc pas testé unitairement directement.
La logique métier qu'il appelle (core.quality_checks) l'est, elle, entièrement.
"""

from __future__ import annotations

from typing import Dict, List, Optional

try:
    from qgis.core import QgsTask
    from shapely import wkb

    _QGIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    QgsTask = object  # type: ignore
    _QGIS_AVAILABLE = False

from .quality_checks import Feature, Issue, run_all_checks


class QualityAnalysisTask(QgsTask):
    """Exécute les contrôles qualité sur une couche QGIS en tâche de fond."""

    def __init__(
        self,
        layer,
        required_fields: Optional[List[str]] = None,
        expected_crs: Optional[str] = None,
        enabled: Optional[Dict[str, bool]] = None,
    ):
        super().__init__("Analyse qualité géométrique", QgsTask.CanCancel)
        self.layer = layer
        self.required_fields = required_fields or []
        self.expected_crs = expected_crs
        self.enabled = enabled or {}
        self.issues: List[Issue] = []
        self._exception = None

    def run(self) -> bool:
        """Corps de la tâche (exécuté dans un thread worker).

        Ne jamais toucher à l'UI ici : uniquement du calcul. On convertit les
        entités QGIS en objets Feature neutres, puis on délègue à la logique
        métier testée.
        """
        try:
            features = self._collect_features()
            layer_crs = (
                self.layer.crs().authid() if self.layer.crs().isValid() else None
            )
            self.issues = run_all_checks(
                features,
                required_fields=self.required_fields,
                layer_crs=layer_crs,
                expected_crs=self.expected_crs,
                enabled=self.enabled,
            )
            return True
        except Exception as exc:  # pragma: no cover
            self._exception = exc
            return False

    def _collect_features(self) -> List[Feature]:
        """Convertit les entités QGIS en Feature (géométrie Shapely + attributs)."""
        features: List[Feature] = []
        total = self.layer.featureCount() or 1
        field_names = [f.name() for f in self.layer.fields()]

        for i, qgis_feat in enumerate(self.layer.getFeatures()):
            if self.isCanceled():
                return features
            geom = qgis_feat.geometry()
            shp = None
            if geom is not None and not geom.isEmpty():
                shp = wkb.loads(bytes(geom.asWkb()))
            attrs = {name: qgis_feat[name] for name in field_names}
            features.append(Feature(id=qgis_feat.id(), geometry=shp, attributes=attrs))

            if i % 1000 == 0:
                self.setProgress(min(99.0, (i / total) * 100.0))
        return features

    def finished(self, result: bool) -> None:  # pragma: no cover
        """Appelé dans le thread principal à la fin de run()."""
        if not result and self._exception is not None:
            from qgis.core import QgsMessageLog, Qgis

            QgsMessageLog.logMessage(
                f"Erreur d'analyse : {self._exception}",
                "GeoDataQuality",
                Qgis.Critical,
            )
