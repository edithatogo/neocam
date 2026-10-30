# ruff: ignore[implicit-namespace-package] -- standalone build script; scripts/ ships no package __init__
"""Editable deterministic pilot + explicitly frozen v2 state/PSA evidence snapshots."""

import csv
import json
import math
from pathlib import Path

from artifact_tool import SpreadsheetFile, Workbook

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/v2"
r = json.loads((OUT / "results_v2.json").read_text())
p = r["assumptions"]
wb = Workbook.create()
TEAL = "#2F8993"
DARK = "#15535C"
WHITE = "#FFFFFF"
YELLOW = "#FFF2CC"
MONEY = "$#,##0;[Red]($#,##0);\u2013"
PCT = "0.0%"
NUM = "#,##0.0;[Red](#,##0.0);\u2013"


def col(n: int) -> str:
    """Convert a 1-based column number to its spreadsheet letter.

    Returns:
        The A1-notation column label.
    """
    out = ""
    while n:
        n, a = divmod(n - 1, 26)
        out = chr(65 + a) + out
    return out


def sheet(name: str, title: str, headers: list[object], widths: list[int]) -> object:
    """Add a titled, frozen-header worksheet and set its column widths.

    Returns:
        The new worksheet.
    """
    s = wb.worksheets.add(name)
    end = col(len(headers))
    s.merge_cells(f"A1:{end}1")
    s.get_range("A1").values = [[title]]
    s.get_range(f"A1:{end}1").format = {
        "fill": DARK,
        "font": {"bold": True, "color": WHITE, "size": 15},
        "row_height": 30,
    }
    s.get_range(f"A3:{end}3").values = [headers]
    s.get_range(f"A3:{end}3").format = {
        "fill": TEAL,
        "font": {"bold": True, "color": WHITE},
        "wrap_text": True,
        "row_height": 30,
    }
    s.freeze_panes.freeze_rows(3)
    for j, w in enumerate(widths, 1):
        s.get_range(f"{col(j)}:{col(j)}").format.column_width = w
    return s


def csvsheet(name: str, path: str, widths: list[int] | None = None) -> object:
    """Add a worksheet whose rows come from a repository CSV export.

    Returns:
        The new worksheet.
    """
    with Path(ROOT / path).open(newline="", encoding="utf-8") as f:
        data = list(csv.reader(f))
    h = data[0]
    s = sheet(name, name.upper(), h, widths or [min(36, max(13, len(x) + 2)) for x in h])
    body = []
    for row in data[1:]:
        v = []
        for x in row:
            try:
                v.append(float(x) if any(t in x.lower() for t in [".", "e"]) else int(x))
            except ValueError:
                v.append(x)
        body.append(v)
    if body:
        s.get_range(f"A4:{col(len(h))}{len(body) + 3}").values = body
        s.get_range(f"A4:{col(len(h))}{len(body) + 3}").format.wrap_text = True
        s.get_range(f"A4:{col(len(h))}{len(body) + 3}").format.row_height = 44
    return s


summary = sheet(
    "Decision summary",
    "PANDA VISION | V2 | 27 OCTOBER 2026",
    ["Decision measure", "Three-site pilot", "33-site public-spoke scenario"],
    [43, 27, 38],
)
inputs = sheet(
    "Editable inputs",
    "EDITABLE DETERMINISTIC INPUTS | BLUE CELLS",
    ["Parameter", "Value", "Unit", "Evidence / interpretation"],
    [34, 18, 19, 62],
)
base = [
    ("sites", 3, "installations", "User/ELC: Atherton, Mareeba, Innisfail"),
    ("calls_per_pilot_site", 12.5, "consultations/year", "User estimate10\u201315 per site, not observed events"),
    ("equipment_cost", 10000, "AUD/site", "User/ELC estimate; invoice/component verification outstanding"),
    ("life_years", 5, "years", "Assumption; PSA3\u20137"),
    ("discount", 0.05, "rate", "Scenario0/3/5%; annual economic equivalent"),
    ("check_minutes", 10, "min/site/week", "Weekly checks documented; time assumed"),
    ("loaded_hour", 85, "AUD/hour", "Assumed loaded staff rate, not verified award"),
    ("support", 300, "AUD/site/year", "Assumption"),
    ("training", 400, "AUD/site/year", "Assumed readiness/refresher effort"),
    ("workflow_per_call", 75, "AUD/consultation", "Incremental over telephone; not entire consultation"),
    ("reliability", 0.95, "probability", "Assumption; failure falls back to telephone"),
    ("odds_ratio", math.sqrt(0.48), "OR", "Haynes2020 adjustedOR.48; half log effect retained"),
    ("rescue_rate", 0.05, "probability", "Assumption among apparent avoided transfers"),
    ("rescue_premium", 10000, "AUD/rescue", "Assumed extra urgent resource cost"),
    ("road_cost", 4000, "AUD/transfer", "Bottom-up assumed resource cost; notQAS tariff"),
    ("marginal_fraction", 0.5, "avoidable share", "Assumption; allocated vs marginal resource boundary"),
    ("downstream_delta", 2000, "AUD/net transfer", "Assumption; negative scenarios allow added local care"),
    ("family_delta", 1500, "AUD/net transfer", "Societal assumption"),
    ("air_original", 18670, "AUD", "Fox2024 Torres study2018\u201319; source-price year2019 assumed"),
    ("cpi_2019", 115.125, "index oldbase", "ABS annual-average2019"),
    ("cpi_bridge_old", 143.6, "index oldbase", "ABS September2025 quarter"),
    ("cpi_bridge_new", 99.73, "index newbase", "ABS same quarter rebased"),
    ("cpi_target", 102.03, "index newbase", "ABS June2026 month; selected cost point"),
    ("road_share", 0.60, "share", "Regional analyst geographic prior"),
    ("rotary_share", 0.25, "share", "Regional analyst geographic prior"),
    ("fixed_share", 0.15, "share", "Regional analyst geographic prior"),
    ("rotary_multiplier", 1.2, "ratio", "Assumed relative to public air anchor"),
    ("fixed_multiplier", 0.9, "ratio", "Assumed relative to public air anchor"),
    ("NEP26", 7418, "AUD/NWAU", "Official IHACPA 2026\u201327"),
    ("QEP", None, "AUD/QWAU", "Missing: current public numeric QEP not verified"),
    ("NWAU_example", 1, "unit", "Illustrative benchmark; not an assigned neonatal episode"),
    ("QWAU_example", None, "unit", "Missing: local adjustments must not be assumed equal"),
]
rowmap = {x[0]: i for i, x in enumerate(base, 4)}
inputs.get_range(f"A4:D{len(base) + 3}").values = [list(x) for x in base]
inputs.get_range(f"A4:D{len(base) + 3}").format.wrap_text = True
inputs.get_range(f"A4:D{len(base) + 3}").format.row_height = 38
inputs.get_range(f"B4:B{len(base) + 3}").format.font = {"color": "#0000FF"}
inputs.get_range("B33:B35").format.fill = YELLOW


def ref(k: str) -> str:
    """Build an absolute reference to an editable-input cell.

    Returns:
        Sheet-qualified absolute cell reference.
    """
    return f"'Editable inputs'!$B${rowmap[k]}"


case = sheet(
    "Casemix",
    "ASSUMED CASEMIX | NOT ESTIMATED FROM ANZNN",
    ["Stratum", "Share", "Phone transfer probability", "Video transfer probability", "Weighted absolute difference"],
    [24, 15, 24, 24, 27],
)
case.get_range("A4:C6").values = [["Low acuity", 0.35, 0.30], ["Moderate acuity", 0.5, 0.65], ["Critical", 0.15, 0.98]]
for rr in [4, 5]:
    case.get_range(f"D{rr}").formulas = [[f"={ref('odds_ratio')}*C{rr}/(1-C{rr}+{ref('odds_ratio')}*C{rr})"]]
case.get_range("D6").formulas = [["=C6"]]
for rr in range(4, 7):
    case.get_range(f"E{rr}").formulas = [[f"=B{rr}*(C{rr}-D{rr})"]]
case.get_range("B4:E6").format.number_format = PCT
case.get_range("A8:E8").values = [
    ["Critical cases receive no transfer-avoidance credit. Survival/morbidity is evaluated separately.", "", "", "", ""]
]
calc = sheet(
    "Pilot calculation",
    "FORMULA-DRIVEN PILOT | CHANGE INPUTS TO RECALCULATE",
    ["Calculation", "Value", "Interpretation"],
    [40, 23, 62],
)
formula_rows = [
    ("Consultations", f"={ref('sites')}*{ref('calls_per_pilot_site')}", "Consultations, not births"),
    (
        "Indexed air resource anchor",
        f"={ref('air_original')}*{ref('cpi_target')}/({ref('cpi_2019')}*({ref('cpi_bridge_new')}/{ref('cpi_bridge_old')}))",
        "June2026 price point; originalyear assumed2019",
    ),
    (
        "Annualised capital per site",
        f"=IF({ref('discount')}=0,{ref('equipment_cost')}/{ref('life_years')},{ref('equipment_cost')}*{ref('discount')}/(1-(1+{ref('discount')})^-{ref('life_years')}))",
        "Economic equivalent; not current cash outlay",
    ),
    (
        "Annual network economic cost",
        f"={ref('sites')}*(B6+52*{ref('check_minutes')}/60*{ref('loaded_hour')}+{ref('support')}+{ref('training')})+B4*{ref('workflow_per_call')}",
        "Includes training and annualised capital",
    ),
    ("Annual continuation cash cost", f"=B7-{ref('sites')}*B6", "Excludes sunk capital"),
    (
        "Apparent avoided transfers",
        f"=B4*SUM('Casemix'!E4:E6)*{ref('reliability')}",
        "Negative values mean additional transfers",
    ),
    ("Delayed rescue episodes", f"=MAX(B9,0)*{ref('rescue_rate')}", "Among apparent avoided transfers"),
    ("Net avoided transfers", "=B9-B10", "Apparent avoided less later rescues"),
    (
        "Allocated transport resource",
        f"={ref('road_share')}*{ref('road_cost')}+{ref('rotary_share')}*B5*{ref('rotary_multiplier')}+{
            ref('fixed_share')
        }*B5*{ref('fixed_multiplier')}",
        "Geographic shares/mode multipliers are assumptions",
    ),
    ("Avoidable transport resource", f"=B12*{ref('marginal_fraction')}", "Not necessarily cash released"),
    (
        "Gross pathway resource benefit",
        f"=B11*(B13+{ref('downstream_delta')})-B10*{ref('rescue_premium')}",
        "Includes local hospital changes and rescue penalty",
    ),
    ("Health-system net saving", "=B14-B7", "Positive=less valued resource use; not funding"),
    ("Family benefit", f"=B11*{ref('family_delta')}", "Can be negative if more transfer"),
    ("Societal net saving", "=B15+B16", "No unsupported survival effects monetised"),
    ("National benchmark", f"={ref('NWAU_example')}*{ref('NEP26')}", "Funding benchmark, not added to resource ledger"),
    (
        "Queensland benchmark",
        f'=IF(OR({ref("QEP")}="",{ref("QWAU_example")}=""),"",{ref("QEP")}*{ref("QWAU_example")})',
        "Missing remains blank; do not substitute NEP",
    ),
]
for rr, (label, formula, note) in enumerate(formula_rows, 4):
    calc.get_range(f"A{rr}:C{rr}").values = [[label, None, note]]
    calc.get_range(f"B{rr}").formulas = [[formula]]
calc.get_range("A4:C21").format.wrap_text = True
calc.get_range("A4:C21").format.row_height = 32
calc.get_range("B4:B21").format.number_format = MONEY
for rr in [4, 9, 10, 11]:
    calc.get_range(f"B{rr}").format.number_format = NUM
ps = sheet(
    "PSA snapshot",
    "FIXED-SEED PSA SNAPSHOT | RERUN PYTHON AFTER CHANGING ASSUMPTIONS",
    [
        "Portfolio/effect",
        "Mean net saving",
        "Median",
        "2.5%",
        "97.5%",
        "P(cost saving)",
        "Iterations",
        "MCSE probability",
    ],
    [29, 20, 20, 20, 20, 19, 15, 21],
)
for rr, (k, v) in enumerate(r["psa"].items(), 4):
    ps.get_range(f"A{rr}:H{rr}").values = [
        [k, v["mean"], v["median"], v["lower"], v["upper"], v["probability_cost_saving"], v["iterations"], None]
    ]
    ps.get_range(f"H{rr}").formulas = [[f"=SQRT(F{rr}*(1-F{rr})/G{rr})"]]
ps.get_range("B4:E11").format.number_format = MONEY
ps.get_range("F4:F11").format.number_format = PCT
ps.get_range("H4:H11").format.number_format = "0.00%"
# Summary formulas and clearly differentiated state snapshot.
info = [
    ["Historical 2022 births", 486, 28276],
    ["Forecast consultations/year", None, r["deterministic"]["spokes"]["consultations"]],
    ["Deterministic annual programme cost", None, r["deterministic"]["spokes"]["programme_cost"]],
    ["Deterministic net resource saving", None, r["deterministic"]["spokes"]["net_saving"]],
    [
        "PSA probability cost saving",
        r["psa"]["pilot_attenuated"]["probability_cost_saving"],
        r["psa"]["spokes_attenuated"]["probability_cost_saving"],
    ],
    ["PSA mean net resource saving", r["psa"]["pilot_attenuated"]["mean"], r["psa"]["spokes_attenuated"]["mean"]],
    ["PSA median", r["psa"]["pilot_attenuated"]["median"], r["psa"]["spokes_attenuated"]["median"]],
    ["PSA 95% lower", r["psa"]["pilot_attenuated"]["lower"], r["psa"]["spokes_attenuated"]["lower"]],
    ["PSA 95% upper", r["psa"]["pilot_attenuated"]["upper"], r["psa"]["spokes_attenuated"]["upper"]],
]
summary.get_range("A4:C12").values = info
summary.get_range("B4:C4").format.number_format = "#,##0"
summary.get_range("B5:C5").format.number_format = "#,##0.0"
for rr, source in [(5, "B4"), (6, "B7"), (7, "B15")]:
    summary.get_range(f"B{rr}").formulas = [[f"='Pilot calculation'!{source}"]]
summary.get_range("B6:C7").format.number_format = MONEY
summary.get_range("B8:C8").format.number_format = PCT
summary.get_range("B9:C12").format.number_format = MONEY
summary.merge_cells("A15:C16")
summary.get_range("A15").values = [
    [
        (
            "Not demonstrated savings. Reference PSA: researcher assumptions and external evidence, not a fitted local"
            " posterior. State growth preserves shared systematic uncertainty."
        )
    ]
]
summary.get_range("A15:C16").format.wrap_text = True
summary.merge_cells("A18:C20")
summary.get_range("A18").values = [
    [
        (
            "Editing blue input cells recalculates the deterministic pilot only. State, PSA and scenario sheets are"
            " exported snapshots: rerun scripts/run_v2.py and rebuild to update them. New dependencies, hosted CI and"
            " the"
            " Conductor checkout remain blocked; see Assurance."
        )
    ]
]
summary.get_range("A18:C20").format.wrap_text = True
# Tabular comparisons/registries retain row-specific provenance.
csvsheet("State site roster", "outputs/v2/site_projection.csv")
csvsheet("Births source 2022", "data/births_queensland_2022.csv")
csvsheet("Scenarios snapshot", "outputs/v2/scenario_results.csv")
csvsheet("Funding sensitivity", "outputs/v2/funding_sensitivity.csv")
csvsheet("Pilot cash budget", "outputs/v2/pilot_five_year_budget.csv")
csvsheet("State cash budget", "outputs/v2/spokes_five_year_budget.csv")
csvsheet("Clinical frontier", "outputs/v2/survival_morbidity_frontier.csv")
csvsheet("Parameter register", "evidence/parameter_register.csv", [28, 27, 30, 43, 60])
csvsheet("Literature map", "evidence/literature_parameter_map.csv")
csvsheet("Transport comparison", "evidence/transport_mode_comparison.csv")
srcsheet = csvsheet("Sources", "evidence/sources.csv")
srcsheet.get_range("A4:F40").format.row_height = 100
srcsheet.get_range("C:C").format.column_width = 43
srcsheet.get_range("E:E").format.column_width = 65
srcsheet.get_range("F:F").format.column_width = 60
qa = sheet("Assurance", "ACTUAL STATUS | BLOCKED IS NOT PASSED", ["Gate", "Status", "Boundary"], [34, 19, 68])
qa.get_range("A4:C12").values = [
    ["Core test suite", "PASSED", "75 tests; current available environment"],
    ["V2 branch coverage", "PASSED", "96%; minimum95%"],
    ["Data and reproducibility", "PASSED", "Birth totals; deterministic seeds; evidence IDs"],
    ["Latest dependency install", "BLOCKED", "PyPI DNS failed; targetspec is not a resolved lock"],
    ["Ruff / Hypothesis / ty", "BLOCKED", "Tools unavailable locally; configured online"],
    ["Vulnerability audit", "BLOCKED", "pip-audit unavailable; no clean audit claimed"],
    ["Hosted Actions / matrix", "NOT RUN", "No hosted execution receipt"],
    ["Conductor working tree", "BLOCKED", "Configured gitlink; github DNS prevented checkout"],
    ["2026mchs parity", "NOT VERIFIED", "Repo explicitly not validated; officialexport gate"],
]
qa.get_range("A4:C12").format.wrap_text = True
qa.get_range("A4:C12").format.row_height = 36
# Single quantitative summary chart, with explicit frozen PSA interpretation.
ch = ps.charts.add("bar", ps.get_range("A3:B11"))
ch.title_text = "Mean annual net resource saving by effect structure"
ch.has_legend = False
ch.set_position("A15", "H32")
print(  # ruff: ignore[print] -- build script reports the pilot-calculation table to stdout
    wb.inspect({
        "kind": "table",
        "range": "'Pilot calculation'!A4:C21",
        "include": "values,formulas",
        "table_max_rows": 18,
        "table_max_cols": 3,
    }).ndjson
)
print(  # ruff: ignore[print] -- build script reports formula diagnostics to stdout
    wb.inspect({
        "kind": "match",
        "search_term": "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
        "options": {"use_regex": True, "max_results": 20},
    }).ndjson
)
wb.render({"sheet_name": "Decision summary", "range": "A1:C20", "scale": 1.5}).save(str(OUT / "workbook_preview.png"))
SpreadsheetFile.export_xlsx(wb).save(str(OUT / "Panda_Vision_economic_model_v2.xlsx"))
print("EXPORTED", OUT / "Panda_Vision_economic_model_v2.xlsx")  # ruff: ignore[print] -- build script reports the output path to stdout
