"""Profile the active v6 exact model; historical ML remains optional."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.pathways_v6 import compare_v6, sample_v6  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path
from src.statewide import load_sites, select_sites  # ruff: ignore[module-import-not-at-top-of-file] -- import requires ROOT on sys.path


def main() -> None:
    """Profile representative spoke-site draws and print their mean net saving."""
    sites = select_sites(load_sites(), "spokes")
    for seed in (20261027, 20261028, 20261029):
        x, e = sample_v6(n=50000, seed=seed)
        result = compare_v6(sites, inputs=x, structural_draws=e)
        print(result["panda"]["net_saving"].mean())  # ruff: ignore[print] -- profiling figure is this script's stdout output


if __name__ == "__main__":
    main()
