"""Export CSV des résultats de brouillage."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping, Any


def export_jamming_rows(rows: list[Mapping[str, Any]], output_csv: str | Path) -> Path:
    """Écrit des lignes de métriques de brouillage dans un CSV."""

    path = Path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_rows = []
    for row in rows:
        normalized = dict(row)
        if "scenario_name" not in normalized:
            normalized["scenario_name"] = normalized.get("scenario", normalized.get("name", ""))
        normalized_rows.append(normalized)

    fieldnames = sorted({key for row in normalized_rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(normalized_rows)
    return path
