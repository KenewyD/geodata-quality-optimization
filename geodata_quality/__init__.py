# -*- coding: utf-8 -*-
"""
GeoData Quality & Optimization Platform
Plugin QGIS de contrôle qualité géométrique et d'optimisation PostGIS.
"""


def classFactory(iface):  # pragma: no cover - QGIS entry point
    """Load the plugin class.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .plugin import GeoDataQualityPlugin

    return GeoDataQualityPlugin(iface)
