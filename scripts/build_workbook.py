# ruff: ignore[implicit-namespace-package] -- standalone build script; scripts/ ships no package __init__
"""Build the v1 Panda Vision economic-model workbook and its preview chart."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from artifact_tool import SpreadsheetFile, Workbook

from src.panda_model import (
    ModelInputs,
    annual_programme_cost,
    clinical_extension,
    deterministic_scenario,
    run_psa,
    weighted_transfer_cost,
)

OUT = "outputs/Panda_Vision_economic_model_v1.xlsx"
x = ModelInputs()
psa = run_psa(20000, 20261027)
prog = annual_programme_cost(x)

wb = Workbook.create()
# palette
TEAL = "#2F8993"
DARK = "#15535C"
LIGHT = "#DDEEF0"
PALE = "#F3F8F8"
GOLD = "#F9C665"
GREEN = "#709C58"
GREY = "#666666"
WHITE = "#FFFFFF"
BLUE = "#0000FF"
BLACK = "#000000"
RED = "#C00000"
YELLOW = "#FFF2CC"
fmt_money = "$#,##0;[Red]($#,##0);-"
fmt_num = "#,##0.0;[Red](#,##0.0);-"
fmt_pct = "0.0%;[Red](0.0%);-"


def title(sheet: object, text: str, end_col: str) -> None:
    """Merge, fill and freeze a worksheet title band."""
    sheet.merge_cells(f"A1:{end_col}1")
    r = sheet.get_range(f"A1:{end_col}1")
    r.values = [[text]]
    r.format = {
        "fill": DARK,
        "font": {"bold": True, "color": WHITE, "size": 16},
        "row_height": 28,
        "vertical_alignment": "center",
    }
    sheet.freeze_panes.freeze_rows(3)


def header(r: object) -> None:
    """Apply the header fill, font and wrapping to a range."""
    r.format = {"fill": TEAL, "font": {"bold": True, "color": WHITE}, "wrap_text": True, "vertical_alignment": "center"}


def input_font(r: object) -> None:
    """Mark a range as editable input (blue)."""
    r.format.font = {"color": BLUE}


def formula_font(r: object) -> None:
    """Mark a range as a calculated formula (black)."""
    r.format.font = {"color": BLACK}


def source_font(r: object) -> None:
    """Mark a range as a provenance source (green)."""
    r.format.font = {"color": "#008000"}


# Dashboard
s = wb.worksheets.add("Decision summary")
title(s, "PANDA VISION | MODEL-BASED ECONOMIC EVALUATION", "H")
s.get_range("A3:H3").values = [
    [
        "Decision question",
        "Current pilot",
        "Annual activity",
        "Economic cost",
        "Break-even effect",
        "PSA cost-saving",
        "PSA median net",
        "95% interval",
    ]
]
header(s.get_range("A3:H3"))
base = deterministic_scenario(x)
s.get_range("A4:H4").values = [
    [
        "Invest in/continue video-enabled neonatal consultation",
        "Atherton, Mareeba, Innisfail",
        prog["consultations"],
        prog["total_economic"],
        base["break_even_effect"],
        psa["summary"]["probability_cost_saving"],
        psa["summary"]["median_net_saving"],
        f"${psa['summary']['net_saving_p025']:,.0f} to ${psa['summary']['net_saving_p975']:,.0f}",
    ]
]
s.get_range("C4").format.number_format = fmt_num
s.get_range("D4").format.number_format = fmt_money
s.get_range("E4:F4").format.number_format = fmt_pct
s.get_range("G4").format.number_format = fmt_money
s.merge_cells("A7:H7")
s.get_range("A7").values = [["INTERPRETATION"]]
header(s.get_range("A7:H7"))
s.get_range("A8:H11").values = [
    ["Finding", "Meaning", "", "", "", "", "", ""],
    [
        "The programme can be cost-saving with small transfer effects",
        (
            "At base costs, break-even is an absolute reduction of about 2 percentage points across all consultations."
            " This is not an observed local effect."
        ),
        "",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "Uncertainty is material",
        (
            "The PSA allows video to increase transfers and produces a wide interval. The probability of cost-saving"
            " is a"
            " decision aid, not proof."
        ),
        "",
        "",
        "",
        "",
        "",
        "",
    ],
    [
        "Clinical value is not exhausted by transfer avoidance",
        (
            "Earlier procedures, better stabilisation, family communication and survival/morbidity remain separate"
            " consequences."
        ),
        "",
        "",
        "",
        "",
        "",
        "",
    ],
]
header(s.get_range("A8:B8"))
s.get_range("A8:H11").format.wrap_text = True
s.merge_cells("A13:H13")
s.get_range("A13").values = [["RECOMMENDATION"]]
header(s.get_range("A13:H13"))
s.merge_cells("A14:H16")
s.get_range("A14").values = [
    [
        (
            "Continue the existing pilot while completing a retrospective review of the 4\u20135 Atherton episodes and"
            " verifying invoices, installed components and retrieval-mode costs. Use the model for local, state and"
            " national investment decisions, with deterministic scenarios and PSA rather than a single point estimate."
            " Treat a tablet-integrated configuration as an engineering/ICT option requiring BTS, eHealth and QH Portal"
            " validation\u2014not as an already approved product."
        )
    ]
]
s.get_range("A14:H16").format.wrap_text = True
for c, w in zip("ABCDEFGH", [26, 22, 13, 15, 15, 14, 15, 20], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w

# Inputs
s = wb.worksheets.add("Inputs")
title(s, "MODEL INPUTS, DISTRIBUTIONS AND PROVENANCE", "G")
s.get_range("A3:G3").values = [["Parameter", "Base", "Low", "High", "Unit", "Status", "Source / rationale"]]
header(s.get_range("A3:G3"))
rows = [
    ["Sites", 3, 3, 3, "sites", "Documented", "ELC 21 Oct 2026"],
    [
        "Consultations per site-year",
        12.5,
        10,
        15,
        "consultations",
        "User-confirmed estimate",
        "Nicholas Cairns meeting; 4\u20135 episodes at Atherton to date",
    ],
    [
        "Installed cost per site",
        10000,
        9000,
        12000,
        "AUD",
        "Verify invoice",
        "ELC presentation states $10k; user confirms per installation",
    ],
    ["Useful life", 5, 3, 7, "years", "Assumption", "Scenario range"],
    ["Weekly check time", 10, 5, 20, "minutes/site", "Assumption", "ELC says weekly checks; duration unreported"],
    ["Loaded staff rate", 85, 70, 110, "AUD/hour", "Assumption", "Replace with Queensland award/on-cost schedule"],
    ["Annual support", 300, 0, 1000, "AUD/site", "Assumption", "Warranty/support not documented"],
    [
        "Incremental video workflow",
        75,
        25,
        175,
        "AUD/consult",
        "Assumption",
        "Consultation occurs in both arms; only extra video/setup time",
    ],
    [
        "Usual-care transfer probability",
        0.65,
        0.20,
        0.85,
        "probability",
        "External-informed prior",
        "California study 82%; deliberately discounted and widened",
    ],
    [
        "Video transfer odds ratio",
        0.70,
        0.35,
        1.40,
        "odds ratio",
        "External-informed prior",
        "Adjusted OR 0.48 in Haynes 2020; base shrunk toward null",
    ],
    [
        "Road share",
        25 / 45,
        0.25,
        0.70,
        "share",
        "Queensland neonatal prior",
        "NeoSTRESS: 25 road, 9 rotary, 11 fixed-wing outbound legs",
    ],
    ["Rotary share", 9 / 45, 0.10, 0.35, "share", "Queensland neonatal prior", "Mode shares scenario-tested"],
    [
        "Fixed-wing share",
        11 / 45,
        0.15,
        0.55,
        "share",
        "Queensland neonatal prior",
        "Current QAS public reports do not provide neonatal mode mix",
    ],
    [
        "Road transport cost",
        4000,
        2000,
        8000,
        "AUD/transfer",
        "Reasoned assumption",
        "Marginal asset/crew resource estimate",
    ],
    [
        "Rotary transport cost",
        25000,
        15000,
        45000,
        "AUD/transfer",
        "Reasoned assumption",
        "User-pays aeromedical asset; contract price not public",
    ],
    [
        "Fixed-wing transport cost",
        18000,
        10000,
        30000,
        "AUD/transfer",
        "Reasoned assumption",
        "User-pays aeromedical asset; contract price not public",
    ],
    [
        "Net downstream hospital difference",
        4000,
        0,
        12000,
        "AUD/transfer",
        "IHACPA-informed assumption",
        "Use routine DRG/NWAU extract when available",
    ],
    [
        "Family burden per transfer",
        1500,
        500,
        4000,
        "AUD/transfer",
        "Societal assumption",
        "Travel, accommodation, time and separation",
    ],
    [
        "NEP 2026\u201327",
        7418,
        7418,
        7418,
        "AUD/NWAU",
        "Official",
        "https://www.ihacpa.gov.au/resources/national-efficient-price-determination-2026-27",
    ],
    ["WTP per QALY", 50000, 0, 100000, "AUD/QALY", "Exploratory only", "Not used in primary cost analysis"],
]
s.get_range(f"A4:G{3 + len(rows)}").values = rows
input_font(s.get_range(f"B4:D{3 + len(rows)}"))
source_font(s.get_range(f"G4:G{3 + len(rows)}"))
s.get_range("B12:D16").format.number_format = fmt_pct
s.get_range(f"B4:D{3 + len(rows)}").conditional_formats.add_custom(
    '=OR($F4="Verify invoice",$F4="Assumption",$F4="Reasoned assumption",$F4="IHACPA-informed assumption")',
    {"fill": YELLOW},
)
for c, w in zip("ABCDEFG", [32, 12, 12, 12, 18, 24, 60], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w
s.get_range(f"A3:G{3 + len(rows)}").format.wrap_text = True

# Deterministic scenarios
s = wb.worksheets.add("Scenario analysis")
title(s, "DETERMINISTIC SCENARIOS | ANNUAL RESULTS", "I")
s.get_range("A3:I3").values = [
    [
        "Scenario",
        "Consult/site",
        "Transfer reduction",
        "Avoided transfers",
        "Programme cost",
        "Weighted transfer cost",
        "Health-system net",
        "Societal net",
        "Interpretation",
    ]
]
header(s.get_range("A3:I3"))
scens = [
    ("No transfer effect", 12.5, 0.00),
    ("Conservative", 10, 0.03),
    ("Break-even vicinity", 12.5, 0.02),
    ("Moderate", 12.5, 0.08),
    ("Observed California raw difference", 12.5, 0.18),
    ("Historical Queensland stress test", 12.5, 0.26),
    ("High volume/moderate effect", 15, 0.08),
]
out = []
for name, cps, e in scens:
    r = deterministic_scenario(x, e, cps)
    out.append([
        name,
        cps,
        e,
        r["avoided_transfers"],
        r["programme_cost"],
        r["weighted_transfer_cost"],
        r["net_saving_health_system"],
        r["net_saving_societal"],
        "Conditional estimate; not local observed effect",
    ])
s.get_range(f"A4:I{3 + len(out)}").values = out
s.get_range(f"B4:B{3 + len(out)}").format.number_format = fmt_num
s.get_range(f"C4:C{3 + len(out)}").format.number_format = fmt_pct
s.get_range(f"D4:D{3 + len(out)}").format.number_format = fmt_num
s.get_range(f"E4:H{3 + len(out)}").format.number_format = fmt_money
s.get_range(f"G4:G{3 + len(out)}").conditional_formats.add_color_scale({
    "minColor": "#F4CCCC",
    "midColor": "#FFF2CC",
    "maxColor": "#D9EAD3",
})
chart = s.charts.add("column", s.get_range(f"A3:A{3 + len(out)}").resize(len(out) + 1, 7))
chart.title_text = "Annual health-system net saving by scenario"
chart.has_legend = False
chart.set_position("A14", "I31")
for c, w in zip("ABCDEFGHI", [32, 12, 14, 14, 15, 16, 16, 16, 42], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w
s.get_range(f"A3:I{3 + len(out)}").format.wrap_text = True

# PSA
s = wb.worksheets.add("Probabilistic analysis")
title(s, "PROBABILISTIC SENSITIVITY ANALYSIS | 20,000 ITERATIONS", "F")
s.get_range("A3:B3").values = [["Measure", "Result"]]
header(s.get_range("A3:B3"))
sumr = psa["summary"]
metrics = [
    ["Probability cost-saving", sumr["probability_cost_saving"]],
    ["Mean health-system net saving", sumr["mean_net_saving"]],
    ["Median health-system net saving", sumr["median_net_saving"]],
    ["95% lower bound", sumr["net_saving_p025"]],
    ["95% upper bound", sumr["net_saving_p975"]],
    ["Mean societal net saving", sumr["mean_societal_net_saving"]],
    ["Mean avoided transfers/year", sumr["mean_avoided_transfers"]],
    ["Mean annual programme cost", sumr["mean_programme_cost"]],
    ["Mean cost per transfer avoided", sumr["mean_transfer_cost"]],
    ["Mean absolute transfer effect", sumr["transfer_effect_mean"]],
    ["Transfer-effect 95% lower", sumr["transfer_effect_p025"]],
    ["Transfer-effect 95% upper", sumr["transfer_effect_p975"]],
]
s.get_range(f"A4:B{3 + len(metrics)}").values = metrics
s.get_range("B4").format.number_format = fmt_pct
s.get_range("B5:B9").format.number_format = fmt_money
s.get_range("B10").format.number_format = fmt_num
s.get_range("B11:B12").format.number_format = fmt_money
s.get_range("B13:B15").format.number_format = fmt_pct
s.get_range("D3:E3").values = [["Net saving midpoint", "Simulation count"]]
header(s.get_range("D3:E3"))
hist = [[h["midpoint"], h["count"]] for h in psa["histogram"]]
s.get_range(f"D4:E{3 + len(hist)}").values = hist
s.get_range(f"D4:D{3 + len(hist)}").format.number_format = fmt_money
chart = s.charts.add("column", s.get_range(f"D3:E{3 + len(hist)}"))
chart.title_text = "Distribution of annual health-system net saving"
chart.has_legend = False
chart.set_position("G3", "N20")
s.merge_cells("A18:F18")
s.get_range("A18").values = [
    [
        (
            "PSA distributions: activity triangular 10/12.5/15 per site; usual transfer beta mean 65%; video OR"
            " lognormal"
            " median 0.70; transport shares Dirichlet 25/9/11; costs lognormal/triangular. The transfer effect can"
            " cross"
            " zero."
        )
    ]
]
s.get_range("A18:F18").format.wrap_text = True
for c, w in zip("ABCDEF", [34, 18, 4, 18, 16, 10], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w

# Transport
s = wb.worksheets.add("Retrieval assumptions")
title(s, "RETRIEVAL MODE AND COST ASSUMPTIONS", "G")
s.get_range("A3:G3").values = [
    ["Mode", "Base share", "Low-air scenario", "High-air scenario", "Base marginal cost", "Evidence", "Limit"]
]
header(s.get_range("A3:G3"))
transport_rows = [
    ["Road", 25 / 45, 0.60, 0.25, 4000, "NeoSTRESS 25/45 outbound legs", "Not a current FNQ consultation cohort"],
    ["Rotary", 9 / 45, 0.15, 0.25, 25000, "NeoSTRESS 9/45 outbound legs", "Current contract cost unavailable publicly"],
    [
        "Fixed wing",
        11 / 45,
        0.25,
        0.50,
        18000,
        "NeoSTRESS 11/45 outbound legs",
        "Current contract cost unavailable publicly",
    ],
    [
        "Total",
        1,
        1,
        1,
        None,
        "https://pubmed.ncbi.nlm.nih.gov/32949204/",
        "QAS 2025-26 performance gives total RSQ activity, not mode split",
    ],
]
s.get_range("A4:G7").values = transport_rows
s.get_range("B4:D7").format.number_format = fmt_pct
s.get_range("E4:E6").format.number_format = fmt_money
source_font(s.get_range("F4:F7"))
s.get_range("A10:B10").values = [["Derived measure", "Value"]]
header(s.get_range("A10:B10"))
s.get_range("A11:B13").values = [
    ["Base weighted transport + downstream cost", weighted_transfer_cost(x)],
    ["QAS RSQ episodes/day (Apr-Jun 2026)", 92],
    ["QAS hospital transfers/day", 72],
]
s.get_range("B11").format.number_format = fmt_money
s.merge_cells("A15:G17")
s.get_range("A15").values = [
    [
        (
            "Current public QAS reporting records 8,398 referrals and more than 6,573 transported episodes in"
            " Apr\u2013Jun"
            " 2026, but does not provide a neonatal road/rotary/fixed-wing breakdown. The model therefore uses a"
            " Queensland neonatal retrieval study as a prior and explicitly tests alternative mixes."
        )
    ]
]
s.get_range("A15:G17").format.wrap_text = True
for c, w in zip("ABCDEFG", [18, 14, 16, 16, 18, 40, 48], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w

# IHACPA
s = wb.worksheets.add("IHACPA benchmarks")
title(s, "IHACPA NEP26 | SELECTED NEONATAL BENCHMARKS", "F")
s.get_range("A3:F3").values = [
    ["AR-DRG V12.0", "Descriptor (abbreviated)", "Inlier NWAU", "NEP benchmark", "Use", "Caveat"]
]
header(s.get_range("A3:F3"))
drg = [
    [
        "P60B",
        "Neonate transferred/died <5 days, minor complexity",
        0.8224,
        0,
        "Transferred episode comparator",
        "Not a marginal retrieval cost",
    ],
    [
        "P68D",
        "Term neonate >=2500g, minor complexity",
        0.6454,
        0,
        "Local-care comparator",
        "Actual coding/LOS required",
    ],
    [
        "P68B",
        "Term neonate >=2500g, major complexity",
        1.4581,
        0,
        "Case-mix scenario",
        "Do not infer clinical severity from consultation",
    ],
    ["P68A", "Term neonate >=2500g, extreme complexity", 3.1083, 0, "High-cost scenario", "Inlier only"],
    [
        "P06B",
        ">=2500g, major intervention or ventilation >=96h, minor complexity",
        7.1826,
        0,
        "Severe pathway stress test",
        "Requires actual code and adjustments",
    ],
]
s.get_range("A4:F8").values = drg
for row in range(4, 9):
    s.get_range(f"D{row}").formulas = [[f"=C{row}*Inputs!B22"]]
formula_font(s.get_range("D4:D8"))
s.get_range("C4:C8").format.number_format = "0.0000"
s.get_range("D4:D8").format.number_format = fmt_money
s.merge_cells("A11:F13")
s.get_range("A11").values = [
    [
        (
            "Use routine patient-level DRG/NWAU where available. The workbook treats NEP as a standardised resource"
            " benchmark. It does not equate activity funding with cash saved, and it avoids double-counting sending and"
            " receiving hospital episodes. Atherton, Mareeba and Innisfail funding arrangements should be confirmed"
            " because rural facilities may include block-funded components under the NEC."
        )
    ]
]
s.get_range("A11:F13").format.wrap_text = True
for c, w in zip("ABCDEF", [14, 48, 14, 18, 26, 42], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w

# Equipment
s = wb.worksheets.add("Equipment options")
title(s, "EQUIPMENT OPTIONS | REPLACEMENT OF AD HOC SETUP", "H")
s.get_range("A3:H3").values = [
    [
        "Option",
        "Indicative installed cost/site",
        "PTZ",
        "Tablet control",
        "Wireless",
        "QH Portal/far-end control",
        "Status",
        "Interpretation",
    ]
]
header(s.get_range("A3:H3"))
equip = [
    [
        "Current Panda Vision",
        10000,
        "4K PTZ",
        "Built-in touchscreen",
        "QH network/Wi-Fi",
        "Documented compliant",
        "Current; invoice verify",
        "Purpose-built mount on Resuscitaire",
    ],
    [
        "Tablet + OBSBOT Tiny 2 Lite",
        4500,
        "2-axis digital PTZ",
        "Host-dependent",
        "USB-C wired",
        "Not verified",
        "Concept only",
        "Lowest hardware cost; docking, power, software and far-end control require validation",
    ],
    [
        "Tablet + OBSBOT Tail Air",
        7500,
        "Motorised PTZ",
        "Obsbot Start app on tablet",
        "Wi-Fi/NDI; PoE/USB-C available",
        "Not verified",
        "Closest current architecture",
        "Can be controlled from tablet and used as webcam; no evidence of QH clinical integration",
    ],
    [
        "Commercial telehealth cart",
        45000,
        "Vendor PTZ",
        "Integrated console",
        "Usually networked",
        "Product-dependent",
        "Comparator",
        "Bulky and more costly; not purpose-designed for neonatal resuscitation",
    ],
]
s.get_range("A4:H7").values = equip
s.get_range("B4:B7").format.number_format = fmt_money
s.merge_cells("A10:H12")
s.get_range("A10").values = [
    [
        (
            "Search conclusion: no off-the-shelf medically integrated tablet-mounted PTZ package was verified that"
            " exactly"
            " replaces Panda Vision. OBSBOT Tail Air is a plausible component because it supports tablet control, 4K"
            " PTZ,"
            " Wi-Fi/NDI, USB-C and PoE, but it is a consumer/prosumer camera. A replacement configuration should be"
            " prototyped and assessed by Biomedical Technology Services, eHealth Telehealth, cyber/privacy and clinical"
            " users before procurement."
        )
    ]
]
s.get_range("A10:H12").format.wrap_text = True
s.get_range("A14:B16").values = [
    ["Source", "URL"],
    ["OBSBOT Tail Air", "https://www.obsbot.com/obsbot-tail-air-streaming-camera"],
    ["Current local configuration", "CHHHS ELC 21 October 2026, item 2.1.7"],
]
header(s.get_range("A14:B14"))
source_font(s.get_range("B15:B16"))
for c, w in zip("ABCDEFGH", [28, 18, 13, 16, 16, 24, 18, 48], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w
s.get_range("A3:H12").format.wrap_text = True

# Clinical extension
s = wb.worksheets.add("Clinical outcome extension")
title(s, "EXPLORATORY CLINICAL OUTCOME EXTENSION", "H")
s.get_range("A3:H3").values = [
    [
        "Incremental survival probability/call",
        "Extra survivors/year",
        "Major morbidity share",
        "Survivors with major morbidity",
        "Incremental QALYs",
        "Lifetime costs",
        "NMB @ $50k/QALY",
        "Interpretation",
    ]
]
header(s.get_range("A3:H3"))
clin = []
for p in [0, 0.001, 0.005, 0.01]:
    r = clinical_extension(prog["consultations"], p)
    clin.append([
        p,
        r["extra_survivors"],
        0.35,
        r["extra_survivors_major_morbidity"],
        r["incremental_qalys"],
        r["incremental_lifetime_costs"],
        r["net_monetary_benefit"],
        "Exploratory structural scenario; not an effectiveness estimate",
    ])
s.get_range("A4:H7").values = clin
s.get_range("A4:A7").format.number_format = fmt_pct
s.get_range("B4:B7").format.number_format = "0.000"
s.get_range("C4:C7").format.number_format = fmt_pct
s.get_range("D4:E7").format.number_format = "0.000"
s.get_range("F4:G7").format.number_format = fmt_money
s.merge_cells("A10:H13")
s.get_range("A10").values = [
    [
        (
            "Why this is included: better resuscitation may prevent death or major injury, but additional survival can"
            " increase downstream expenditure, especially when major morbidity occurs. The primary evaluation therefore"
            " reports cost-consequences without assuming a mortality effect. This extension should remain disabled for"
            " decision-making until credible effect and long-term cost/QALY inputs are identified."
        )
    ]
]
s.get_range("A10:H13").format.wrap_text = True
for c, w in zip("ABCDEFGH", [20, 16, 18, 18, 16, 18, 18, 44], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w

# Evidence
s = wb.worksheets.add("Evidence register")
title(s, "EVIDENCE REGISTER AND ASSUMPTION CLASSIFICATION", "E")
s.get_range("A3:E3").values = [["ID", "Source", "Use", "Status", "Decision limit"]]
header(s.get_range("A3:E3"))
ev = [
    [
        "L1",
        "CHHHS ELC Operational, 21 Oct 2026, item 2.1.7",
        "Configuration, sites, pathway, $10k benchmark",
        "Local documented",
        "No quantified outcome effect",
    ],
    [
        "L2",
        "Nicholas Cairns meeting, 27 Oct 2026",
        "4\u20135 Atherton episodes; 10\u201315/site-year",
        "Local estimate",
        "Retrospective case review required",
    ],
    [
        "E1",
        "https://pubmed.ncbi.nlm.nih.gov/23148301/",
        "Queensland avoided-transfer evidence and 5% break-even precedent",
        "External empirical",
        "2012 technology and costs",
    ],
    [
        "E2",
        "https://pubmed.ncbi.nlm.nih.gov/35074308/",
        "Decision model and PSA structure",
        "External model",
        "US financing/transport",
    ],
    [
        "E3",
        "https://pubmed.ncbi.nlm.nih.gov/35235430/",
        "Decision-tree cost components and thresholds",
        "External model",
        "US programme",
    ],
    [
        "E4",
        "https://pubmed.ncbi.nlm.nih.gov/32081766/",
        "Transfer effect: 64% vs 82%, adjusted OR 0.48",
        "External observational",
        "Confounding and different sites",
    ],
    [
        "E5",
        "https://pubmed.ncbi.nlm.nih.gov/33691080/",
        "Stabilisation evidence",
        "External observational",
        "No significant time difference",
    ],
    [
        "E6",
        "https://pubmed.ncbi.nlm.nih.gov/32949204/",
        "Queensland neonatal transport-mode prior",
        "External/local-system study",
        "Outbound legs; not FNQ cohort",
    ],
    [
        "Q1",
        "https://www.ambulance.qld.gov.au/about/performance-data",
        "Current RSQ volumes",
        "Official",
        "No mode split",
    ],
    [
        "Q2",
        (
            "https://www.health.qld.gov.au/system-governance/policies-standards/health-service-directives/retrieval"
            "-services"
        ),
        "Coordination and HHS aeromedical payment responsibility",
        "Official",
        "Contract prices not public",
    ],
    [
        "I1",
        "https://www.ihacpa.gov.au/resources/national-efficient-price-determination-2026-27",
        "NEP $7,418 and AR-DRG v12",
        "Official",
        "Benchmark, not cash saving",
    ],
    [
        "I2",
        "https://www.ihacpa.gov.au/resources/national-efficient-cost-determination-2026-27",
        "Rural block-funding context",
        "Official",
        "Facility funding regime to confirm",
    ],
    [
        "G1",
        "https://github.com/edithatogo/microcosting_healthworkforce",
        "Rate conversion/indexation/DSA patterns",
        "Reusable methods",
        "No rates imported",
    ],
    [
        "G2",
        "https://github.com/edithatogo/reimbursement-atlas",
        "IHACPA provenance/source registry",
        "Reusable provenance",
        "No turnkey NWAU engine found",
    ],
    [
        "G3",
        "https://github.com/edithatogo/voiage",
        "Future EVPI/EVPPI/EVSI",
        "Optional later",
        "Not required for base model",
    ],
]
s.get_range(f"A4:E{3 + len(ev)}").values = ev
source_font(s.get_range(f"B4:B{3 + len(ev)}"))
for c, w in zip("ABCDE", [10, 62, 38, 24, 44], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w
s.get_range(f"A3:E{3 + len(ev)}").format.wrap_text = True

# Standards
s = wb.worksheets.add("Methods and standards")
title(s, "METHODS, REPORTING AND DATA REQUEST", "F")
s.get_range("A3:F3").values = [
    ["Component", "Method", "Primary output", "Standard", "Current status", "Next data item"]
]
header(s.get_range("A3:F3"))
methods = [
    [
        "Primary economic analysis",
        "Annual cohort decision tree",
        "Costs, avoided transfers, cost-consequences",
        "CHEERS 2022",
        "Implemented",
        "Episode-level transfer decision and actual mode",
    ],
    [
        "Budget impact",
        "Cash flow plus economic annualisation",
        "1-, 3- and 5-year organisational impact",
        "ISPOR budget impact principles",
        "Implemented",
        "Invoices, support and staff time",
    ],
    [
        "Uncertainty",
        "Deterministic scenarios + PSA",
        "Probability cost-saving and 95% interval",
        "Good modelling practice",
        "Implemented",
        "Local priors and correlations",
    ],
    [
        "Hospital resource use",
        "Actual DRG/NWAU plus NEP/NEC context",
        "Standardised benchmark and local cost differential",
        "IHACPA NEP26/AHPCS v4.2",
        "Framework ready",
        "DRG/NWAU extract for consulted neonates",
    ],
    [
        "Clinical extension",
        "Death / survival with and without major morbidity",
        "QALYs, lifetime costs, NMB",
        "Exploratory only",
        "Disabled for base decision",
        "Credible effect and long-term outcome inputs",
    ],
    [
        "Prospective validation",
        "Later registry if decision uncertainty remains",
        "Calibration and impact evaluation",
        "QA/research pathway to determine",
        "Not required for initial model",
        "Consistent episode form",
    ],
]
s.get_range("A4:F9").values = methods
for c, w in zip("ABCDEF", [24, 32, 30, 28, 22, 44], strict=False):
    s.get_range(f"{c}:{c}").format.column_width = w
s.get_range("A3:F9").format.wrap_text = True

# Global styling and gridlines
for i in range(10):
    sh = wb.worksheets.get_item_at(i)
    sh.get_range("A1:Z100").format.font = {"name": "Arial", "size": 10}
    sh.get_range("A1:Z100").format.vertical_alignment = "top"

Path("outputs").mkdir(exist_ok=True, parents=True)
SpreadsheetFile.export_xlsx(wb).save(OUT)
print(OUT)  # ruff: ignore[print] -- build script reports the workbook path to stdout
print(  # ruff: ignore[print] -- build script reports formula diagnostics to stdout
    wb.inspect({
        "kind": "match",
        "search_term": "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
        "options": {"use_regex": True, "max_results": 100},
        "summary": "formula errors",
    }).ndjson
)
print(  # ruff: ignore[print] -- build script reports the decision-summary table to stdout
    wb.inspect({
        "kind": "table",
        "range": "Decision summary!A1:H16",
        "include": "values,formulas",
        "table_max_rows": 20,
        "table_max_cols": 10,
    }).ndjson
)
wb.render({"sheet_name": "Decision summary", "range": "A1:H16", "scale": 1.3}).save("outputs/workbook_preview.png")
