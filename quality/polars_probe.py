"""Independent birth-table reconciliation using only Polars as a DataFrame engine."""
from pathlib import Path
import json

import polars as pl

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    """Check native CSV parsing, types, row count and null/duplicate behaviour."""
    table = pl.read_csv(ROOT / 'data/births_queensland_2022.csv')
    errors: list[str] = []
    if table.height != 72:
        errors.append('Source row count differs from 72')
    if table['births'].sum() != 46711:
        errors.append('Public birth total differs from 46711')
    if table['facility'].n_unique() != table.height:
        errors.append('Duplicate source facility')
    if table.select(pl.all().null_count()).row(0) != (0,) * table.width:
        errors.append('Unexpected null input')
    if set(table['year'].to_list()) != {2022}:
        errors.append('Wrong source year')
    print(json.dumps({'engine': 'polars', 'version': pl.__version__, 'errors': errors}, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())
