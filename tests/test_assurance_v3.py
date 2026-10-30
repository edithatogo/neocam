"""Test the evidence harness against real subprocesses and adversarial receipts."""

import sys
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest

from quality.assurance import Gate, input_fingerprint, run_gate, validate_receipts

if TYPE_CHECKING:
    from collections.abc import Callable

from quality.contracts import audit_inputs, forbidden_imports, forbidden_packages, validate_lock

# Deliberately invalid gate specifications must be validated by the gate itself.
_gate = cast("Callable[..., object]", Gate)


def make_receipt(tmp_path: Path):
    return run_gate(
        Gate("probe", (sys.executable, "-c", 'print("real execution")')), tmp_path, "abc", tmp_path / "logs"
    )


def test_real_success_has_log_hash(tmp_path: Path) -> None:
    receipt = make_receipt(tmp_path)
    assert receipt.status == "passed"
    assert receipt.returncode == 0
    assert len(receipt.log_sha256) == 64
    assert (tmp_path / receipt.log).read_text().strip() == "real execution"


def test_program_error_is_failure_even_for_missing_module_text(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-c", 'raise ModuleNotFoundError("No module named real_bug")')),
        tmp_path,
        "abc",
        tmp_path / "logs",
    )
    assert receipt.status == "failed"


def test_missing_executable_is_blocked(tmp_path: Path) -> None:
    receipt = run_gate(Gate("probe", ("/certainly-not-installed/panda-tool",)), tmp_path, "abc", tmp_path / "logs")
    assert receipt.status == "blocked"


def test_timeout_is_failure_not_unavailability(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-c", "import time; time.sleep(5)"), timeout=0.05),
        tmp_path,
        "abc",
        tmp_path / "logs",
    )
    assert receipt.status == "failed"
    assert "timeout" in receipt.reason.lower()


def test_missing_python_tool_is_blocked(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-m", "not_installed_panda_module"), module="not_installed_panda_module"),
        tmp_path,
        "abc",
        tmp_path / "logs",
    )
    assert receipt.status == "blocked"


def test_no_shell_interpolation(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-c", "import sys; print(sys.argv[1])", "$(touch compromised)")),
        tmp_path,
        "abc",
        tmp_path / "logs",
    )
    assert receipt.status == "passed"
    assert not (tmp_path / "compromised").exists()


def test_valid_receipts_accepted(tmp_path: Path) -> None:
    receipt = make_receipt(tmp_path)
    assert validate_receipts([receipt], {"probe"}, "abc", tmp_path) == []


@pytest.mark.parametrize(
    ("field", "value"), [("fingerprint", "stale"), ("status", "blocked"), ("returncode", 1), ("log_sha256", "0" * 64)]
)
def test_stale_or_failed_or_tampered_receipts_rejected(tmp_path: Path, field: str, value: object) -> None:
    receipt = replace(make_receipt(tmp_path), **{field: value})
    assert validate_receipts([receipt], {"probe"}, "abc", tmp_path)


def test_duplicate_receipts_rejected(tmp_path: Path) -> None:
    receipt = make_receipt(tmp_path)
    assert validate_receipts([receipt, receipt], {"probe"}, "abc", tmp_path)


def test_missing_gate_rejected(tmp_path: Path) -> None:
    assert validate_receipts([make_receipt(tmp_path)], {"probe", "missing"}, "abc", tmp_path)


def test_extra_failed_gate_rejected(tmp_path: Path) -> None:
    receipt = make_receipt(tmp_path)
    extra = replace(receipt, gate="extra", status="failed")
    assert validate_receipts([receipt, extra], {"probe"}, "abc", tmp_path)


def test_log_cannot_escape_project(tmp_path: Path) -> None:
    receipt = replace(make_receipt(tmp_path), log="../outside")
    assert validate_receipts([receipt], {"probe"}, "abc", tmp_path)


def test_deleted_log_rejected(tmp_path: Path) -> None:
    receipt = make_receipt(tmp_path)
    (tmp_path / receipt.log).unlink()
    assert validate_receipts([receipt], {"probe"}, "abc", tmp_path)


def test_negative_duration_rejected(tmp_path: Path) -> None:
    receipt = replace(make_receipt(tmp_path), duration_seconds=-1)
    assert validate_receipts([receipt], {"probe"}, "abc", tmp_path)


def test_fingerprint_changes_with_source_not_report(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    src = tmp_path / "src" / "value.py"
    _ = src.write_text("VALUE = 1\n")
    before = input_fingerprint(tmp_path)
    (tmp_path / "verification").mkdir()
    _ = (tmp_path / "verification" / "note.txt").write_text("report")
    assert before == input_fingerprint(tmp_path)
    _ = src.write_text("VALUE = 2\n")
    assert before != input_fingerprint(tmp_path)


@pytest.mark.parametrize(
    "source",
    [
        "import pandas as pd",
        "from xarray import Dataset",
        "import pandas.core",
        'importlib.import_module("pandas")',
        '__import__("xarray")',
    ],
)
def test_pandas_and_xarray_imports_blocked(source: str) -> None:
    assert forbidden_imports(source)


@pytest.mark.parametrize(
    "source",
    [
        "import polars as pl",
        "import numpy as np",
        "import csv",
        'text = "import pandas"',
        "# from xarray import Dataset",
    ],
)
def test_policy_does_not_ban_numerics_or_documentation(source: str) -> None:
    assert forbidden_imports(source) == []


@pytest.mark.parametrize("names", [["Pandas"], ["XARRAY"], ["numpy", "pandas"], ["pandas_stubs"]])
def test_resolved_graph_bans_packages(names: list[str]) -> None:
    assert forbidden_packages(names)


def test_resolved_graph_allows_polars_numpy() -> None:
    assert forbidden_packages(["polars", "polars-runtime-32", "numpy"]) == []


def test_missing_lock_is_not_accepted(tmp_path: Path) -> None:
    assert validate_lock(tmp_path / "uv.lock")


def test_lock_rejects_banned_transitive(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text('version=1\n[[package]]\nname="pandas"\nversion="1.0"\n')
    assert validate_lock(path)


def test_lock_requires_download_hashes(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text(
        'version=1\n[[package]]\nname="numpy"\nversion="2.5.4"\nsource={registry="https://pypi.org/simple"}\n'
    )
    assert validate_lock(path)


def test_empty_lock_rejected(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text("version=1\n")
    assert validate_lock(path)


def test_hashed_lock_accepted(tmp_path: Path) -> None:
    path = tmp_path / "uv.lock"
    _ = path.write_text(
        'version=1\n[[package]]\nname="numpy"\nversion="2.5.4"\nsource={registry="https://pypi.org/simple"}\nwheels=[{url="https://files.pythonhosted.org/n.whl",hash="sha256:'
        + "a" * 64
        + '"}]\n'
    )
    assert validate_lock(path) == []


def test_current_input_register_complete() -> None:
    root = Path(__file__).resolve().parents[1]
    report = audit_inputs(root)
    assert report["errors"] == []
    assert report["parameters_checked"] == 27
    assert report["public_births"] == 46711
    assert report["source_validation"] != "all inputs empirically verified"


def test_exit_69_from_a_program_is_not_automatically_a_missing_tool(tmp_path: Path) -> None:
    receipt = run_gate(
        Gate("probe", (sys.executable, "-c", "raise SystemExit(69)")), tmp_path, "abc", tmp_path / "logs"
    )
    assert receipt.status == "failed"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"name": "../unsafe", "command": ("x",)}, "Gate name must be a lowercase identifier"),
        ({"name": "ok", "command": ()}, "Command must contain nonempty string arguments"),
        ({"name": "ok", "command": ("x",), "timeout": 0}, "Gate timeout must be positive and finite"),
    ],
)
def test_invalid_gate_spec_rejected(kwargs: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        # Deliberately invalid gate specifications must fail closed at runtime.
        _ = _gate(**kwargs)


def test_external_log_directory_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Log directory must be inside the project"):
        _ = run_gate(
            Gate("probe", (sys.executable, "-c", "print(1)")), tmp_path, "abc", tmp_path.parent / "outside-logs"
        )
