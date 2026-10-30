# ruff: ignore[implicit-namespace-package] -- standalone reproducibility driver, not a package module
"""One local entry point for current analysis, reporting and byte-level provenance."""

import argparse
from pathlib import Path

from quality.artifacts import seal, verify
from scripts.analyse_v7 import main as analyse
from scripts.build_current_report import build
from scripts.plot_current import main as plot

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Run analysis, plotting, report build, sealing and verification in order.

    Raises:
        RuntimeError: If post-build byte-level verification reports errors.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config/reference.json")
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/v12")
    parser.add_argument("--office", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "outputs"):
        parser.error("Current release output must remain under repository outputs")
    analyse(args.config, output)
    plot(output)
    build(output, office=args.office)
    seal(ROOT, output)
    errors = verify(ROOT, output)
    if errors:
        raise RuntimeError(errors)


if __name__ == "__main__":
    main()
