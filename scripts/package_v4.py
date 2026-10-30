# ruff: ignore[implicit-namespace-package] -- standalone packaging script, not a package module
"""Create a versioned Git-backed source archive, bundle and portable skill package."""

import argparse
import hashlib
import json
import subprocess  # ruff: ignore[suspicious-subprocess-import] -- sealing archives with fixed git commands
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def package(destination: Path) -> dict:
    """Build and verify the project archives, then return the package manifest.

    Returns:
        Manifest with the resolved commit, archive digests and remote-push status.

    Raises:
        ValueError: If a written archive fails its integrity test.
    """
    destination.mkdir(parents=True, exist_ok=True)
    project = destination / "Panda_Vision_project_v4.zip"
    bundle = destination / "Panda_Vision_project_v4.bundle"
    subprocess.run(["git", "archive", "--format=zip", f"--output={project}", "HEAD"], cwd=ROOT, check=True)  # ruff: ignore[subprocess-without-shell-equals-true, start-process-with-partial-path] -- fixed git command, shell disabled
    subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=ROOT, check=True)  # ruff: ignore[subprocess-without-shell-equals-true, start-process-with-partial-path] -- fixed git command, shell disabled
    subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=ROOT, check=True, capture_output=True)  # ruff: ignore[subprocess-without-shell-equals-true, start-process-with-partial-path] -- fixed git command, shell disabled
    skill = destination / "maintaining-lean-ci_skill_v1.zip"
    skillroot = ROOT / ".agents/skills/maintaining-lean-ci"
    with zipfile.ZipFile(skill, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(skillroot.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                z.write(path, Path("maintaining-lean-ci") / path.relative_to(skillroot))
    plots = destination / "Panda_Vision_plots_tables_v4.zip"
    with zipfile.ZipFile(plots, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted((ROOT / "outputs/v4").rglob("*")):
            if path.is_file() and path.suffix in {".csv", ".png", ".svg", ".json"}:
                z.write(path, path.relative_to(ROOT / "outputs/v4"))
    for path in (project, skill, plots):
        with zipfile.ZipFile(path) as z:
            if z.testzip() is not None:
                msg = f"Archive integrity failure: {path}"
                raise ValueError(msg)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],  # ruff: ignore[start-process-with-partial-path] -- fixed git command, not user input
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    report = {
        "commit": commit,
        "archives": {
            p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
            for p in (project, bundle, skill, plots)
        },
        "git_submodule": "gitlink only; initialise separately with network access",
        "remote_push": False,
    }
    (destination / "Panda_Vision_package_manifest_v4.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path("/mnt/data"))
    print(json.dumps(package(parser.parse_args().destination), indent=2))  # ruff: ignore[print] -- CLI manifest report goes to stdout
