# -*- coding: utf-8 -*-
"""
Classe principale du plugin : intégration dans la barre d'outils et le menu.
"""

from __future__ import annotations

import os

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon


class GeoDataQualityPlugin:
    """Point d'entrée du plugin QGIS."""

    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        self.menu = "&GeoData Quality"

    def initGui(self):
        """Crée l'entrée de menu et le bouton de barre d'outils."""
        icon_path = os.path.join(os.path.dirname(__file__), "resources", "icon.png")
        self.action = QAction(
            QIcon(icon_path), "GeoData Quality & Optimization", self.iface.mainWindow()
        )
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToVectorMenu(self.menu, self.action)

    def unload(self):
        """Retire proprement les éléments d'interface au déchargement."""
        if self.action is not None:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginVectorMenu(self.menu, self.action)
            self.action = None

    def run(self):
        """Ouvre le dialogue principal."""
        from .ui.quality_dialog import QualityDialog

        if self.dialog is None:
            self.dialog = QualityDialog(self.iface, self.iface.mainWindow())
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()
