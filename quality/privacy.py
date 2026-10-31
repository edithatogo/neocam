"""High-confidence identifier scan for a public repository: a privacy gate, not a proof.

Why this gate exists
--------------------
Secret scanning finds credentials and never personal identifiers. This module is the
complementary check: it looks for the shapes a personal or patient identifier takes
when it leaks into tracked content, and fails the assurance run when it finds one.

What is scanned
---------------
Every file below the repository root, except the local-only, generated and dependency
scopes named in ``EXCLUDED_DIRECTORIES`` and ``EXCLUDED_FILE_*`` (these mirror the local
entries of ``.gitignore``) and the declared submodule paths in ``.gitmodules``. Text
files are decoded as UTF-8. The XML parts of OOXML containers (``.docx``, ``.xlsx``,
``.pptx``) are read with :mod:`zipfile`, and the FlateDecode streams of PDF files are
inflated with :mod:`zlib`, so document bodies are scanned with the standard library
alone. Opaque or compressed payloads cannot be read as text; they are listed in the
receipt instead of being skipped silently.

What is detected
----------------
* ``email``: a mailbox other than an RFC 2606/6761 reserved domain or URL userinfo.
* ``au_phone``: an Australian number written in a conventional grouped form, so a bare
  ten-digit run is never treated as a phone number.
* ``medicare_number``, ``tfn``, ``card_number``: a numeric identifier next to the words
  that name it, with a length or Luhn check on the captured value.
* ``identifier_column``, ``identifier_key``: a CSV header or JSON key named after a
  personal identifier, when that column or key actually holds identifier-shaped values.

What is deliberately NOT detected
---------------------------------
* Personal names, in free text or in document metadata such as ``dc:creator`` and
  ``cp:lastModifiedBy``. Name detection needs a model and a name gazetteer; it is out
  of scope here by design, and no claim should be read as covering it.
* Street addresses, dates of birth and postcodes in free text.
* Identifiers inside opaque binary payloads or inside compressed image streams.
* Identifiers that do not appear in one of the documented shapes. A bare digit run is
  not evidence of a person: in this repository a bare ten-digit run is a digest
  fragment, a chart coordinate or a decimal fraction. Every numeric rule therefore
  demands either a grouped format or the word that names the identifier.

Matched values are never printed and never written to the receipt, which is retained
evidence in a public repository. Only the rule, the path, the line and, for a named
field, the field name are recorded.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

ROOT = Path(__file__).resolve().parents[1]

# Local-only, generated or dependency scopes; mirrors the local entries of .gitignore.
EXCLUDED_DIRECTORIES = frozenset({
    ".git",
    ".venv",
    ".tools",
    ".uv-cache",
    ".ruff_cache",
    ".pytest_cache",
    ".hypothesis",
    ".gremlins_cache",
    ".mypy_cache",
    ".pytype",
    ".basedpyright",
    ".opencode",
    ".worktrees",
    ".feedback-cache",
    ".tox",
    ".nox",
    ".ipynb_checkpoints",
    "build",
    "archive",
    "coverage",
    "htmlcov",
    "node_modules",
    "__pycache__",
})
EXCLUDED_DIRECTORY_PREFIXES = (".venv-",)
EXCLUDED_FILE_NAMES = frozenset({".coverage", ".DS_Store", "coverage.json", "coverage.xml"})
EXCLUDED_FILE_PREFIXES = (".testmondata",)
EXCLUDED_FILE_SUFFIXES = frozenset({".pyc", ".pyo", ".swp", ".swo", ".tmp", ".bak"})

# Containers whose inner parts are genuine text, and payloads that cannot be read.
OOXML_SUFFIXES = frozenset({".docx", ".docm", ".dotx", ".xlsx", ".xlsm", ".xltx", ".pptx", ".pptm", ".potx"})
PDF_SUFFIXES = frozenset({".pdf"})
OPAQUE_SUFFIXES = frozenset({
    ".7z",
    ".bmp",
    ".bz2",
    ".class",
    ".db",
    ".der",
    ".dll",
    ".dylib",
    ".eot",
    ".exe",
    ".gif",
    ".gz",
    ".ico",
    ".jpeg",
    ".jpg",
    ".npy",
    ".npz",
    ".otf",
    ".p12",
    ".pfx",
    ".png",
    ".so",
    ".sqlite",
    ".tgz",
    ".tif",
    ".tiff",
    ".ttf",
    ".vsix",
    ".wasm",
    ".webp",
    ".whl",
    ".woff",
    ".woff2",
    ".xz",
    ".zip",
})
TABULAR_SUFFIXES = frozenset({".csv", ".tsv"})
JSON_SUFFIXES = frozenset({".json", ".jsonl", ".ndjson"})

# Every read is bounded so the gate cannot become a memory hazard. Document containers
# are read whole because their text parts are small and individually bounded; a text
# file is read up to the text bound, and anything larger is reported, never guessed.
MAX_TEXT_BYTES = 32 * 1024 * 1024
MAX_CONTAINER_BYTES = 64 * 1024 * 1024
MAX_CONTAINER_PART_BYTES = 2 * 1024 * 1024
MAX_INFLATED_BYTES = 2 * 1024 * 1024
MINIMUM_TABLE_ROWS = 2
AU_PHONE_DIGITS = 10
CARD_MIN_DIGITS = 13
CARD_MAX_DIGITS = 19
MEDICARE_DIGITS = frozenset({10, 11})
TFN_DIGITS = frozenset({8, 9})

EMAIL_LOCAL_PATTERN = r"(?<![A-Za-z0-9._%+\-])[A-Za-z0-9._%+\-]{1,64}"
EMAIL_DOMAIN_PATTERN = r"@(?:[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,24}"
EMAIL_PATTERN = re.compile(EMAIL_LOCAL_PATTERN + EMAIL_DOMAIN_PATTERN + r"(?![A-Za-z0-9\-])")
# Reserved for documentation and testing (RFC 2606, RFC 6761): not a mailbox.
RESERVED_EMAIL_DOMAINS = frozenset({
    "example.com",
    "example.net",
    "example.org",
    "example.edu",
    "invalid",
    "test",
    "localhost",
    "local",
})
URL_USERINFO_PATTERN = re.compile(r"://[^/\s]*:[^/\s]*$")

PHONE_PATTERN = re.compile(r"(?<![\d.])(?:\+?61[ \-]?|0)\d[\d ()\-]{5,17}\d(?![\d.])")
AU_PHONE_PREFIXES = frozenset({"02", "03", "04", "07", "08"})

MEDICARE_PATTERN = re.compile(
    r"(?i)\b(?:medicare|ihi|individual healthcare identifier)\b[^\d\n]{0,40}?(\d[\d \-]{8,13}\d)"
)
TFN_PATTERN = re.compile(r"(?i)\b(?:tfn|tax file number)\b[^\d\n]{0,30}?(\d[\d \-]{6,11}\d)")
CARD_KEYWORDS_PATTERN = r"(?i)\b(?:card[ _\-]?(?:number|no)|credit[ _\-]?card|debit[ _\-]?card|cardholder)\b"
CARD_VALUE_PATTERN = r"[^\d\n]{0,30}?(\d[\d \-]{11,17}\d)"
CARD_PATTERN = re.compile(CARD_KEYWORDS_PATTERN + CARD_VALUE_PATTERN)

# Exact, normalised column and key names, grouped by the value shape each one requires.
NAME_FIELDS = (
    "patient",
    "patient_id",
    "patient_number",
    "patient_no",
    "patient_name",
    "mrn",
    "medical_record_number",
    "first_name",
    "given_name",
    "given_names",
    "surname",
    "last_name",
    "family_name",
    "middle_name",
    "maiden_name",
    "address",
    "home_address",
    "street_address",
    "residential_address",
)
DATE_FIELDS = ("dob", "date_of_birth", "birth_date")
MEDICARE_FIELDS = (
    "medicare",
    "medicare_number",
    "medicare_no",
    "medicare_id",
    "ihi",
    "ihi_number",
    "individual_healthcare_identifier",
)
PHONE_FIELDS = ("phone", "phone_number", "telephone", "telephone_number", "mobile", "mobile_number")
EMAIL_FIELDS = ("email", "email_address")
TFN_FIELDS = ("tfn", "tax_file_number")
CARD_FIELDS = ("card_number", "card_no", "credit_card_number")
IDENTIFIER_NAMES: dict[str, str] = {
    **dict.fromkeys(NAME_FIELDS, "name"),
    **dict.fromkeys(DATE_FIELDS, "date"),
    **dict.fromkeys(MEDICARE_FIELDS, "medicare"),
    **dict.fromkeys(PHONE_FIELDS, "phone"),
    **dict.fromkeys(EMAIL_FIELDS, "email"),
    **dict.fromkeys(TFN_FIELDS, "tfn"),
    **dict.fromkeys(CARD_FIELDS, "card"),
}
PHONE_VALUE_PATTERN = re.compile(r"\d{8,15}")
DATE_VALUE_PATTERN = re.compile(r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|\d{8})")
GITMODULES_PATH_PATTERN = re.compile(r"(?m)^\s*path\s*=\s*(\S+)\s*$")
EMPTY_VALUE_MARKERS = frozenset({"", "na", "n/a", "none", "null", "unknown", "not stated", "not reported"})
NAME_STRIP_PATTERN = re.compile(r"[^a-z0-9]+")


class _CliArgs(Protocol):
    """The parsed CLI attributes for the identifier scan."""

    root: str
    output: str | None


@dataclass(frozen=True)
class Finding:
    """One suspected identifier, described without exposing the matched value.

    Attributes:
        rule: The pattern name that matched.
        path: Repository-relative POSIX path of the file.
        line: One-based line number, or the first line naming a JSON key.
        detail: The column or key name for a field finding, otherwise empty.
    """

    rule: str
    path: str
    line: int
    detail: str = ""


@dataclass(frozen=True)
class Allowance:
    """A reviewed false positive; the written reason is part of the exemption.

    Attributes:
        rule: The rule name this exemption covers.
        path: The exact repository-relative path, or ``*`` for any path.
        value: The exact matched text, or ``*`` for any match.
        reason: The written justification; an empty reason is rejected.
    """

    rule: str
    path: str
    value: str
    reason: str


@dataclass(frozen=True)
class NotScanned:
    """A file this scan could not read as text, with the reason it was skipped.

    Attributes:
        path: Repository-relative POSIX path of the file.
        reason: Why the file has no text coverage.
    """

    path: str
    reason: str


@dataclass(frozen=True)
class Report:
    """The outcome of one scan, including what it did not cover.

    Attributes:
        scanned_files: Number of files that produced text coverage.
        text_files: Number of files decoded directly as UTF-8 text.
        container_files: Number of OOXML or PDF files whose inner text was extracted.
        findings: Findings that no exemption covers.
        exemptions: Exemptions this scan actually applied.
        unused_exemptions: Declared exemptions that suppressed nothing.
        not_scanned: Files with no text coverage, and why.
    """

    scanned_files: int
    text_files: int
    container_files: int
    findings: tuple[Finding, ...]
    exemptions: tuple[Allowance, ...]
    unused_exemptions: tuple[Allowance, ...]
    not_scanned: tuple[NotScanned, ...]

    @property
    def passed(self) -> bool:
        """Report whether the scan found nothing and spent every exemption.

        Returns:
            bool: True when the tree is clean and no exemption is stale.
        """
        return not self.findings and not self.unused_exemptions


@dataclass
class _Scan:
    """Mutable accumulator for one walk over the tree."""

    root: Path
    allowances: Sequence[Allowance]
    findings: list[Finding]
    used: set[int]
    not_scanned: list[NotScanned]
    text_files: int = 0
    container_files: int = 0

    def record(self, rule: str, path: str, line: int, matched: str, detail: str = "") -> None:
        """Record one match unless a reviewed exemption covers it."""
        if self._exempt(rule, path, matched):
            return
        self.findings.append(Finding(rule, path, line, detail))

    def skip(self, path: str, reason: str) -> None:
        """Record that a file produced no text coverage."""
        self.not_scanned.append(NotScanned(path, reason))

    def _exempt(self, rule: str, path: str, matched: str) -> bool:
        """Return whether a declared exemption covers one match, recording its use."""
        for index, allowance in enumerate(self.allowances):
            if allowance.rule == rule and allowance.path in {"*", path} and allowance.value in {"*", matched}:
                self.used.add(index)
                return True
        return False


def _digits(value: str) -> str:
    """Return the digits of a value once grouping punctuation is removed."""
    stripped = value.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
    return stripped if stripped.isdigit() else ""


def _luhn_valid(digits: str) -> bool:
    """Return whether a digit string satisfies the Luhn checksum."""
    total = 0
    for position, character in enumerate(reversed(digits)):
        value = int(character)
        if position % 2:
            value = (value * 2) % 10 + (value * 2) // 10
        total += value
    return bool(digits) and total % 10 == 0


def _is_reserved_email(value: str) -> bool:
    """Return whether an address uses a reserved or non-routable domain."""
    domain = value.rsplit("@", 1)[-1].lower()
    return any(domain == reserved or domain.endswith("." + reserved) for reserved in RESERVED_EMAIL_DOMAINS)


def _is_url_userinfo(line: str, start: int) -> bool:
    """Return whether a match is credential material in a URL, not a mailbox."""
    return URL_USERINFO_PATTERN.search(line[:start]) is not None


def _is_australian_phone(value: str) -> bool:
    """Return whether written text is a grouped Australian telephone number."""
    if not any(character in value for character in " -()") and not value.startswith("+"):
        return False
    digits = _digits(value)
    if digits.startswith("61"):
        digits = "0" + digits[2:]
    return len(digits) == AU_PHONE_DIGITS and digits[:2] in AU_PHONE_PREFIXES


def _is_medicare_value(value: str) -> bool:
    """Return whether a value has the length of a Medicare or IHI number."""
    return len(_digits(value)) in MEDICARE_DIGITS


def _is_tfn_value(value: str) -> bool:
    """Return whether a value has the length of a tax file number."""
    return len(_digits(value)) in TFN_DIGITS


def _is_card_value(value: str) -> bool:
    """Return whether a value is a Luhn-valid card-length sequence."""
    digits = _digits(value)
    return CARD_MIN_DIGITS <= len(digits) <= CARD_MAX_DIGITS and _luhn_valid(digits)


def _is_email_value(value: str) -> bool:
    """Return whether a value is a whole mailbox address."""
    return EMAIL_PATTERN.fullmatch(value.strip()) is not None


def _is_phone_value(value: str) -> bool:
    """Return whether a field value is a bare phone-number-shaped digit group."""
    return PHONE_VALUE_PATTERN.fullmatch(_digits(value)) is not None


def _is_date_value(value: str) -> bool:
    """Return whether a value is a date of birth in a documented shape."""
    return DATE_VALUE_PATTERN.fullmatch(value.strip()) is not None


def _is_name_value(value: str) -> bool:
    """Return whether a value carries any content for a person-named field."""
    return value.strip().lower() not in EMPTY_VALUE_MARKERS


SHAPE_TESTS: dict[str, Callable[[str], bool]] = {
    "name": _is_name_value,
    "date": _is_date_value,
    "medicare": _is_medicare_value,
    "phone": _is_phone_value,
    "email": _is_email_value,
    "tfn": _is_tfn_value,
    "card": _is_card_value,
}
CONTEXT_RULES: tuple[tuple[str, re.Pattern[str], Callable[[str], bool]], ...] = (
    ("medicare_number", MEDICARE_PATTERN, _is_medicare_value),
    ("tfn", TFN_PATTERN, _is_tfn_value),
    ("card_number", CARD_PATTERN, _is_card_value),
)


def _identifier_kind(name: str) -> str | None:
    """Return the identifier kind a column or key name denotes, if any."""
    normalised = NAME_STRIP_PATTERN.sub("_", name.strip().lower()).strip("_")
    return IDENTIFIER_NAMES.get(normalised)


def _scalars(value: object) -> list[str]:
    """Flatten a JSON value into its scalar text values.

    Returns:
        list[str]: Scalar values rendered as text, excluding booleans and nulls.
    """
    found: list[str] = []
    stack = [value]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            stack.extend(cast("dict[str, object]", node).values())
        elif isinstance(node, list):
            stack.extend(cast("list[object]", node))
        elif isinstance(node, str):
            found.append(node)
        elif isinstance(node, (int, float)):
            found.append(str(node))
    return found


def _matches_shape(kind: str, values: Sequence[str]) -> bool:
    """Return whether any value has the shape the identifier kind requires."""
    test = SHAPE_TESTS.get(kind)
    return test is not None and any(test(value) for value in values)


def _csv_columns(text: str, delimiter: str) -> list[tuple[str, list[str]]]:
    """Return the candidate-named columns of one delimited file with their values."""
    rows = list(csv.reader(text.splitlines(), delimiter=delimiter))
    if len(rows) < MINIMUM_TABLE_ROWS or not rows[0]:
        return []
    positions = [(index, name) for index, name in enumerate(rows[0]) if _identifier_kind(name) is not None]
    return [(name, [row[index] for row in rows[1:] if len(row) > index]) for index, name in positions]


def _json_keys(text: str) -> list[str]:
    """Return the candidate-named keys of one JSON document that hold identifier-shaped values."""
    try:
        data = cast("object", json.loads(text))
    except ValueError, RecursionError:
        return []
    found: set[str] = set()
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            for key, value in cast("dict[str, object]", node).items():
                kind = _identifier_kind(key)
                if kind is not None and _matches_shape(kind, _scalars(value)):
                    found.add(key)
                stack.append(value)
        elif isinstance(node, list):
            stack.extend(cast("list[object]", node))
    return sorted(found)


def _line_of_key(text: str, name: str) -> int:
    """Return the first line that names a JSON key, defaulting to the first line."""
    match = re.search(rf'"{re.escape(name)}"\s*:', text)
    return text.count("\n", 0, match.start()) + 1 if match else 1


def _inspect_line(scan: _Scan, relative: str, number: int, line: str) -> None:
    """Record every value match on one line of text."""
    for match in EMAIL_PATTERN.finditer(line):
        value = match.group(0)
        if not _is_reserved_email(value) and not _is_url_userinfo(line, match.start()):
            scan.record("email", relative, number, value)
    for match in PHONE_PATTERN.finditer(line):
        value = match.group(0)
        if _is_australian_phone(value):
            scan.record("au_phone", relative, number, value)
    for rule, pattern, validator in CONTEXT_RULES:
        for match in pattern.finditer(line):
            value = match.group(1)
            if validator(value):
                scan.record(rule, relative, number, value)


def _inspect_fields(scan: _Scan, relative: str, text: str, delimiter: str) -> None:
    """Record a finding for every named field that holds identifier-shaped values."""
    if Path(relative).suffix.lower() in JSON_SUFFIXES:
        for name in _json_keys(text):
            scan.record("identifier_key", relative, _line_of_key(text, name), name, detail=name)
        return
    for name, values in _csv_columns(text, delimiter):
        kind = _identifier_kind(name)
        if kind is not None and _matches_shape(kind, values):
            scan.record("identifier_column", relative, 1, name, detail=name)


def _inspect_text(scan: _Scan, relative: str, text: str, delimiter: str = ",") -> None:
    """Record every value match in decoded text, plus named-field findings when applicable."""
    for number, line in enumerate(text.splitlines(), 1):
        _inspect_line(scan, relative, number, line)
    suffix = Path(relative).suffix.lower()
    if suffix in TABULAR_SUFFIXES or suffix in JSON_SUFFIXES:
        _inspect_fields(scan, relative, text, delimiter)


def _read_text(scan: _Scan, relative: str, blob: bytes) -> None:
    """Scan one file that is expected to be text."""
    try:
        text = blob.decode("utf-8")
    except UnicodeDecodeError:
        scan.skip(relative, "not-utf8-or-binary-payload")
        return
    if "\0" in text:
        scan.skip(relative, "not-utf8-or-binary-payload")
        return
    scan.text_files += 1
    _inspect_text(scan, relative, text, delimiter="\t" if relative.endswith(".tsv") else ",")


def _inflate(data: bytes, limit: int) -> bytes:
    """Return a bounded inflation of deflate data under either framing."""
    for window in (zlib.MAX_WBITS, -zlib.MAX_WBITS):
        try:
            return zlib.decompressobj(window).decompress(data, limit)
        except zlib.error:
            continue
    return b""


def _pdf_texts(blob: bytes) -> list[str]:
    """Return the raw and inflated text of a PDF container."""
    parts = [blob]
    for match in re.finditer(rb"stream\r?\n", blob):
        end = blob.find(b"endstream", match.end())
        if end < 0:
            break
        parts.append(_inflate(blob[match.end() : end], MAX_INFLATED_BYTES))
    return [part.decode("utf-8", errors="replace") for part in parts]


def _zip_members(archive: zipfile.ZipFile) -> list[bytes]:
    """Return the readable XML members of an open OOXML container."""
    parts: list[bytes] = []
    for info in archive.infolist():
        if not info.filename.endswith((".xml", ".rels")) or info.file_size > MAX_CONTAINER_PART_BYTES:
            continue
        try:
            parts.append(archive.read(info))
        except OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile:
            continue
    return parts


def _zip_texts(path: Path) -> list[str]:
    """Return the decoded XML parts of an OOXML container."""
    try:
        with zipfile.ZipFile(path) as archive:
            parts = _zip_members(archive)
    except OSError, RuntimeError, NotImplementedError, zipfile.BadZipFile:
        return []
    return [part.decode("utf-8", errors="replace") for part in parts]


def _file_bytes(scan: _Scan, relative: str, path: Path, *, limit: int) -> bytes | None:
    """Return the bytes of a file under a size bound, recording why it has no coverage."""
    try:
        if path.stat().st_size > limit:
            scan.skip(relative, "oversize")
            return None
        return path.read_bytes()
    except OSError:
        scan.skip(relative, "unreadable")
        return None


def _scan_file(scan: _Scan, path: Path) -> None:
    """Scan one candidate file, recording why any part of it has no coverage."""
    relative = path.relative_to(scan.root).as_posix()
    suffix = path.suffix.lower()
    if suffix in OPAQUE_SUFFIXES:
        scan.skip(relative, "opaque-or-compressed-payload")
        return
    if suffix in OOXML_SUFFIXES or suffix in PDF_SUFFIXES:
        blob = _file_bytes(scan, relative, path, limit=MAX_CONTAINER_BYTES)
        if blob is None:
            return
        parts = _zip_texts(path) if suffix in OOXML_SUFFIXES else _pdf_texts(blob)
        if not parts:
            scan.skip(relative, "container-unreadable")
            return
        scan.container_files += 1
        for part in parts:
            _inspect_text(scan, relative, part)
        return
    blob = _file_bytes(scan, relative, path, limit=MAX_TEXT_BYTES)
    if blob is not None:
        _read_text(scan, relative, blob)


def _submodule_paths(root: Path) -> frozenset[str]:
    """Return the declared submodule paths, whose content belongs to another repository."""
    try:
        text = (root / ".gitmodules").read_text(encoding="utf-8")
    except OSError:
        return frozenset[str]()
    return frozenset(cast("str", match.group(1)).strip() for match in GITMODULES_PATH_PATTERN.finditer(text))


def _included_file(path: Path) -> bool:
    """Return whether a file is inside the scan scope by name."""
    return (
        path.name not in EXCLUDED_FILE_NAMES
        and path.suffix.lower() not in EXCLUDED_FILE_SUFFIXES
        and not path.name.startswith(EXCLUDED_FILE_PREFIXES)
    )


def repository_files(root: Path) -> Iterator[Path]:
    """Yield every in-scope file below the root, pruning local and generated scopes.

    Args:
        root: Repository root.

    Yields:
        Path: Absolute paths of files that the scan treats as repository content.
    """
    submodules = _submodule_paths(root)
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(directory.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name in EXCLUDED_DIRECTORIES or entry.name.startswith(EXCLUDED_DIRECTORY_PREFIXES):
                    continue
                if entry.relative_to(root).as_posix() in submodules:
                    continue
                stack.append(entry)
            elif _included_file(entry):
                yield entry


def _validate_allowances(allowances: Sequence[Allowance]) -> None:
    """Reject exemptions that are unreviewed, duplicated or incomplete.

    Raises:
        ValueError: If a reason is missing, a selector is empty, or an entry duplicates another.
    """
    if any(not allowance.reason.strip() for allowance in allowances):
        msg = "Every exemption requires a written reason"
        raise ValueError(msg)
    if any(not allowance.rule or not allowance.path or not allowance.value for allowance in allowances):
        msg = "Exemptions require a rule, a path and a value"
        raise ValueError(msg)
    if len({(item.rule, item.path, item.value) for item in allowances}) != len(allowances):
        msg = "Duplicate exemption"
        raise ValueError(msg)


# Exemptions are empty by design: every false positive proven so far is already excluded
# by a rule (reserved email domains, URL userinfo, and bare digit runs that are not
# identifiers), so no exemption is currently justified. An entry is added only with a
# written reason, and ``unused_exemptions`` then fails the gate once it stops being
# needed, so an exemption can never quietly widen the scan.
ALLOWANCES: tuple[Allowance, ...] = ()


def scan_repository(root: Path, allowances: Sequence[Allowance] = ALLOWANCES) -> Report:
    """Scan the repository tree and report findings, exemptions and coverage.

    Args:
        root: Repository root to walk.
        allowances: Reviewed exemptions; empty in normal use.

    Returns:
        Report: Findings, applied exemptions, stale exemptions and coverage counts.

    Raises:
        ValueError: If an exemption is malformed or the root is not a directory.
    """
    _validate_allowances(allowances)
    if not root.is_dir():
        msg = "Repository root is not a directory"
        raise ValueError(msg)
    scan = _Scan(root.resolve(), allowances, [], set(), [])
    for path in repository_files(scan.root):
        _scan_file(scan, path)
    return Report(
        scanned_files=scan.text_files + scan.container_files,
        text_files=scan.text_files,
        container_files=scan.container_files,
        findings=tuple(sorted(scan.findings, key=lambda item: (item.path, item.line, item.rule))),
        exemptions=tuple(item for index, item in enumerate(allowances) if index in scan.used),
        unused_exemptions=tuple(item for index, item in enumerate(allowances) if index not in scan.used),
        not_scanned=tuple(sorted(scan.not_scanned, key=lambda item: item.path)),
    )


def _report_body(report: Report) -> dict[str, object]:
    """Build the JSON receipt body, which contains no matched content.

    Returns:
        dict[str, object]: A serialisable receipt with counts, findings and coverage gaps.
    """
    reasons: dict[str, list[str]] = {}
    for entry in report.not_scanned:
        reasons.setdefault(entry.reason, []).append(entry.path)
    return {
        "passed": report.passed,
        "scanned_files": report.scanned_files,
        "text_files": report.text_files,
        "container_files": report.container_files,
        "findings_count": len(report.findings),
        "findings": [
            {"rule": item.rule, "path": item.path, "line": item.line, "detail": item.detail} for item in report.findings
        ],
        "exemptions": [_exemption_body(item) for item in report.exemptions],
        "unused_exemptions": [_exemption_body(item) for item in report.unused_exemptions],
        "not_scanned": {reason: sorted(paths) for reason, paths in sorted(reasons.items())},
    }


def _exemption_body(item: Allowance) -> dict[str, str]:
    """Return one exemption as a serialisable record."""
    return {"rule": item.rule, "path": item.path, "value": item.value, "reason": item.reason}


def main() -> int:
    """Run the identifier scan and emit a content-free receipt.

    Returns:
        int: 0 when the tree is clean, 1 when a finding or a stale exemption remains.
    """
    parser = argparse.ArgumentParser(description="Scan repository content for personal identifiers.")
    _ = parser.add_argument("--root", default=str(ROOT), help="Repository root to scan")
    _ = parser.add_argument("--output", help="Write the JSON receipt to this path")
    args = cast("_CliArgs", cast("object", parser.parse_args()))
    report = scan_repository(Path(args.root))
    for item in report.findings:
        label = f" [{item.detail}]" if item.detail else ""
        print(f"FINDING {item.rule}: {item.path}:{item.line}{label}")  # ruff: ignore[print] -- findings carry no matched content
    if report.unused_exemptions:
        print("STALE   exemptions that suppressed nothing:")  # ruff: ignore[print] -- CLI summary goes to stdout
        for item in report.unused_exemptions:
            print(f"        {item.rule} {item.path} {item.value}")  # ruff: ignore[print] -- CLI summary goes to stdout
    scanned = f"Scanned {report.scanned_files} files ({report.text_files} text, {report.container_files} containers)"
    gaps = f"{len(report.findings)} finding(s); {len(report.not_scanned)} file(s) without text coverage"
    print(f"{scanned}; {gaps}")  # ruff: ignore[print] -- CLI summary goes to stdout
    if args.output is not None:
        destination = Path(args.output)
        _ = destination.parent.mkdir(parents=True, exist_ok=True)
        _ = destination.write_text(json.dumps(_report_body(report), indent=2) + "\n", encoding="utf-8")
    return int(not report.passed)


if __name__ == "__main__":
    raise SystemExit(main())
