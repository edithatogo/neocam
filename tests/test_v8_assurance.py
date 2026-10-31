"""Regression tests for complete, interruption-resilient assurance evidence."""

from __future__ import annotations

import errno
import hashlib
import json
import shutil
import sys
from typing import TYPE_CHECKING, TypedDict, cast

import pytest

from quality import cli
from quality.assurance import Gate, Receipt, run_gate

if TYPE_CHECKING:
    from pathlib import Path


class Report(TypedDict):
    """Checkpointed assurance report fields asserted by these tests."""

    run_finished: bool
    full_local_assurance: bool
    run_id: str
    active_gate: str
    receipts: list[dict[str, object]]


def test_permission_denied_is_a_failed_receipt_not_an_aborted_run(tmp_path: Path) -> None:
    executable = tmp_path / "not-executable"
    _ = executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o600)
    result = run_gate(Gate("permission_probe", (str(executable),)), tmp_path, "fp", tmp_path / "logs")
    assert result.status == "failed"
    assert result.returncode != 0
    assert "permission" in result.reason.lower()
    assert (tmp_path / result.log).is_file()


def test_other_launch_oserror_is_failed_not_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        msg = "Exec format error"
        raise OSError(errno.ENOEXEC, msg)

    monkeypatch.setattr("quality.assurance.subprocess.run", fail)
    result = run_gate(Gate("format_probe", ("bad-binary",)), tmp_path, "fp", tmp_path / "logs")
    assert result.status == "failed"
    assert "Exec format" in result.reason


def test_undecodable_tool_output_is_retained(tmp_path: Path) -> None:
    result = run_gate(
        Gate("bytes_probe", (sys.executable, "-c", "import os;os.write(1,b'\\xff\\n')")),
        tmp_path,
        "fp",
        tmp_path / "logs",
    )
    assert result.status == "passed"
    assert "\ufffd" in (tmp_path / result.log).read_text()


def test_checkpoint_survives_unexpected_later_gate_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["quality.cli", "--profile", "full", "--evidence-version", "v8"])

    def fingerprint(_root: Path) -> str:
        return "fp"

    def gates(_profile: str) -> list[Gate]:
        return [Gate("first", (sys.executable, "-c", "pass")), Gate("second", (sys.executable, "-c", "pass"))]

    monkeypatch.setattr(cli, "input_fingerprint", fingerprint)
    monkeypatch.setattr(cli, "gates_for_profile", gates)

    def run(gate: Gate, root: Path, fp: str, logdir: Path) -> Receipt:
        if gate.name == "second":
            saved = cast("Report", json.loads((logdir / "receipt.json").read_text()))
            assert saved["run_finished"] is False
            assert saved["full_local_assurance"] is False
            assert len(saved["receipts"]) == 1
            msg = "simulated runner interruption"
            raise RuntimeError(msg)
        p = logdir / "first.txt"
        _ = p.write_text("ok")
        return Receipt(
            "first",
            "passed",
            0,
            fp,
            gate.command,
            0.01,
            str(p.relative_to(root)),
            hashlib.sha256(p.read_bytes()).hexdigest(),
        )

    monkeypatch.setattr(cli, "run_gate", run)
    with pytest.raises(RuntimeError, match="simulated runner interruption"):
        _ = cli.main()
    data = cast("Report", json.loads((tmp_path / "verification/v8/full/receipt.json").read_text()))
    assert data["run_finished"] is False
    assert data["run_id"]
    assert data["active_gate"] == "second"
    assert data["receipts"][0]["gate"] == "first"


@pytest.mark.parametrize("bad", ["../other", "v8/../x", "8", ""])
def test_evidence_version_rejects_path_or_invalid_name(
    monkeypatch: pytest.MonkeyPatch, bad: str, tmp_path: Path
) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["quality.cli", "--evidence-version", bad])
    with pytest.raises(SystemExit) as error:
        _ = cli.main()
    assert error.value.code == 2


def test_missing_native_tool_has_explicit_missing_path(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "ROOT", tmp_path)

    def no_which(_name: str) -> None:
        return None

    monkeypatch.setattr(shutil, "which", no_which)
    # The private path resolver is the published in-repo surface under test.
    assert cli._native("gitleaks") == str(tmp_path / ".tools/bin/gitleaks")  # pyright: ignore[reportPrivateUsage]
