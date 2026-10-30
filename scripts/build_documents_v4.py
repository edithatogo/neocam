# ruff: ignore[implicit-namespace-package] -- standalone build script; scripts/ ships no package __init__
"""Build the CHHHS two-page plan and evidence/analysis supplement from release outputs."""

import csv
import json
import re
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/v4"
FIG = OUT / "figures"
r = json.loads((OUT / "results_v2.json").read_text())
pytest_log = (ROOT / "verification/v4/full/pytest.txt").read_text()
test_count = int(re.search(r"(\d+) passed", pytest_log).group(1))


def read(path: Path) -> list[dict[str, str]]:
    """Load a CSV file from the repository.

    Returns:
        The parsed CSV records.
    """
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def money(x: float) -> str:
    """Format an amount as whole AUD with an explicit sign.

    Returns:
        The formatted currency string.
    """
    return ("$" if x >= 0 else "\u2212$") + f"{abs(x):,.0f}"


# Authentic corporate memo shell retained, no invented endorsement.
doc = Document(ROOT / "assets/Briefing_note.docx")
doc.paragraphs[0].text = "28 October 2026 | Evaluation plan v4 | Discussion draft \u2014 no expenditure approval"
doc.paragraphs[1].text = "Panda Vision: evaluating investment in neonatal video support"
doc.tables[0].cell(1, 0).text = (
    "Proceed with an existing-evidence, model-based evaluation of the Atherton-led pilot and conditional Queensland"
    " expansion. "
    "Use the completed analyses to identify when investment is worthwhile; do not present modelled resource savings as"
    " observed cash savings. "
    "No prospective cohort, randomised trial or structured expert elicitation is a prerequisite."
)
doc.tables[1].cell(0, 1).text = "Prepared for Dr Dylan Mordaunt, Chief Medical Officer"
doc.tables[1].cell(1, 1).text = "CMO / neonatal, retrieval, virtual-care and finance partners"
doc.tables[2].cell(1, 0).text = (
    "1. Decision and comparator. Compare video-supported with telephone-supported specialist consultation:"
    " consultation occurs in both arms. "
    "The established RSQ/ANTS-NQ escalation pathway is retained. Assess continuation, equipment replacement and"
    " rollout from organisational, "
    "whole-health-system and societal perspectives. The pilot comprises Atherton, Mareeba and Innisfail; forecast"
    " activity is 10\u201315 consultations "
    "per site annually. The 4\u20135 Atherton episodes describe feasibility, not a causal effect or incidence rate."
    " [ELC2026; USER2026]\n\n"
    "2. Existing evidence and assumptions. Use the ELC material, published comparative studies and economic models,"
    " public birth/network data, "
    "retrieval-cost reports and available routine information. Keep the $10,000 installation estimate marked for"
    " invoice/component verification. "
    "The 2022 denominators are Atherton 157, Mareeba 134 and Innisfail 195 births. A historical 65-site public roster"
    " supports a primary "
    "33-site expansion scenario; it is not a verified 2026 service census. Assumed casemix, geography and uptake"
    " remain uncertain. [QH2022; ANZNN2023]\n\n"
    "3. Analytical design. Retain the small severity-stratified annual-cohort model. Include failed connections, local"
    " care, transfer and later rescue; "
    "critical cases receive no transfer-avoidance credit. Shared clinical-effect uncertainty remains correlated across"
    " sites. Separate resource costs, "
    "NWAU \u00d7 NEP, QWAU \u00d7 QEP and actual budgets. NEP26 is $7,418; unverified QEP/local adjustments remain"
    " blank. The indexed aeromedical "
    "anchor is not a neonatal tariff or guaranteed cash release. [NEP26; QHFUND26; AIR2019; M1]\n\n"
    "4. Analyses completed. Reproduced 58 primary deterministic scenarios and eight 20,000-draw probabilistic"
    " analyses; five-year budget tables; "
    "65 site projections; nine hypothetical funding comparisons; and 108 exploratory survival/morbidity combinations."
    " Added six equipment-life "
    "checks, 18 break-even thresholds and Monte Carlo precision/repeated-seed checks using existing parameters. Plots,"
    " complete CSV tables "
    "and the results workbook accompany this plan. No clinical parameter has been added. [M1]\n\n"
    "5. Current decision signal. The pilot reference PSA has 46.0% probability of resource cost saving, mean"
    " +$2,428/year and 95% interval "
    "\u2212$41,148 to +$65,642. The illustrative state network gives 50.7%, mean +$135,429 and interval \u2212$1.012m"
    " to +$1.809m. A three-year "
    "equipment life reduces deterministic pilot net saving to about $80/year. These results show uncertainty, not"
    " futility or proof of savings. "
    "Unproven mortality gains are not credited in the primary analysis. [M1]\n\n"
    "6. Remaining work and release decision. Replace assumptions only where invoices, published updates or ordinary"
    " records are available; "
    "otherwise retain explicit ranges and structural alternatives. Prioritise clinical-effect transportability,"
    " avoidable retrieval resources and equipment "
    "life. Complete the connected, locked-environment assurance gates, resolve actual diagnostics and obtain"
    " clinical/economic review before "
    "publication or investment recommendations. Further prospective evaluation is optional and should address"
    " decision-changing uncertainty. [M1]"
)
for row, text in [
    (
        1,
        (
            "Family travel, unpaid time and separation are consequences; no consumer-derived utilities or clinical"
            " benefits are claimed."
        ),
    ),
    (2, "Use available clinical and operational feedback; no requirement for a formal expert-estimation exercise."),
    (
        3,
        (
            "Existing public evidence informs the analysis. No external stakeholder endorsement or service-change"
            " approval"
            " is implied."
        ),
    ),
]:
    doc.tables[3].cell(row, 1).text = text
vals = [
    (
        "No expenditure approval sought. Separate sunk pilot capital from replacement and rollout. Pilot continuation"
        " cash"
        " cost is estimated at $7,123/year; full annualised economic cost is $14,052."
    ),
    (
        "No new establishment approved. Shared specialist support, readiness and training remain explicitly costed"
        " assumptions."
    ),
    (
        "Observational effect evidence, historical births and inferred transport mix limit transferability. Null/harm"
        " scenarios and shared uncertainty remain explicit."
    ),
    (
        "Aggregate existing-evidence modelling only. Obtain appropriate governance/data permissions before"
        " individual-record linkage or release of restricted material."
    ),
    (
        "Tablet/PTZ replacement is a concept, not an approved configuration. Retain biomedical, cleaning, QH Portal"
        " far-end control, privacy and cyber checks."
    ),
    (
        "Access and family displacement are assessed separately. Include survival with major morbidity and its costs;"
        " do"
        " not use cost saving as the sole criterion."
    ),
]
for i, t in enumerate(vals, 1):
    doc.tables[4].cell(i, 1).text = t
doc.tables[5].cell(1, 0).text = (
    "Our care: timely specialist support. Our people: rural readiness. First Peoples health: equitable access."
    " Our sustainability: transparent costs, uncertainty and proportionate engineering."
)
doc.tables[6].cell(1, 0).text = (
    "1. Analysis supplement v4, results workbook, plots and full tables. 2. CHHHS presentation v4. "
    "3. Repository/Git bundle, Conductor tracks and reusable lean-CI skill. 4. Actual verification receipt and"
    " outstanding-gate register. "
    "Source identifiers refer to the supplement/register; M1 denotes reproducible model outputs, not an external study."
)
for t in list(doc.tables)[7:]:
    t._element.getparent().remove(t._element)  # ruff: ignore[private-member-access] -- python-docx exposes no public OOXML node handle
for node in doc._element.xpath(".//w:t"):  # ruff: ignore[private-member-access] -- lxml element access is the only template-editing route
    if node.text and "<select document type>" in node.text:
        node.text = "MEMORANDUM"
    elif node.text and "Choose an item" in node.text:
        node.text = ""
for p in list(doc.paragraphs):
    if p.text.strip() in {"/", "☐ / ☐"}:
        p.text = ""
    if not p.text.strip() and p._p.xpath(".//w:sdt"):  # ruff: ignore[private-member-access] -- python-docx exposes no public element handle
        p._p.getparent().remove(p._p)  # ruff: ignore[private-member-access] -- python-docx exposes no public element handle
    for run in p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(9)
for table in doc.tables:
    for row in table.rows:
        row.height = None
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(3)
                p.paragraph_format.line_spacing = 1.0
                for run in p.runs:
                    run.font.name = "Arial"
                    run.font.size = Pt(9)
    for cell in table.rows[0].cells:
        for p in cell.paragraphs:
            p.paragraph_format.keep_with_next = True
for run in doc.paragraphs[1].runs:
    run.font.size = Pt(16)
    run.bold = True
doc.tables[3].cell(0, 0).paragraphs[0].paragraph_format.page_break_before = True
doc.save(OUT / "Panda_Vision_two_page_plan_v4.docx")

# Companion analysis report, with explicit pages to keep charts next to interpretations.
s = Document()
sec = s.sections[0]
sec.page_height = Inches(11.7)
sec.page_width = Inches(8.3)
sec.top_margin = sec.bottom_margin = Inches(0.6)
sec.left_margin = sec.right_margin = Inches(0.7)
s.styles["Normal"].font.name = "Arial"
s.styles["Normal"].font.size = Pt(10)
s.styles["Normal"].paragraph_format.space_after = Pt(6)
for name in ("Heading 1", "Heading 2"):
    s.styles[name].font.name = "Arial"
    s.styles[name].font.color.rgb = RGBColor.from_string("15535C")
sec.header.paragraphs[0].text = "PANDA VISION | Analysis and evidence supplement v4 | 28 October 2026"
footer = sec.footer.paragraphs[0]
footer.text = "Preliminary model \u2014 assumptions remain explicit | Page "
fld = OxmlElement("w:fldSimple")
fld.set(qn("w:instr"), "PAGE")
footer._p.append(fld)  # ruff: ignore[private-member-access] -- python-docx exposes no public element handle


def title(t: str, *, new: bool = True) -> None:
    """Start a numbered supplement section, optionally on a new page."""
    if new:
        s.add_page_break()
    s.add_heading(t, 1)


def para(t: str) -> None:
    """Add a body paragraph to the supplement."""
    s.add_paragraph(t)


def image(name: str, width: float = 6.7) -> None:
    """Insert a PNG figure from the v4 output directory."""
    s.add_picture(str(FIG / f"{name}.png"), width=Inches(width))


def table(headers: list[object], rows: list[list[object]]) -> object:
    """Add a styled table whose header and body cells are stringified.

    Returns:
        The new table.
    """
    t = s.add_table(rows=1, cols=len(headers))
    t.style = "Light Shading Accent 1"
    for cell, v in zip(t.rows[0].cells, headers, strict=False):
        cell.text = str(v)
    for row in rows:
        for cell, v in zip(t.add_row().cells, row, strict=False):
            cell.text = str(v)
    for row in t.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(3)
                for run in p.runs:
                    run.font.size = Pt(9)
    return t


title("1. What the completed model can support", new=False)
para(
    "The decision is whether to continue, replace or extend video support in neonatal specialist consultations that"
    " would occur anyway by telephone. This is an existing-evidence evaluation, not a prospective study proposal. V4"
    " preserves all 27 economic parameters and the default model outputs; it strengthens workflow, diagnostic analyses"
    " and deliverable consistency."
)
table(
    ["Annual result", "Pilot: 3 sites", "Illustrative network: 33 sites"],
    [
        [label, *[formatter(r[section][key][field]) for key in keys]]
        for label, section, keys, field, formatter in [
            ("Consultations", "deterministic", ["pilot", "spokes"], "consultations", lambda x: f"{x:,.1f}"),
            ("Economic programme cost", "deterministic", ["pilot", "spokes"], "programme_cost", money),
            ("Deterministic net resource saving", "deterministic", ["pilot", "spokes"], "net_saving", money),
            ("PSA mean", "psa", ["pilot_attenuated", "spokes_attenuated"], "mean", money),
            ("PSA median", "psa", ["pilot_attenuated", "spokes_attenuated"], "median", money),
            ("PSA 2.5th percentile", "psa", ["pilot_attenuated", "spokes_attenuated"], "lower", money),
            ("PSA 97.5th percentile", "psa", ["pilot_attenuated", "spokes_attenuated"], "upper", money),
            (
                "Probability resource cost saving",
                "psa",
                ["pilot_attenuated", "spokes_attenuated"],
                "probability_cost_saving",
                lambda x: f"{100 * x:.2f}%",
            ),
        ]
    ],
)
para(
    "Results are conditional on analyst priors, not measured CHHHS savings or posterior estimates. Resource cost"
    " saving is not cash released. Absence of financial saving does not imply absence of clinical value. The primary"
    " analysis credits no proven mortality benefit. [M1]"
)
table(
    ["Analysis actually run", "Extent"],
    [
        ["Deterministic scenarios", "58 primary comparisons; five portfolios; separate Weipa reopening"],
        ["Probabilistic analysis", "8 structures \u00d7 20,000 draws; separate annual realisation uncertainty"],
        ["Precision / robustness", "Nested prefixes and 6 independent-seed runs \u00d7 20,000 draws"],
        ["Further checks", "6 equipment-life cases; 18 two-way break-even thresholds"],
        ["Clinical consequences", "108 exploratory survival/morbidity/value combinations"],
        ["Funding / budget", "9 hypothetical QWAU/QEP comparisons; 2 five-year cash budgets"],
        ["Population / artifacts", "65 historical site projections; 14 individual charts; full CSV tables"],
    ],
)

title("2. Population, scope and traceable inputs")
para(
    "The 21 October ELC paper describes implementation at Atherton, Mareeba and Innisfail. Local clarification"
    " establishes 4\u20135 episodes at Atherton and a forecast 10\u201315 video consultations per site annually. The"
    " period and eligible population for the observed episodes are not known, so no local incidence/effect is"
    " inferred. Installation cost $10,000 is local information requiring invoice/component verification. [ELC2026;"
    " USER2026]"
)
table(
    ["Site", "2022 babies", "Forecast consultations", "Implied calls / birth"],
    [
        ["Atherton", "157", "10\u201315", "6.4\u20139.6%"],
        ["Mareeba", "134", "10\u201315", "7.5\u201311.2%"],
        ["Innisfail", "195", "10\u201315", "5.1\u20137.7%"],
        ["Total", "486", "30\u201345", "6.2\u20139.3%"],
    ],
)
para(
    "The official perinatal table contains 72 public rows; co-located birth centres are combined into 65 sites without"
    " changing the 46,711-birth total. The 33-site primary spoke scenario contains 28,276 births. Its threshold of at"
    " least 20 births is an analytical rule, not a capability standard. Private births are aggregate only. This is not"
    " a complete contemporary 2026 operating-site roster. [QH2022]"
)
para(
    "ANZNN describes a selected high-risk population and participating units; it is not an all-birth or"
    " outborn-consultation denominator. Group/geography assignments are labelled proxies. Reopened services are"
    " separate hybrid-year scenarios. Newer registration data were located but not imported; registration and"
    " perinatal definitions are not interchangeable. [ANZNN2023; BDM2025]"
)
para(
    "The parameter register records sources, ranges and analyst assumptions. Current schema, arithmetic, reference and"
    " protected-file checks pass; they cannot establish the empirical truth of uncertain cost/effect inputs. Full"
    " study extraction and contemporary operational validation remain incomplete. No additional structured elicitation"
    " is imposed."
)

title("3. Evidence mapped to model roles")
table(
    ["Study", "Evidence used", "Interpretation"],
    [
        [
            "Armfield 2012; PMID23148301",
            "5/19 avoided transports; 4 helicopters; historical net saving AUD54,400",
            "Queensland economic precedent, not a current local causal rate.",
        ],
        [
            "Haynes 2020; PMID32081766",
            "317 newborns; adjusted transfer OR0.48 (0.26\u20130.90)",
            "Observational effect, attenuated for transportability.",
        ],
        [
            "Haynes 2021; PMID33691080",
            "Stabilisation \u22121.8min (\u221216.0 to12.4)",
            "No proven stabilisation-time saving monetised.",
        ],
        [
            "Yoo 2022; PMID35074308",
            "Decision model, 1,000 simulations; ROI2.23",
            "Economic/state-scale precedent; US2017 prices not transplanted.",
        ],
        [
            "Thao 2022; PMID35235430",
            "Decision tree, transport and hospital costs",
            "Structural precedent; not independent effect replication.",
        ],
        [
            "Lietz 2026; PMID42647428",
            "Simulation93participants; no difference between phone/video/AR",
            "Supports null incremental-video possibility; not clinical equivalence proof.",
        ],
        [
            "Sandhu 2026; PMID42313572",
            "20participants; improved procedural confidence",
            "Implementation/training, not survival-effect estimation.",
        ],
    ],
)
para(
    "The search is targeted and largely abstract-verified, not a completed systematic full-text review. Economic"
    " studies sharing clinical evidence are not counted as independent effect replications. Original prices and dollar"
    " findings remain in their stated historical contexts unless source year/resource quantities permit a defensible"
    " update. [ARM2012; HAY2020; HAY2021; YOO2022; THAO2022; LIETZ2026; SANDHU2026]"
)
para(
    "The reference prior uses half the Haynes log-OR (central OR≈0.693) with added transportability uncertainty. This"
    " attenuation is an analyst judgement. Published-effect, sceptical and no-effect structures are separately"
    " evaluated. No procedural-confidence-to-mortality conversion is made."
)

title("4. Pilot and statewide probabilistic distributions")
image("pilot_psa")
image("spokes_psa")
para(
    "The same uncertain clinical-effect draw is shared across sites. Increasing scale improves representation of"
    " activity and casemix but does not average away a systematic error in effectiveness. Annual event-count"
    " variability is calculated separately from parameter uncertainty. [M1]"
)

title("5. Structural scenarios and the financial conclusion")
image("pilot_scenarios")
image("effect_structures")
para(
    "Null effects, greater transfer rates, later rescue, critical-heavy casemix, additional local care and different"
    " avoidable-cost fractions remain represented. A new transfer may be clinically appropriate, not a harm. The full"
    " 58-row CSV includes state results and other variations. [M1]"
)

title("6. Simulation precision is not clinical certainty")
image("pilot_mc_precision")
rr = read(OUT / "independent_seed_checks.csv")
table(
    ["Portfolio", "Seed", "Draws", "Cost-saving probability"],
    [[x["portfolio"], x["seed"], x["draws"], f"{100 * float(x['p_saving']):.3f}%"] for x in rr],
)
para(
    "Pilot repeats span 45.93\u201345.985%; state repeats 50.625\u201351.10%. The reference probability Monte Carlo SE"
    " is about 0.35 percentage points at 20,000 draws. These checks indicate adequate simulation precision for the"
    " present decision uncertainty; they do not validate assumed priors or clinical effectiveness. Nested prefixes"
    " overlap and are not independent studies. [M1]"
)

title("7. Retrieval costing and funding must stay separate")
para(
    "A Queensland aeromedical resource anchor of $18,670 is reported in a Torres Strait skin/soft-tissue infection"
    " study of 2018\u201319 care. It is all-age, non-neonatal, mixed-air and not an RSQ marginal tariff. Assuming a"
    " 2019 price year, the CPI bridge gives $23,824.91 at June 2026: 18,670 \u00d7102.03 / [115.125"
    " \u00d7(99.73/143.6)]. The source-price year is uncertain; 2018 and additional30% air-cost pressure are tested."
    " [AIR2019; CPIBASE; CPI2026]"
)
para(
    "Rotary1.2\u00d7 / fixed-wing0.9\u00d7 multipliers, geographic mode mix and50% avoidable fraction are assumptions."
    " Road$4,000 is a bottom-up illustration: staff$3,000, distance$360, coordination$400 and equipment$240. NeoSTRESS"
    " was 45 outbound, non-patient sound-measurement legs, not a representative neonatal transport census."
    " [NEOSTRESS2020]"
)
image("funding_grid", 6.2)
para(
    "Maintain four ledgers: resource cost; NWAU\u00d7NEP; QWAU\u00d7QEP; actual organisational budget. The numerical"
    " QEP/local weights remain missing. Your mchs 2026 parity is not validated; use a verified official/GEN_WAU export"
    " for episode valuation. Do not add funding benchmarks together. [NEP26; QHFUND26; MCHS]"
)

title("8. Equipment life and conditional break-even")
image("equipment_life")
image("break_even")
para(
    "The three-year equipment-life case leaves only about $80/year deterministic pilot saving, compared with $4,167"
    " over five years and $5,912 over seven. The 18 break-even thresholds vary utilisation and avoidable resource"
    " fraction using existing parameters. They are conditions under the model, not observed treatment effects or"
    " procurement thresholds. [M1]"
)

title("9. Budget impact and societal interpretation")
image("pilot_budget")
image("spokes_budget")
para(
    "Year-one capital and later cash costs are separate from annualised resource values. Family travel/time offsets"
    " are estimated; they do not equal cash savings to CHHHS. The workbook retains separate health-system and societal"
    " deterministic columns. Actual organisational funding consequences cannot be inferred without verified contracts,"
    " allocations and activity adjustments. [M1]"
)

title("10. Survival with morbidity and remaining structural limits")
image("survival_frontier")
para(
    "The108-point frontier includes survivors with major morbidity and higher future costs. Absolute survival"
    " gain0/0.1/0.5/1%, major-morbidity share10/35/70%, discount0/3/5% and illustrative value$0/$50k/$100k per QALY"
    " are varied. Forty-year survival, utilities0.9/0.5 and annual costs$1k/$20k are assumptions. No survival benefit"
    " or calibrated lifetime ICER is claimed. These utility inputs do not define the worth of disabled people. [M1]"
)
para(
    "Not implemented as empirically supported models: antenatal maternal transfer, repeated consultations per infant,"
    " origin\u2013destination flight/crew routes, shared network outages, specialist response delays, differential"
    " effects by condition, age-varying survival/morbidity and caregiver/equity spillovers. These remain explicit"
    " limitations, not hidden additional features. They can be explored later where decision value warrants it;"
    " current work does not depend on obtaining a formal elicitation."
)
para(
    "Decision use: assess benefit requirements, equipment/implementation choices and robustness across priors, rather"
    " than report only a probability of financial saving. Cost-only EVPI in the model is not an automatically"
    " justified research budget and does not capture unquantified health benefits."
)

title("11. Lean engineering and reusable safeguards")
image("verification_work")
para(
    "The full harness executes the ordinary suite once under coverage, then reuses its output for coverage checks."
    " Local prek hooks are thin; optional testmon/mutation caches invalidate on static inputs,"
    " dependency/interpreter/configuration changes and source deletions. PR, full-local and hosted assurance remain"
    " different claims. One Renovate configuration replaces duplicate updater policy; no bot activation or hosted CI"
    " is claimed."
)
para(
    f"The v4 local suite currently passes {test_count} tests. The full harness records 6 passed, 22 blocked and 1 "
    f"failed gate: the missing real uv.lock is a failed consistency check. Ruff, ty, basedpyright, Hypothesis, "
    f"Gremlins, Scalene, Gitleaks, Vale, Polars, prek, actionlint and zizmor could not execute because "
    f"dependencies/binaries could not be installed in this network-restricted runtime. New tool configurations may "
    f"expose additional diagnostics on their first real run. The Conductor gitlink is pinned, not populated."
)
para(
    "The reusable maintaining-lean-ci skill is included under .agents/skills with a portable receipt checker and"
    " adversarial contract tests. Validation is executable checker tests plus author review, not independent"
    " fresh-agent pressure testing. It is repo-local/portable; no permanent installation in ChatGPT or all future"
    " projects is claimed. Artifact tooling is separate from the numerical model environment."
)

title("12. Sources and reproducibility")
para(
    "Source and parameter registries, seven-study mapping, full scenario tables, fixed-seed draws, diagnostic code,"
    " plot inputs and engineering receipts are included in the repository. Source labels below identify public"
    " references; local ELC/USER statements are explicitly local information. M1 is a model result, not published"
    " evidence."
)
for row in read(ROOT / "evidence/sources.csv"):
    pp = s.add_paragraph(
        f"[{row['source_id']}] {row['publisher']}. {row['title']}. Data/reference period: {row['data_year']}. {
            row['url']
        }"
    )
    for run in pp.runs:
        run.font.size = Pt(8)
para(
    "Reproduce: python scripts/run_v2.py --out outputs/v4 --iterations 20000; python scripts/complete_analysis_v4.py."
    " Use the reviewed locked environment for full acceptance. The delivered host versions and incomplete gates are"
    " recorded separately from target dependency pins."
)
s.save(OUT / "Panda_Vision_analysis_supplement_v4.docx")
print("Saved two-page plan and 12-section supplement")  # ruff: ignore[print] -- build script reports completion to stdout
