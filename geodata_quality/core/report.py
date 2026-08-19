# -*- coding: utf-8 -*-
"""
Génération de rapports de contrôle qualité.

Produit un résumé structuré (comptes par type d'anomalie) et un rapport HTML
lisible, exportable pour la collectivité utilisatrice.
"""

from __future__ import annotations

import html
from collections import Counter
from datetime import datetime
from typing import Dict, List

from .quality_checks import Issue


def summarize(issues: List[Issue]) -> Dict[str, int]:
    """Compte les anomalies par type de contrôle."""
    counter = Counter(issue.check for issue in issues)
    return dict(sorted(counter.items(), key=lambda kv: kv[1], reverse=True))


def to_html(issues: List[Issue], layer_name: str = "couche") -> str:
    """Construit un rapport HTML simple et autoportant."""
    summary = summarize(issues)
    total = len(issues)
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    rows = "".join(
        f"<tr><td>{html.escape(check)}</td><td>{count}</td></tr>"
        for check, count in summary.items()
    )

    detail_rows = "".join(
        f"<tr><td>{html.escape(str(i.feature_id))}</td>"
        f"<td>{html.escape(i.check)}</td>"
        f"<td>{html.escape(i.message)}</td></tr>"
        for i in issues[:1000]  # borne pour ne pas générer un HTML géant
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Rapport qualité - {html.escape(layer_name)}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; color: #1a1a1a; }}
  h1 {{ font-size: 1.4rem; }}
  table {{ border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
  th {{ background: #f0f0f0; }}
  .total {{ font-weight: 600; }}
</style>
</head>
<body>
  <h1>Rapport de contrôle qualité</h1>
  <p>Couche&nbsp;: <strong>{html.escape(layer_name)}</strong><br>
     Généré le&nbsp;: {generated}</p>
  <p class="total">Total d'anomalies&nbsp;: {total}</p>
  <h2>Synthèse par type</h2>
  <table>
    <tr><th>Contrôle</th><th>Nombre</th></tr>
    {rows or '<tr><td colspan="2">Aucune anomalie 🎉</td></tr>'}
  </table>
  <h2>Détail (1000 premières)</h2>
  <table>
    <tr><th>ID entité</th><th>Contrôle</th><th>Message</th></tr>
    {detail_rows}
  </table>
</body>
</html>"""
