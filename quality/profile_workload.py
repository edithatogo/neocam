"""Existing PSA workload for CPU/memory profiling; no new model scenarios."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.statewide import load_sites, select_sites, psa


def main() -> None:
    """Profile the current statewide reference structure with a fixed seed."""
    sites = select_sites(load_sites(), 'spokes')
    for seed in (20261027, 20261028, 20261029):
        result = psa(sites, n=50000, seed=seed)
        print(result['summary']['mean'])


if __name__ == '__main__':
    main()
