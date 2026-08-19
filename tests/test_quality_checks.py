# -*- coding: utf-8 -*-
"""
Tests unitaires des contrôles qualité géométriques.

Ces tests s'exécutent sans QGIS ni PostGIS : ils valident la logique métier
pure (module core.quality_checks) avec des géométries Shapely construites à la
main. C'est ce qui rend le cœur du plugin réellement testable en CI.
"""

from shapely.geometry import Polygon, MultiPolygon

from geodata_quality.core.quality_checks import (
    Feature,
    check_invalid_geometries,
    check_empty_geometries,
    check_duplicate_geometries,
    check_multipart_geometries,
    check_self_intersections,
    check_missing_attributes,
    check_crs,
    check_overlaps,
    run_all_checks,
)


def _valid_square(offset=0.0):
    return Polygon(
        [
            (offset, offset),
            (offset + 1, offset),
            (offset + 1, offset + 1),
            (offset, offset + 1),
        ]
    )


def test_valid_geometry_produces_no_issue():
    feats = [Feature(id=1, geometry=_valid_square())]
    assert check_invalid_geometries(feats) == []


def test_invalid_bowtie_is_detected():
    # "Nœud papillon" : contour qui se recoupe -> polygone invalide.
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    feats = [Feature(id=1, geometry=bowtie)]
    issues = check_invalid_geometries(feats)
    assert len(issues) == 1
    assert issues[0].check == "invalid_geometry"


def test_self_intersection_detected():
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    feats = [Feature(id=7, geometry=bowtie)]
    issues = check_self_intersections(feats)
    assert len(issues) == 1
    assert issues[0].feature_id == 7


def test_empty_geometry_detected():
    feats = [
        Feature(id=1, geometry=Polygon()),
        Feature(id=2, geometry=None),
        Feature(id=3, geometry=_valid_square()),
    ]
    issues = check_empty_geometries(feats)
    ids = {i.feature_id for i in issues}
    assert ids == {1, 2}


def test_duplicate_geometry_detected():
    sq = _valid_square()
    feats = [
        Feature(id=1, geometry=sq),
        Feature(id=2, geometry=_valid_square()),  # identique
        Feature(id=3, geometry=_valid_square(offset=5)),  # différent
    ]
    issues = check_duplicate_geometries(feats)
    assert len(issues) == 1
    assert issues[0].feature_id == 2
    assert issues[0].details["duplicate_of"] == 1


def test_multipart_detected():
    mp = MultiPolygon([_valid_square(), _valid_square(offset=5)])
    feats = [Feature(id=1, geometry=mp)]
    issues = check_multipart_geometries(feats)
    assert len(issues) == 1
    assert issues[0].details["parts"] == 2


def test_missing_attributes_detected():
    feats = [
        Feature(id=1, geometry=_valid_square(), attributes={"code": "A", "nom": ""}),
        Feature(id=2, geometry=_valid_square(), attributes={"code": "B", "nom": "X"}),
    ]
    issues = check_missing_attributes(feats, ["code", "nom"])
    assert len(issues) == 1
    assert issues[0].feature_id == 1
    assert issues[0].details["fields"] == ["nom"]


def test_crs_mismatch_detected():
    assert check_crs("EPSG:4326", "EPSG:2154")  # mismatch -> une anomalie
    assert check_crs("EPSG:2154", "EPSG:2154") == []  # ok
    assert check_crs(None, "EPSG:2154")  # CRS absent -> anomalie


def test_overlap_detected():
    a = _valid_square()
    b = _valid_square(offset=0.5)  # chevauche a
    feats = [Feature(id=1, geometry=a), Feature(id=2, geometry=b)]
    issues = check_overlaps(feats)
    assert len(issues) == 1


def test_run_all_checks_respects_enabled_flags():
    bowtie = Polygon([(0, 0), (1, 1), (1, 0), (0, 1)])
    feats = [Feature(id=1, geometry=bowtie)]
    # On désactive tout sauf invalid_geometry.
    enabled = {
        "empty_geometry": False,
        "duplicate_geometry": False,
        "multipart_geometry": False,
        "self_intersection": False,
        "overlap": False,
    }
    issues = run_all_checks(feats, enabled=enabled)
    checks = {i.check for i in issues}
    assert checks == {"invalid_geometry"}
