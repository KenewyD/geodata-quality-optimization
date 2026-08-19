# -*- coding: utf-8 -*-
"""
Dialogue principal du plugin.

L'interface visuelle est définie dans quality_dialog.ui (Qt Designer). Ici on
la charge avec uic.loadUi et on connecte les widgets à la logique métier.
La logique lourde (analyse) est lancée dans un QgsTask pour ne pas geler QGIS.
"""

from __future__ import annotations

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QMessageBox

FORM_CLASS, _ = uic.loadUiType(
    os.path.join(os.path.dirname(__file__), "quality_dialog.ui")
)


class QualityDialog(QDialog, FORM_CLASS):
    """Fenêtre de configuration et d'exécution des contrôles qualité."""

    def __init__(self, iface, parent=None):
        super().__init__(parent)
        # setupUi vient de la classe générée à partir du .ui
        self.setupUi(self)
        self.iface = iface
        self._last_issues = []
        self._last_layer_name = ""

        self.runButton.clicked.connect(self.on_run)
        self.exportButton.clicked.connect(self.on_export)
        self.closeButton.clicked.connect(self.close)

        self._populate_connections()

    # ---- Configuration UI ------------------------------------------------ #

    def _populate_connections(self):
        """Charge les connexions PostGIS enregistrées dans QGIS."""
        try:
            from qgis.core import QgsProviderRegistry

            md = QgsProviderRegistry.instance().providerMetadata("postgres")
            if md is not None:
                for name in md.connections().keys():
                    self.connCombo.addItem(name)
        except Exception:
            # En environnement sans connexions configurées, on n'échoue pas.
            pass

    def selected_checks(self):
        """Renvoie le dictionnaire {contrôle: activé} depuis les cases."""
        return {
            "invalid_geometry": self.chkInvalid.isChecked(),
            "empty_geometry": self.chkEmpty.isChecked(),
            "duplicate_geometry": self.chkDuplicate.isChecked(),
            "multipart_geometry": self.chkMultipart.isChecked(),
            "self_intersection": self.chkSelfIntersect.isChecked(),
            "overlap": self.chkOverlap.isChecked(),
            "crs": self.chkCrs.isChecked(),
            "missing_attribute": self.chkAttributes.isChecked(),
        }

    # ---- Actions --------------------------------------------------------- #

    def on_run(self):
        """Lance l'analyse dans un QgsTask pour garder l'UI réactive."""
        layer = self.layerCombo.currentLayer()
        if layer is None:
            QMessageBox.warning(self, "Attention", "Sélectionnez une couche.")
            return

        required = [f.strip() for f in self.reqEdit.text().split(",") if f.strip()]
        expected_crs = self.crsEdit.text().strip() or None
        enabled = self.selected_checks()

        self.progressBar.setValue(0)
        self.resultsText.clear()

        # Import local pour éviter de dépendre de QGIS à l'import du module
        # (utile pour les tests unitaires de la logique métier).
        from ..core.analysis_task import QualityAnalysisTask
        from qgis.core import QgsApplication

        task = QualityAnalysisTask(
            layer=layer,
            required_fields=required,
            expected_crs=expected_crs,
            enabled=enabled,
        )
        task.progressChanged.connect(
            lambda: self.progressBar.setValue(int(task.progress()))
        )
        task.taskCompleted.connect(lambda: self._on_task_done(task))
        task.taskTerminated.connect(
            lambda: self.resultsText.append("Analyse interrompue.")
        )
        self._last_layer_name = layer.name()
        QgsApplication.taskManager().addTask(task)

    def _on_task_done(self, task):
        """Callback exécuté à la fin de l'analyse (thread principal)."""
        from ..core.report import summarize

        self._last_issues = task.issues
        self.progressBar.setValue(100)
        summary = summarize(task.issues)
        if not summary:
            self.resultsText.append("Aucune anomalie détectée ✅")
            return
        self.resultsText.append(f"{len(task.issues)} anomalie(s) détectée(s) :\n")
        for check, count in summary.items():
            self.resultsText.append(f"  • {check} : {count}")

    def on_export(self):
        """Exporte le dernier rapport en HTML."""
        if not self._last_issues:
            QMessageBox.information(self, "Rapport", "Aucun résultat à exporter.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Enregistrer le rapport", "rapport_qualite.html", "HTML (*.html)"
        )
        if not path:
            return
        from ..core.report import to_html

        with open(path, "w", encoding="utf-8") as fh:
            fh.write(to_html(self._last_issues, self._last_layer_name))
        QMessageBox.information(self, "Rapport", f"Rapport enregistré :\n{path}")
