"""The current report ships a paginated PDF that only the reportlab path produces.

The PDF transcribes the same authored lines as the markdown sibling, so it is
checked for the disclosed caveats, for reportlab-only structure (producer string,
embedded base-14 fonts, more than one page) and for byte determinism.
"""

import base64
import contextlib
import json
import re
import shutil
import zlib
from pathlib import Path
from typing import cast

from quality import artifacts
from scripts.build_current_report import build

ROOT = Path(__file__).resolve().parents[1]
# Every input the report builder reads from the resolved output snapshot.
REPORT_INPUTS = (
    "resolved_inputs.json",
    "results.json",
    "psa_perspectives.csv",
    "mixed_estate_budget.csv",
    "utility_bridge_scenarios.csv",
)
# Disclosed caveats the paginated document must carry, as authored for the markdown sibling.
CAVEATS = (
    "no new patient data, local effect fitting or independent clinical validation",
    "This is not a video-effect estimate",
    "Simulated roles are author review only",
    "Software acceptance is separate from these numerical outputs",
    "IHACPA episode prices are prototypes",
)
_TEXT_SHOW: re.Pattern[bytes] = re.compile(rb"\((?:\\.|[^\\()])*\)\s*Tj", re.DOTALL)
_STREAM: re.Pattern[bytes] = re.compile(rb"stream\r?\n(.*?)endstream", re.DOTALL)
_PAGE: re.Pattern[bytes] = re.compile(rb"/Type\s*/Page\b")


def _current_output() -> Path:
    assurance = cast("dict[str, object]", json.loads((ROOT / "config/assurance.json").read_text(encoding="utf-8")))
    return ROOT / cast("str", assurance["current_output"])


def _render(tmp_path: Path) -> bytes:
    """Build the report in an isolated directory and return the PDF bytes.

    Returns:
        bytes: The generated ``current_report.pdf`` contents.
    """
    source = _current_output()
    for name in REPORT_INPUTS:
        _ = shutil.copy(source / name, tmp_path / name)
    build(tmp_path)
    return (tmp_path / "current_report.pdf").read_bytes()


def _content_streams(data: bytes) -> list[bytes]:
    """Return each content stream as written plus every decoding that applies.

    Returns:
        list[bytes]: Raw and decoded content stream payloads.
    """
    decoded: list[bytes] = []
    for chunk in cast("list[bytes]", _STREAM.findall(data)):
        body = chunk.strip(b"\r\n")
        candidates = [body]
        if body.endswith(b"~>"):
            candidates.append(base64.a85decode(body[:-2], adobe=False))
        for candidate in list(candidates):
            with contextlib.suppress(zlib.error):
                candidates.append(zlib.decompress(candidate))
        decoded.extend(candidates)
    return decoded


def _drawn_text(data: bytes) -> str:
    """Join reportlab's drawn text literals, ignoring line wrapping and whitespace.

    Returns:
        str: Whitespace-free document text.
    """
    parts: list[str] = []
    for stream in _content_streams(data):
        for literal in cast("list[bytes]", _TEXT_SHOW.findall(stream)):
            raw = literal[: literal.rfind(b")")][1:]
            parts.append(re.sub(rb"\\([()\\])", rb"\1", raw).decode("latin-1"))
    return re.sub(r"\s+", "", "".join(parts))


def test_report_pdf_is_produced_by_the_reportlab_path(tmp_path: Path) -> None:
    data = _render(tmp_path)
    assert data.startswith(b"%PDF")
    # reportlab's producer string, its base-14 fonts and page furniture: a
    # matplotlib figure export has none of these.
    assert b"ReportLab" in data
    assert b"matplotlib" not in data
    assert b"/BaseFont /Helvetica" in data
    assert b"/BaseFont /Helvetica-Bold" in data
    # No figure raster: like the markdown sibling, the PDF is text only.
    assert b"/Subtype /Image" not in data
    assert len(_PAGE.findall(data)) > 1


def test_report_pdf_is_byte_deterministic(tmp_path: Path) -> None:
    assert _render(tmp_path) == _render(tmp_path)


def test_report_pdf_carries_the_disclosed_caveats(tmp_path: Path) -> None:
    text = _drawn_text(_render(tmp_path))
    for caveat in CAVEATS:
        assert re.sub(r"\s+", "", caveat) in text, caveat


def test_report_pdf_is_written_beside_its_markdown_and_html_siblings(tmp_path: Path) -> None:
    _ = _render(tmp_path)
    assert (tmp_path / "current_report.md").is_file()
    assert (tmp_path / "current_report.html").is_file()
    assert (tmp_path / "current_report.pdf").stat().st_size > 0


def test_report_pdf_is_registered_in_the_release_inventory(tmp_path: Path) -> None:
    _ = _render(tmp_path)
    inventory = artifacts.output_inventory(tmp_path)
    assert "current_report.pdf" in inventory
    assert len(inventory["current_report.pdf"]) == artifacts.SHA256_HEX_LENGTH
