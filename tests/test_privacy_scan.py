"""Prove the identifier scan is sensitive to a fixture and silent on the real tree.

Synthetic identifiers are assembled at run time on purpose: this module is itself inside
the scanned tree, so a literal mailbox, phone number or ten-digit group here would be
reported by the very gate the tests exercise.
"""

from __future__ import annotations

import json
import sys
import zipfile
import zlib
from typing import TYPE_CHECKING, cast

import pytest

from quality import privacy
from quality.cli import gates_for_profile
from quality.privacy import Allowance

if TYPE_CHECKING:
    from pathlib import Path

# Assembled rather than literal, for the reason in the module docstring.
AT = chr(64)
FAKE_EMAIL = "jordan.reeve" + AT + "exampleclinic.net.au"
FAKE_RESERVED_EMAIL = "jordan.reeve" + AT + "example.com"
FAKE_USERINFO = "https://user:" + "hunter2" + AT + "github.com/binary"
FAKE_PHONE = "(07) " + "3138 " + "5521"
FAKE_INTERNATIONAL = "+61 " + "412 345 " + "678"
FAKE_MOBILE = "04" + "12 345 " + "678"
FAKE_SUBSCRIBER = "2123 45670 " + "1"
FAKE_TAX = "123 456 " + "782"
FAKE_PAYMENT = "4111 1111 1111 " + "1111"
FAKE_NOT_A_CARD = "4111 1111 1111 " + "1112"
ALL_RULES = (
    "email",
    "au_phone",
    "medicare_number",
    "tfn",
    "card_number",
    "identifier_column",
    "identifier_key",
)
CLEAN_SCAN = "Published aggregate facility counts with cited public sources.\n"


def fixture_tree(root: Path) -> Path:
    """Write the sensitivity fixture into a temporary root and return it.

    Returns:
        Path: The temporary root that now holds the fixture files.
    """
    note = f"Referral: {FAKE_EMAIL} or {FAKE_PHONE} or {FAKE_INTERNATIONAL}.\n"
    note += f"Medicare number: {FAKE_SUBSCRIBER}\n"
    note += f"Payment card number {FAKE_PAYMENT}\n"
    note += f"Tax file number: {FAKE_TAX}\n"
    _ = (root / "note.md").write_text(note, encoding="utf-8")
    header = "patient_id," + "medicare" + ",visit,dob"
    rows = f"8841,{FAKE_SUBSCRIBER},2026-01-02,1970-01-01\n"
    rows += f"8842,{FAKE_SUBSCRIBER},2026-01-03,not reported\n"
    _ = (root / "roster.csv").write_text(header + "\n" + rows, encoding="utf-8")
    _ = (root / "export.json").write_text(json.dumps({"surname": "Reeve", "queue": [1, 2]}), encoding="utf-8")
    untyped = {"mobile": {"pilot": 1.5}, "dob": "not reported"}
    _ = (root / "untyped.json").write_text(json.dumps(untyped), encoding="utf-8")
    return root


def rules_of(report: privacy.Report) -> set[str]:
    """Return the set of rule names reported.

    Returns:
        set[str]: Every rule name that produced a finding.
    """
    return {finding.rule for finding in report.findings}


def test_synthetic_identifiers_of_every_documented_shape_are_found(tmp_path: Path) -> None:
    report = privacy.scan_repository(fixture_tree(tmp_path))
    assert report.findings
    assert report.passed is False
    assert set(ALL_RULES) <= rules_of(report)


def test_identifier_findings_name_the_field_and_never_the_value(tmp_path: Path) -> None:
    report = privacy.scan_repository(fixture_tree(tmp_path))
    details = {finding.detail for finding in report.findings if finding.rule.startswith("identifier_")}
    assert details == {"patient_id", "medicare", "dob", "surname"}
    body = json.dumps(privacy._report_body(report))  # pyright: ignore[reportPrivateUsage] -- the receipt is the reviewed output surface
    for value in (FAKE_EMAIL, FAKE_PHONE, FAKE_SUBSCRIBER, FAKE_TAX, FAKE_PAYMENT, FAKE_MOBILE):
        assert value not in body


def test_the_real_repository_tree_passes_without_exemptions() -> None:
    report = privacy.scan_repository(privacy.ROOT)
    assert report.findings == ()
    assert report.unused_exemptions == ()
    assert report.exemptions == ()
    assert privacy.ALLOWANCES == ()
    assert report.passed is True
    assert report.scanned_files > 1000


def test_documented_identifier_columns_are_reported(tmp_path: Path) -> None:
    _ = (tmp_path / "table.csv").write_text("mrn,first_name,surname,address\n1,Ann,Lee,1 Road\n", encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    assert rules_of(report) == {"identifier_column"}
    assert {finding.detail for finding in report.findings} == {"mrn", "first_name", "surname", "address"}


def test_columns_that_only_resemble_identifiers_are_not_reported(tmp_path: Path) -> None:
    _ = (tmp_path / "table.csv").write_text("telephone_net,patient_family_net,mobile\n1.5,2.5,0.0\n", encoding="utf-8")
    _ = (tmp_path / "nested.json").write_text(json.dumps({"mobile": {"pilot": 0.0}}), encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    assert report.findings == ()
    assert report.passed is True


def test_reserved_domains_and_url_userinfo_are_not_mailboxes(tmp_path: Path) -> None:
    _ = (tmp_path / "notes.txt").write_text(f"{FAKE_RESERVED_EMAIL}\n{FAKE_USERINFO}\n", encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    assert report.findings == ()
    assert report.passed is True


def test_mailboxes_are_found_at_the_local_part_boundary_only(tmp_path: Path) -> None:
    valid = "a" * 64 + AT + "exampleclinic.net.au"
    too_long = "a" * 65 + AT + "exampleclinic.net.au"
    pair = "one" + AT + "alpha.net" + " " + "two" + AT + "beta.net"
    _ = (tmp_path / "addresses.txt").write_text(f"{valid}\n{too_long}\nStray {AT} sign\n{pair}\n", encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    emails = [finding for finding in report.findings if finding.rule == "email"]
    assert len(emails) == 3
    assert sorted(finding.line for finding in emails) == [1, 4, 4]


def test_line_numbers_survive_non_newline_breaks(tmp_path: Path) -> None:
    text = "clean first line\rsecond line with " + FAKE_EMAIL + "\n"
    _ = (tmp_path / "breaks.txt").write_text(text, encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    assert [(finding.rule, finding.line) for finding in report.findings] == [("email", 2)]


def test_bare_digit_runs_and_decimal_fractions_are_not_identifiers(tmp_path: Path) -> None:
    text = "0123456789\n" + "9012345679\n" + "17041.049382716046\n" + "22972.9012345679\n"
    text += "digest 8560351941732 and 2837737991474 and 2245706871922\n"
    _ = (tmp_path / "bounds.txt").write_text(text, encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    assert report.findings == ()
    assert report.passed is True


def test_grouped_numbers_are_read_as_australian_telephone_numbers(tmp_path: Path) -> None:
    accepted = tmp_path / "accepted"
    rejected = tmp_path / "rejected"
    accepted.mkdir()
    rejected.mkdir()
    _ = (accepted / "ok.txt").write_text(f"{FAKE_PHONE}\n{FAKE_INTERNATIONAL}\n{FAKE_MOBILE}\n", encoding="utf-8")
    services = "Healthdirect 1800 022 222\nLifeline 13 11 14\n1300 655 506\n"
    _ = (rejected / "service.txt").write_text(services, encoding="utf-8")
    found = privacy.scan_repository(accepted)
    ignored = privacy.scan_repository(rejected)
    assert rules_of(found) == {"au_phone"}
    assert len(found.findings) == 3
    assert ignored.findings == ()


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("4111 1111 1111 1111", True),
        ("4111 1111 1111 1112", False),
        ("1234 5678 9012", False),
        ("", False),
    ],
)
def test_luhn_check_decides_card_shapes(value: str, *, expected: bool) -> None:
    assert privacy._luhn_valid(privacy._digits(value)) is expected  # pyright: ignore[reportPrivateUsage] -- the checksum helper is the in-repo surface under test


def test_card_context_requires_the_luhn_checksum(tmp_path: Path) -> None:
    valid = tmp_path / "valid"
    invalid = tmp_path / "invalid"
    valid.mkdir()
    invalid.mkdir()
    _ = (valid / "card.txt").write_text(f"credit card {FAKE_PAYMENT}\n", encoding="utf-8")
    _ = (invalid / "wrong.txt").write_text(f"credit card {FAKE_NOT_A_CARD}\n", encoding="utf-8")
    assert rules_of(privacy.scan_repository(valid)) == {"card_number"}
    assert privacy.scan_repository(invalid).findings == ()


def test_value_patterns_are_not_matched_without_their_context(tmp_path: Path) -> None:
    _ = (tmp_path / "bare.txt").write_text(f"{FAKE_SUBSCRIBER}\n{FAKE_TAX}\n{FAKE_PAYMENT}\n", encoding="utf-8")
    assert privacy.scan_repository(tmp_path).findings == ()


def test_unreadable_utf8_and_opaque_payloads_are_reported_not_scanned(tmp_path: Path) -> None:
    _ = (tmp_path / "binary.bin").write_bytes(b"\xff\xfe\x00\x01")
    _ = (tmp_path / "blob.npz").write_bytes(b"PK\x03\x04" + FAKE_EMAIL.encode())
    report = privacy.scan_repository(tmp_path)
    reasons = {entry.reason for entry in report.not_scanned}
    assert reasons == {"not-utf8-or-binary-payload", "opaque-or-compressed-payload"}
    assert report.findings == ()
    assert report.passed is True


def test_oversize_files_are_reported_not_read(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(privacy, "MAX_TEXT_BYTES", 4)
    _ = (tmp_path / "large.txt").write_text(FAKE_EMAIL, encoding="utf-8")
    report = privacy.scan_repository(tmp_path)
    assert [entry.reason for entry in report.not_scanned] == ["oversize"]
    assert report.findings == ()


def test_ooxml_document_bodies_are_scanned(tmp_path: Path) -> None:
    with zipfile.ZipFile(tmp_path / "brief.docx", "w") as archive:
        _ = archive.writestr("word/document.xml", f"<w:t>{FAKE_EMAIL}</w:t>")
    report = privacy.scan_repository(tmp_path)
    assert rules_of(report) == {"email"}
    assert report.container_files == 1


def test_ooxml_container_that_cannot_be_read_is_reported(tmp_path: Path) -> None:
    _ = (tmp_path / "broken.docx").write_bytes(b"not a zip container")
    report = privacy.scan_repository(tmp_path)
    assert [entry.reason for entry in report.not_scanned] == ["container-unreadable"]
    assert report.passed is True


def test_pdf_streams_are_inflated_and_scanned(tmp_path: Path) -> None:
    stream = zlib.compress(f"(Referral) Tj ({FAKE_EMAIL}) Tj".encode())
    _ = (tmp_path / "plan.pdf").write_bytes(b"%PDF-1.4\nstream\n" + stream + b"\nendstream\n%%EOF\n")
    report = privacy.scan_repository(tmp_path)
    assert rules_of(report) == {"email"}
    assert report.container_files == 1


def test_inflate_tolerates_payloads_that_are_not_deflate_data() -> None:
    assert privacy._inflate(b"not compressed", 64) == b""  # pyright: ignore[reportPrivateUsage] -- the inflation helper is the in-repo surface under test
    assert privacy._inflate(zlib.compress(b"plain"), 64) == b"plain"  # pyright: ignore[reportPrivateUsage] -- the inflation helper is the in-repo surface under test


def test_exemption_suppresses_a_proven_false_positive(tmp_path: Path) -> None:
    _ = (tmp_path / "note.md").write_text(FAKE_EMAIL, encoding="utf-8")
    allowance = Allowance("email", "note.md", FAKE_EMAIL, "Fixture value proven not to be a person.")
    report = privacy.scan_repository(tmp_path, [allowance])
    assert report.findings == ()
    assert report.exemptions == (allowance,)
    assert report.passed is True


def test_an_exemption_that_suppresses_nothing_fails_the_run(tmp_path: Path) -> None:
    _ = (tmp_path / "note.md").write_text(CLEAN_SCAN, encoding="utf-8")
    allowance = Allowance("email", "*", "*", "No longer needed and therefore stale.")
    report = privacy.scan_repository(tmp_path, [allowance])
    assert report.findings == ()
    assert report.unused_exemptions == (allowance,)
    assert report.passed is False


def test_exemptions_require_a_reason_and_a_unique_selector(tmp_path: Path) -> None:
    _ = (tmp_path / "note.md").write_text(CLEAN_SCAN, encoding="utf-8")
    duplicate = Allowance("email", "*", "*", "Duplicated by suspicion.")
    with pytest.raises(ValueError, match="written reason"):
        _ = privacy.scan_repository(tmp_path, [Allowance("email", "*", "*", "   ")])
    with pytest.raises(ValueError, match="Duplicate exemption"):
        _ = privacy.scan_repository(tmp_path, [duplicate, duplicate])


def test_a_missing_repository_root_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a directory"):
        _ = privacy.scan_repository(tmp_path / "absent")


def test_walk_prunes_local_scopes_and_declared_submodules(tmp_path: Path) -> None:
    modules = '[submodule "sibling"]\n\tpath = extensions/sibling\n\turl = https://example.invalid/x.git\n'
    _ = (tmp_path / ".gitmodules").write_text(modules, encoding="utf-8")
    for name in ("extensions/sibling", ".git", "__pycache__", ".venv-lock", "archive"):
        (tmp_path / name).mkdir(parents=True)
        _ = (tmp_path / name / "inner.txt").write_text("x", encoding="utf-8")
    _ = (tmp_path / "__pycache__" / "cache.pyc").write_bytes(b"\x00")
    _ = (tmp_path / ".testmondata").write_text("x", encoding="utf-8")
    _ = (tmp_path / "kept.md").write_text("x", encoding="utf-8")
    found = {path.name for path in privacy.repository_files(tmp_path)}
    assert "kept.md" in found
    assert not {"inner.txt", "cache.pyc", ".testmondata"} & found
    assert privacy._submodule_paths(tmp_path) == frozenset({"extensions/sibling"})  # pyright: ignore[reportPrivateUsage] -- the submodule reader is the in-repo surface under test


def test_quick_profile_stays_a_strict_subset_and_full_profile_enforces_privacy() -> None:
    full = {gate.name: gate for gate in gates_for_profile("full")}
    pull_request = {gate.name for gate in gates_for_profile("pr")}
    quick = {gate.name for gate in gates_for_profile("quick")}
    assert "privacy" in full
    assert "privacy" in pull_request
    assert "privacy" not in quick
    assert "quality.privacy" in full["privacy"].command
    assert full["privacy"].timeout > 0


def test_cli_reports_findings_without_printing_the_matched_value(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = fixture_tree(tmp_path)
    receipt = tmp_path / "receipts" / "privacy.json"
    monkeypatch.setattr(sys, "argv", ["privacy", "--root", str(tmp_path), "--output", str(receipt)])
    assert privacy.main() == 1
    printed = capsys.readouterr().out
    assert "FINDING email:" in printed
    assert FAKE_EMAIL not in printed
    body = cast("dict[str, object]", json.loads(receipt.read_text(encoding="utf-8")))
    assert body["passed"] is False
    assert body["findings_count"] == len(cast("list[object]", body["findings"]))
    assert FAKE_EMAIL not in json.dumps(body)


def test_cli_exits_zero_on_a_clean_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _ = (tmp_path / "clean.md").write_text(CLEAN_SCAN, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["privacy", "--root", str(tmp_path)])
    assert privacy.main() == 0
    assert "0 finding(s)" in capsys.readouterr().out
