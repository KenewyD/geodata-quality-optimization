# -*- coding: utf-8 -*-
"""
Contrôles qualité géométriques.

Ce module est volontairement écrit en Python pur (Shapely) et découplé de
l'API QGIS. Cela permet :
  - de tester chaque contrôle avec pytest sans lancer QGIS ;
  - de réutiliser la logique côté serveur (batch, PostGIS) ;
  - de garder une séparation nette entre logique métier et interface (UI).

Chaque contrôle prend en entrée une liste de "features" (dictionnaires
{'id': ..., 'geometry': <shapely geom>, 'attributes': {...}}) et renvoie une
liste d'anomalies décrivant le problème trouvé.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

from shapely.geometry.base import BaseGeometry
from shapely.validation import explain_validity


@dataclass
class Issue:
    """Une anomalie détectée sur une entité."""

    feature_id: Any
    check: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "check": self.check,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class Feature:
    """Représentation minimale et neutre d'une entité géographique."""

    id: Any
    geometry: Optional[BaseGeometry]
    attributes: Dict[str, Any] = field(default_factory=dict)


# --------------------------------------------------------------------------- #
# Contrôles unitaires
# --------------------------------------------------------------------------- #


def check_invalid_geometries(features: Iterable[Feature]) -> List[Issue]:
    """Détecte les géométries topologiquement invalides.

    Une géométrie invalide est par exemple un polygone dont le contour se
    recoupe. Shapely s'appuie sur GEOS pour cette validation ; explain_validity
    donne la raison exacte, utile pour le rapport et pour le débogage.
    """
    issues: List[Issue] = []
    for feat in features:
        geom = feat.geometry
        if geom is None:
            continue
        if not geom.is_valid:
            issues.append(
                Issue(
                    feature_id=feat.id,
                    check="invalid_geometry",
                    message="Géométrie invalide",
                    details={"reason": explain_validity(geom)},
                )
            )
    return issues


def check_empty_geometries(features: Iterable[Feature]) -> List[Issue]:
    """Détecte les géométries nulles ou vides."""
    issues: List[Issue] = []
    for feat in features:
        geom = feat.geometry
        if geom is None or geom.is_empty:
            issues.append(
                Issue(
                    feature_id=feat.id,
                    check="empty_geometry",
                    message="Géométrie vide ou nulle",
                )
            )
    return issues


def check_multipart_geometries(features: Iterable[Feature]) -> List[Issue]:
    """Signale les géométries multi-parties (MultiPolygon, MultiLineString...).

    Ce n'est pas toujours une erreur, mais dans beaucoup de jeux cadastraux on
    attend une entité = une parcelle. On le remonte donc comme avertissement.
    """
    issues: List[Issue] = []
    multipart_types = {"MultiPolygon", "MultiLineString", "MultiPoint"}
    for feat in features:
        geom = feat.geometry
        if geom is None:
            continue
        if geom.geom_type in multipart_types and len(geom.geoms) > 1:
            issues.append(
                Issue(
                    feature_id=feat.id,
                    check="multipart_geometry",
                    message="Géométrie multi-parties",
                    details={"parts": len(geom.geoms)},
                )
            )
    return issues


def check_self_intersections(features: Iterable[Feature]) -> List[Issue]:
    """Détecte les auto-intersections.

    Une auto-intersection rend un polygone invalide. On la traite séparément
    du contrôle générique d'invalidité pour produire un message explicite.
    """
    issues: List[Issue] = []
    for feat in features:
        geom = feat.geometry
        if geom is None or geom.is_empty:
            continue
        reason = explain_validity(geom)
        if "Self-intersection" in reason:
            issues.append(
                Issue(
                    feature_id=feat.id,
                    check="self_intersection",
                    message="Auto-intersection détectée",
                    details={"reason": reason},
                )
            )
    return issues


def check_missing_attributes(
    features: Iterable[Feature], required_fields: Iterable[str]
) -> List[Issue]:
    """Vérifie la présence et la non-nullité des attributs obligatoires."""
    required = list(required_fields)
    issues: List[Issue] = []
    for feat in features:
        missing = [
            f
            for f in required
            if f not in feat.attributes or feat.attributes[f] in (None, "")
        ]
        if missing:
            issues.append(
                Issue(
                    feature_id=feat.id,
                    check="missing_attribute",
                    message="Attribut(s) obligatoire(s) manquant(s)",
                    details={"fields": missing},
                )
            )
    return issues


def check_duplicate_geometries(features: Iterable[Feature]) -> List[Issue]:
    """Détecte les doublons géométriques exacts.

    On utilise le WKB comme clé de hachage : deux géométries strictement
    identiques produisent le même WKB. Complexité O(n) en moyenne grâce au
    dictionnaire, ce qui reste raisonnable sur de gros volumes.
    """
    seen: Dict[bytes, Any] = {}
    issues: List[Issue] = []
    for feat in features:
        geom = feat.geometry
        if geom is None or geom.is_empty:
            continue
        key = geom.wkb
        if key in seen:
            issues.append(
                Issue(
                    feature_id=feat.id,
                    check="duplicate_geometry",
                    message="Doublon géométrique",
                    details={"duplicate_of": seen[key]},
                )
            )
        else:
            seen[key] = feat.id
    return issues


def check_crs(features_crs: Optional[str], expected_crs: str) -> List[Issue]:
    """Vérifie que le CRS de la couche correspond au CRS attendu.

    Contrôle simple mais fréquent : une couche dans le mauvais système de
    projection fausse toutes les analyses de distance/surface.
    """
    if features_crs is None:
        return [
            Issue(
                feature_id=None,
                check="crs",
                message="CRS non défini sur la couche",
            )
        ]
    if features_crs.upper() != expected_crs.upper():
        return [
            Issue(
                feature_id=None,
                check="crs",
                message="CRS inattendu",
                details={"found": features_crs, "expected": expected_crs},
            )
        ]
    return []


def check_overlaps(features: List[Feature]) -> List[Issue]:
    """Détecte les chevauchements entre polygones.

    Implémentation naïve O(n²) pour la clarté pédagogique. Pour de gros
    volumes, ce contrôle doit être délégué à PostGIS (voir postgis_optimizer),
    qui utilise un index spatial GiST. On garde cette version pour les tests
    et les petits jeux de données.
    """
    issues: List[Issue] = []
    polys = [f for f in features if f.geometry is not None and not f.geometry.is_empty]
    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            a, b = polys[i].geometry, polys[j].geometry
            if a.overlaps(b):
                issues.append(
                    Issue(
                        feature_id=polys[i].id,
                        check="overlap",
                        message="Chevauchement de géométries",
                        details={"with": polys[j].id},
                    )
                )
    return issues


# --------------------------------------------------------------------------- #
# Orchestrateur
# --------------------------------------------------------------------------- #


def run_all_checks(
    features: List[Feature],
    required_fields: Optional[List[str]] = None,
    layer_crs: Optional[str] = None,
    expected_crs: Optional[str] = None,
    enabled: Optional[Dict[str, bool]] = None,
) -> List[Issue]:
    """Exécute l'ensemble des contrôles activés et agrège les anomalies.

    :param enabled: dictionnaire {nom_du_controle: bool}. Si None, tout est
                    activé. Permet à l'UI de laisser l'utilisateur choisir.
    """
    enabled = enabled or {}

    def on(name: str) -> bool:
        return enabled.get(name, True)

    issues: List[Issue] = []
    if on("invalid_geometry"):
        issues += check_invalid_geometries(features)
    if on("empty_geometry"):
        issues += check_empty_geometries(features)
    if on("multipart_geometry"):
        issues += check_multipart_geometries(features)
    if on("self_intersection"):
        issues += check_self_intersections(features)
    if on("duplicate_geometry"):
        issues += check_duplicate_geometries(features)
    if on("overlap"):
        issues += check_overlaps(features)
    if on("missing_attribute") and required_fields:
        issues += check_missing_attributes(features, required_fields)
    if on("crs") and expected_crs:
        issues += check_crs(layer_crs, expected_crs)
    return issues
