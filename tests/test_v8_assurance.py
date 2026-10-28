"""Regression tests for complete, interruption-resilient assurance evidence."""
from pathlib import Path
from types import SimpleNamespace
import errno
import hashlib
import json
import sys
import pytest

from quality.assurance import Gate, Receipt, run_gate
import quality.cli as cli

def test_permission_denied_is_a_failed_receipt_not_an_aborted_run(tmp_path):
    executable = tmp_path / "not-executable"
    executable.write_text("#!/bin/sh\nexit 0\n")
    executable.chmod(0o600)
    result = run_gate(Gate("permission_probe", (str(executable),)), tmp_path, "fp", tmp_path / "logs")
    assert result.status == "failed"
    assert result.returncode != 0
    assert "permission" in result.reason.lower()
    assert (tmp_path / result.log).is_file()

def test_other_launch_oserror_is_failed_not_missing(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise OSError(errno.ENOEXEC, "Exec format error")
    monkeypatch.setattr("quality.assurance.subprocess.run", fail)
    result = run_gate(Gate("format_probe", ("bad-binary",)), tmp_path, "fp", tmp_path / "logs")
    assert result.status == "failed"
    assert "Exec format" in result.reason

def test_undecodable_tool_output_is_retained(tmp_path):
    result = run_gate(Gate("bytes_probe", (sys.executable, "-c", "import os;os.write(1,b'\\xff\\n')")),
                      tmp_path, "fp", tmp_path / "logs")
    assert result.status == "passed"
    assert "\ufffd" in (tmp_path / result.log).read_text()

def test_checkpoint_survives_unexpected_later_gate_failure(monkeypatch,tmp_path):
    monkeypatch.setattr(cli,"ROOT",tmp_path)
    monkeypatch.setattr(sys,"argv",["quality.cli","--profile","full","--evidence-version","v8"])
    monkeypatch.setattr(cli,"input_fingerprint",lambda root:"fp")
    monkeypatch.setattr(cli,"gates_for_profile",lambda profile:[
        Gate("first",(sys.executable,"-c","pass")),Gate("second",(sys.executable,"-c","pass"))])
    def run(gate, root, fp, logdir):
        if gate.name=="second":
            saved=json.loads((logdir/"receipt.json").read_text())
            assert saved["run_finished"] is False
            assert saved["full_local_assurance"] is False
            assert len(saved["receipts"])==1
            raise RuntimeError("simulated runner interruption")
        p=logdir/"first.txt";p.write_text("ok")
        return Receipt("first","passed",0,fp,gate.command,.01,
                       str(p.relative_to(root)),hashlib.sha256(p.read_bytes()).hexdigest())
    monkeypatch.setattr(cli,"run_gate",run)
    with pytest.raises(RuntimeError,match="simulated runner interruption"):
        cli.main()
    data=json.loads((tmp_path/"verification/v8/full/receipt.json").read_text())
    assert data["run_finished"] is False
    assert data["run_id"]
    assert data["active_gate"]=="second"
    assert data["receipts"][0]["gate"]=="first"

@pytest.mark.parametrize("bad",["../other","v8/../x","8",""])
def test_evidence_version_rejects_path_or_invalid_name(monkeypatch,bad,tmp_path):
    monkeypatch.setattr(cli,"ROOT",tmp_path)
    monkeypatch.setattr(sys,"argv",["quality.cli","--evidence-version",bad])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code==2
