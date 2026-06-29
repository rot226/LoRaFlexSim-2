"""Export CSV des résultats de brouillage."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Mapping, Any


def export_jamming_rows(rows: list[Mapping[str, Any]], output_csv: str | Path) -> Path:
    """Écrit des lignes de métriques de brouillage dans un CSV."""

    path = Path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path
