import argparse
import logging
import os

try:
    import pandas as pd  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    pd = None


LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS = ("PDR", "SF", "airtime")


def _validate_row(row: "pd.Series", line_number: int) -> list[str]:
    """Return validation errors for a given CSV row."""
    errors: list[str] = []

    def _parse_float(column: str) -> float | None:
        raw = row.get(column)
        if raw is None:
            errors.append(f"colonne '{column}' absente")
            return None
        raw_str = str(raw).strip()
        if raw_str == "":
            errors.append(f"colonne '{column}' vide")
            return None
        try:
            return float(raw_str)
        except ValueError:
            errors.append(f"colonne '{column}' non numérique: {raw_str!r}")
            return None

    pdr = _parse_float("PDR")
    sf = _parse_float("SF")
    airtime = _parse_float("airtime")

    if pdr is not None and not (0.0 <= pdr <= 1.0):
        errors.append(f"PDR hors bornes [0,1]: {pdr}")
    if sf is not None:
        if not sf.is_integer():
            errors.append(f"SF doit être entier: {sf}")
        elif not (7 <= int(sf) <= 12):
            errors.append(f"SF hors bornes [7,12]: {int(sf)}")
    if airtime is not None and airtime < 0.0:
        errors.append(f"airtime doit être >= 0: {airtime}")

    if errors:
        LOGGER.warning(
            "Ligne %d rejetée (%s). Données: %s",
            line_number,
            "; ".join(errors),
            row.to_dict(),
        )

    return errors


def clean_csv(input_path: str, output_path: str | None = None) -> str:
    """Load CSV file, clean it and save to new file.

    Parameters
    ----------
    input_path : str
        Path to CSV file to clean.
    output_path : str | None
        Destination path for cleaned CSV. If None, ``input_path`` is used with
        ``_clean`` suffix.

    Returns
    -------
    str
        Path to the cleaned CSV file on disk.
    """
    if pd is None:
        raise RuntimeError("pandas is required to clean CSV files")

    df = pd.read_csv(input_path, dtype=str)

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "Colonnes obligatoires manquantes: " + ", ".join(missing_columns)
        )

    valid_rows: list["pd.Series"] = []
    rejected_count = 0
    for idx, row in df.iterrows():
        line_number = idx + 2  # +1 for header, +1 for 1-indexing
        if _validate_row(row, line_number):
            rejected_count += 1
            continue
        valid_rows.append(row)

    if valid_rows:
        df = pd.DataFrame(valid_rows, columns=df.columns)
    else:
        df = pd.DataFrame(columns=df.columns)

    # Drop exact duplicate rows among valid entries only
    df = df.drop_duplicates()

    # If an ``event_id`` column exists, sort by it for consistency
    if "event_id" in df.columns:
        df = df.sort_values(by="event_id")
    else:
        df = df.sort_index()

    cleaned_path = (
        output_path if output_path is not None else os.path.splitext(input_path)[0] + "_clean.csv"
    )
    df.to_csv(cleaned_path, index=False)

    LOGGER.info(
        "Validation CSV terminée: %d ligne(s) valide(s), %d rejetée(s).",
        len(df),
        rejected_count,
    )

    return cleaned_path


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Nettoie un fichier CSV de résultats")
    parser.add_argument("csv_file", help="Chemin du fichier CSV à nettoyer")
    parser.add_argument(
        "--output",
        "-o",
        help="Chemin du fichier nettoyé (par défaut <csv_file>_clean.csv)",
    )
    args = parser.parse_args()

    cleaned = clean_csv(args.csv_file, args.output)
    print(f"Fichier nettoyé enregistré dans {cleaned}")


if __name__ == "__main__":
    main()
