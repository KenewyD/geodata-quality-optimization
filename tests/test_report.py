# -*- coding: utf-8 -*-
"""Tests du module de rapport."""

from geodata_quality.core.quality_checks import Issue
from geodata_quality.core.report import summarize, to_html


def _issues():
    return [
        Issue(feature_id=1, check="invalid_geometry", message="x"),
        Issue(feature_id=2, check="invalid_geometry", message="x"),
        Issue(feature_id=3, check="duplicate_geometry", message="x"),
    ]


def test_summarize_counts_by_check():
    summary = summarize(_issues())
    assert summary["invalid_geometry"] == 2
    assert summary["duplicate_geometry"] == 1


def test_to_html_contains_totals_and_is_valid_html():
    html_out = to_html(_issues(), layer_name="parcelles")
    assert "parcelles" in html_out
    assert "Total d'anomalies" in html_out
    assert html_out.strip().startswith("<!DOCTYPE html>")


def test_to_html_empty_issues():
    html_out = to_html([], layer_name="vide")
    assert "Aucune anomalie" in html_out
