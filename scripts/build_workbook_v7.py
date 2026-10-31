# ruff: ignore[implicit-namespace-package] -- standalone workbook builder, not a package module
"""Build the v7 inspectable results workbook using artifact_tool."""

import csv
import json
from pathlib import Path

from artifact_tool import SpreadsheetFile, Workbook

try:  # imported as ``scripts.document_metadata`` when the repository root is on sys.path
    from scripts.document_metadata import neutralise_archive_metadata
except ModuleNotFoundError:  # run directly as ``python scripts/build_workbook_v7.py``
    from document_metadata import neutralise_archive_metadata

root = Path(__file__).resolve().parents[1]
out = root / "outputs/v7"
results = json.loads((out / "results_v7.json").read_text())
wb = Workbook.create()
sheets = []
EXACT_INT_LIMIT = 1e15


def col(n: int) -> str:
    """Return the spreadsheet column label for a 1-based column index."""
    text = ""
    while n:
        n, x = divmod(n - 1, 26)
        text = chr(65 + x) + text
    return text


def number(value: object) -> object:
    """Coerce CSV text to bool, int or float where the value is unambiguous.

    Returns:
        The coerced value, or the original text when no numeric form applies.
    """
    if not isinstance(value, str):
        return value
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        n = float(value)
        return int(n) if n.is_integer() and abs(n) < EXACT_INT_LIMIT else n
    except ValueError:
        return value


def sheet(  # ruff: ignore[too-many-arguments, too-many-positional-arguments] -- published workbook-sheet helper
    name: str,
    title: str,
    note: str,
    headers: list[str],
    records: list[list],
    narrative: bool = False,  # ruff: ignore[boolean-default-value-positional-argument, boolean-type-hint-positional-argument] -- published flag
) -> object:
    """Add a titled worksheet with a styled header and coerced record values.

    Returns:
        The created artifact_tool worksheet object.
    """
    sh = wb.worksheets.add(name)
    width = col(len(headers))
    sh.get_range("A1").values = [[title]]
    sh.get_range("A1").format.font = {"bold": True, "size": 15, "color": "#15535C"}
    sh.merge_cells(f"A2:{width}2")
    sh.get_range("A2").values = [[note]]
    sh.get_range(f"A2:{width}2").format.wrap_text = True
    sh.get_range(f"A2:{width}2").format.row_height = 42
    sh.get_range(f"A4:{width}4").values = [headers]
    sh.get_range(f"A4:{width}4").format = {
        "fill": "#15535C",
        "font": {"bold": True, "color": "#FFFFFF"},
        "wrap_text": True,
        "row_height": 40,
    }
    if records:
        sh.get_range_by_indexes(4, 0, len(records), len(headers)).values = [[number(v) for v in row] for row in records]
    sh.get_range(f"A4:{width}{max(5, 4 + len(records))}").format.column_width = 21
    sh.get_range(f"A5:A{max(5, 4 + len(records))}").format.column_width = 30
    sh.freeze_panes.freeze_rows(4)
    if narrative:
        sh.get_range_by_indexes(4, 0, len(records), len(headers)).format.wrap_text = True
        sh.get_range_by_indexes(4, 0, len(records), len(headers)).format.row_height = 72
        sh.get_range(f"B4:{width}{4 + len(records)}").format.column_width = 43
    sheets.append((name, len(records), len(headers)))
    return sh


def csvsheet(
    name: str,
    path: str | Path,
    note: str,
    narrative: bool = False,  # ruff: ignore[boolean-default-value-positional-argument, boolean-type-hint-positional-argument] -- published flag
) -> object:
    """Add a worksheet populated from a CSV file on disk.

    Returns:
        The created artifact_tool worksheet object.
    """
    with Path(path).open(newline="", encoding="utf-8") as f:
        data = list(csv.reader(f))
    return sheet(name, name, note, data[0], data[1:], narrative)


readme = [
    [
        "Scope",
        "Four portfolios and six evaluative views; five complete configurations. No proven clinical benefit or procurement approval.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Regional coverage",
        "10 CHHHS hospital/emergency locations; 14 including four TCHHS hospitals. Not every primary/community clinic or a verified installation list.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Perspectives",
        "State + Commonwealth + patient/family reconcile to the bounded societal result. CHHHS is nested, not added again.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Funding",
        "Government results are hypothetical funding-adjusted resource allocations, not actual cash entitlements. Current QEP/local QWAU inputs remain unverified.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Value of perspective",
        "Fixed expected-value choices, evaluated under another perspective; ties split explicitly. This is not per-draw perfect information or a population multiplier.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "HRQoL",
        "EPICure2 age11 cohort utilities inform only illustrative bridges. No QALY/DALY improvement is credited in the reference model.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Simulation",
        "44 structures × 20,000 paired draws; shared uncertainty across sites and options. Researcher priors, not fitted local posterior probabilities.",  # ruff: ignore[line-too-long, ambiguous-unicode-character-string] -- authored report text kept verbatim
    ],
    ["Review", "Four simulated role-based author reviews; no independent agents or professional sign-off."],
    [
        "Source archive",
        "Supplied corporate originals, restricted selected ELC excerpt and labelled transcriptions saved. Original public PDFs/XLSX downloads failed; archival completeness is not claimed.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Recalculation",
        "Python produces simulation results. Formula cells check exported accounting. Spreadsheet edits do not recalculate PSA.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
    [
        "Assurance",
        "Ordinary tests and output checks have separate receipts. Full Gitleaks/latest toolchain/lock/hosted CI/Conductor checkout remain unverified when unavailable.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ],
]
sh = sheet(
    "Read me",
    "Panda Vision — regional perspectives v7",
    "28 October 2026 | Private working analysis | AUD unless stated",
    ["Topic", "Interpretation"],
    readme,
    narrative=True,
)
sh.get_range("B4:B15").format.column_width = 105
sh.get_range("A5:B15").format.row_height = 47
with (out / "psa_perspectives.csv").open() as f:
    psa = list(csv.DictReader(f))
summary = [
    [v[k] for k in ("portfolio", "strategy", "mean", "lower", "upper", "probability_positive", "probability_optimal")]
    for v in psa
    if v["scenario"] == "reference" and v["perspective"] == "health_system"
]
sh = sheet(
    "Regional summary",
    "Five-option reference health-system comparison",
    "Equal video effects are a hypothesis. A lower-priced conceptual kit is not an approved clinical equivalent.",
    ["Portfolio", "Strategy", "Expected net/year", "2.5%", "97.5%", "P(saving)", "P(optimal)"],
    summary,
)
sh.get_range("C5:E24").set_number_format("#,##0;[Red](#,##0);–")  # ruff: ignore[ambiguous-unicode-character-string] -- deliberate typographic character in authored text
sh.get_range("F5:G24").set_number_format("0.0%")
with (out / "deterministic.csv").open() as f:
    det = list(csv.DictReader(f))
rr = [
    [
        v["portfolio"],
        v["strategy"],
        v["consultations"],
        v["immediate_transfers"],
        v["delayed_rescues"],
        v["final_local"],
        None,
        v["state_net"],
        v["commonwealth_net"],
        v["patient_family_net"],
        v["societal_bounded_net"],
        None,
    ]
    for v in det
]
sh = sheet(
    "Accounting checks",
    "Exact cohort and perspective reconciliation",
    "Both residual columns should be near zero. Provider CHHHS is a nested view, not an additional cost to add.",
    [
        "Portfolio",
        "Strategy",
        "Consultations",
        "Immediate",
        "Rescue",
        "Final local",
        "Cohort residual",
        "State net",
        "Commonwealth net",
        "Patient/family net",
        "Societal net",
        "Ledger residual",
    ],
    rr,
)
for row in range(5, 5 + len(rr)):
    sh.get_range(f"G{row}").formulas = [[f"=C{row}-SUM(D{row}:F{row})"]]
    sh.get_range(f"L{row}").formulas = [[f"=SUM(H{row}:J{row})-K{row}"]]
sh.get_range("C5:L24").set_number_format("#,##0.00;[Red](#,##0.00);–")  # ruff: ignore[ambiguous-unicode-character-string] -- deliberate typographic character in authored text
for name, file, note in [
    (
        "PSA all views",
        "psa_perspectives.csv",
        "44 structures × 20,000 draws × six views × five options. Government allocation scenarios are not forecasts of actual payment.",  # ruff: ignore[line-too-long, ambiguous-unicode-character-string] -- authored report text kept verbatim
    ),
    (
        "Value of perspective",
        "value_of_perspective.csv",
        "Fixed-choice directional regret, with explicit expected-value ties and tie-specific bounds. Network-year values are already aggregated.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ),
    (
        "Established options",
        "established_options.csv",
        "Excludes the unapproved prototype. Local technical suitability of established categories still requires assessment.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ),
    (
        "Regional roster",
        "regional_roster.csv",
        "Missing historical births are not observed zeros; these hospital/emergency scenarios exclude community clinics.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ),
    (
        "Absolute pathways",
        "deterministic.csv",
        "Immediate + rescue + final local = consultations. Expected counts are not observed patients.",
    ),
    ("Reconciliation", "reconciliation.csv", "Maximum absolute residuals across all exact paired draws."),
    (
        "Allocation surface",
        "allocation_two_way.csv",
        "Exact two-way cost-allocation grid. Grid frequencies are not probability distributions.",
    ),
    (
        "Structural scenarios",
        "structural_scenarios.csv",
        "Null, sceptical and unattenuated-effect structures; reopening, readiness, incumbent, prototype and allocation alternatives.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ),
    (
        "Health thresholds",
        "health_thresholds.csv",
        "No-transfer-benefit health thresholds; hypothetical values per QALY, not official thresholds or measured effects.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
    ),
    (
        "Utility bridge",
        "utility_bridge_scenarios.csv",
        "Source utility differences are not treatment effects. Duration and improved fraction are explicitly assumed.",
    ),
]:
    csvsheet(name, out / file, note)
csvsheet(
    "Parameter audit",
    root / "evidence/v7/parameter_audit.csv",
    "49 fields, including retired historical inputs; verification of provenance does not validate an assumption.",
    narrative=True,
)
csvsheet(
    "Method assumptions",
    root / "evidence/v7/method_assumptions.csv",
    "30 additional existing numerical/structural assumptions; not new fitted parameters.",
    narrative=True,
)
csvsheet(
    "Source register",
    root / "sources/source_register.csv",
    "Source links and limits; not all original bytes have been acquired.",
    narrative=True,
)
csvsheet(
    "NEP transcription",
    root / "sources/extracts/IHACPA_NEP26_verified_rows.csv",
    "Verified Appendix H rows transcribed from PDF; this is not the original price-weight workbook or patient-level NWAU.",  # ruff: ignore[line-too-long] -- authored report text kept verbatim
)
csvsheet(
    "NHRA floors",
    root / "sources/extracts/NHRA_2026_2031_input_rate_floor.csv",
    "Input-rate floors subject to other provisions/caps, not automatic marginal episode coefficients.",
    narrative=True,
)
csvsheet(
    "HRQoL source",
    root / "sources/extracts/EPICure2_utility_extract.csv",
    "Distinct instruments/tariffs and childhood proxy reports. Full body reviewed; supplementary files not acquired.",
)
csvsheet(
    "Full-text status",
    root / "evidence/v6/full_text_verification.csv",
    "Retained critical-source retrieval status; four core papers remain inaccessible in full.",
    narrative=True,
)
print("Sheets:", len(sheets), "rows:", sum(n for _, n, _ in sheets))  # ruff: ignore[print] -- script status line goes to stdout
print(wb.inspect({"kind": "region", "sheet_id": "Accounting checks", "range": "G4:L8", "max_chars": 1800}).ndjson)  # ruff: ignore[print] -- CLI inspection report goes to stdout
SpreadsheetFile.export_xlsx(wb).save(str(out / "Panda_Vision_analysis_v7.xlsx"))
neutralise_archive_metadata(out / "Panda_Vision_analysis_v7.xlsx")
wb.render({"sheet_name": "Regional summary", "range": "A1:G10", "scale": 1.4}).save(str(out / "workbook_preview.png"))
