from __future__ import annotations

import logging

import pandas as pd
import pytest

from loraflexsim.launcher.clean_results import clean_csv


def test_clean_csv_rejects_invalid_rows_and_logs_details(tmp_path, caplog):
    input_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"

    input_csv.write_text(
        "PDR,SF,airtime,event_id\n"
        "0.8,7,0.12,1\n"
        "1.2,8,0.11,2\n"  # PDR hors bornes
        "0.5,13,0.10,3\n"  # SF hors bornes
        "0.4,9,-0.10,4\n"  # airtime négatif
        "abc,10,0.20,5\n"  # PDR non numérique
        "0.6,8,0.09,6\n",
        encoding="utf-8",
    )

    with caplog.at_level(logging.WARNING):
        clean_csv(str(input_csv), str(output_csv))

    df = pd.read_csv(output_csv)
    assert len(df) == 2
    assert set(df["event_id"].tolist()) == {1, 6}
    assert "Ligne 3 rejetée" in caplog.text
    assert "PDR hors bornes [0,1]: 1.2" in caplog.text
    assert "SF hors bornes [7,12]: 13" in caplog.text
    assert "airtime doit être >= 0: -0.1" in caplog.text
    assert "colonne 'PDR' non numérique" in caplog.text


def test_clean_csv_fails_when_required_columns_are_missing(tmp_path):
    input_csv = tmp_path / "missing_cols.csv"
    input_csv.write_text("PDR,SF\n0.9,7\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Colonnes obligatoires manquantes: airtime"):
        clean_csv(str(input_csv))
