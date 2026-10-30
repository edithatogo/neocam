"""Independent birth-table reconciliation using only Polars as a DataFrame engine."""

import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
# Published Queensland 2022 birth-table expectations pinned to the source CSV.
EXPECTED_ROWS = 72
EXPECTED_BIRTHS = 46711


def main() -> int:
    """Check native CSV parsing, types, row count and null/duplicate behaviour.

    Returns:
        int: 1 when any reconciliation check fails, otherwise 0.
    """
    table = pl.read_csv(ROOT / "data/births_queensland_2022.csv")
    errors: list[str] = []
    if table.height != EXPECTED_ROWS:
        errors.append(f"Source row count differs from {EXPECTED_ROWS}")
    if table["births"].sum() != EXPECTED_BIRTHS:
        errors.append(f"Public birth total differs from {EXPECTED_BIRTHS}")
    if table["facility"].n_unique() != table.height:
        errors.append("Duplicate source facility")
    if table.select(pl.all().null_count()).row(0) != (0,) * table.width:
        errors.append("Unexpected null input")
    if set(table["year"].to_list()) != {2022}:
        errors.append("Wrong source year")
    print(json.dumps({"engine": "polars", "version": pl.__version__, "errors": errors}, indent=2))  # ruff: ignore[print] -- standalone probe emits its JSON report to stdout
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
