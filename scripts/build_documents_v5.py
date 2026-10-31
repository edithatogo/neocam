# ruff: ignore[implicit-namespace-package] -- standalone build script; scripts/ ships no package __init__
"""Create branded two-page plan and a bounded comparative analysis supplement."""

import csv
import json
from pathlib import Path

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

try:  # imported as ``scripts.document_metadata`` when the repository root is on sys.path
    from scripts.document_metadata import save_neutralised
except ModuleNotFoundError:  # run directly as ``python scripts/build_documents_v5.py``
    from document_metadata import save_neutralised

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/v5"
FIG = OUT / "figures"
r = json.loads((OUT / "results_v5.json").read_text())


def money(v: float) -> str:
    """Format an amount as whole AUD with an explicit sign.

    Returns:
        The formatted currency string.
    """
    return ("\u2212$" if v < 0 else "$") + f"{abs(v):,.0f}"


def read(name: str) -> list[dict[str, str]]:
    """Load one CSV export from the v5 output directory.

    Returns:
        The parsed CSV records.
    """
    with (OUT / name).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def brief() -> None:  # ruff: ignore[complex-structure, too-many-branches] -- one linear document-composition pass
    """Author the branded two-page plan from the supplied corporate template."""
    d = Document(ROOT / "assets/Briefing_note.docx")
    d.paragraphs[0].text = "28 October 2026 | Evaluation plan v5 | Discussion draft \u2014 no procurement approval"
    d.paragraphs[1].text = "Neonatal teleconsultation: five-option investment evaluation"
    d.tables[0].cell(1, 0).text = (
        "Use the existing-evidence model to compare telephone, mobile teleconference, Panda Vision, ceiling/wall"
        " PTZ and a complete tablet/OBSBOT kit. Distinguish new investment from continuation or replacement. Review"
        " conditional results and feasibility before procurement or publication; no new trial or structured expert"
        " elicitation is required to conduct the model-based study."
    )
    d.tables[1].cell(0, 1).text = "Prepared for Dr Dylan Mordaunt, Chief Medical Officer"
    d.tables[1].cell(1, 1).text = "CMO / neonatal, retrieval, virtual-care and finance partners"
    d.tables[2].cell(1, 0).text = (
        "1. Decision and setting. Telephone-supported consultation and the RSQ/ANTS-NQ escalation pathway are retained"
        " in all arms. The pilot includes Atherton, Mareeba and Innisfail, with 10\u201315 consultations per site"
        " annually. The 4\u20135 Atherton episodes inform workflow, not efficacy or incidence. Use public historical"
        " births for the existing 33-site Queensland scenario, not as a current capability census. [ELC2026; USER2026;"
        " QH2022]\n\n"
        "2. Complete configurations. ELC indicative installed costs are $45,000 for mobile teleconference, $10,000 for"
        " Panda Vision and $47,000 for fixed PTZ. The tablet/OBSBOT kit is a separate complete-system concept at an"
        " assumed $4,500, with $7,500 and wider alternatives tested. A $349 camera alone is not an equivalent service."
        " Verify integration, mounting, cleaning, power, far-end control and total cost. No technical approval or"
        " invoice verification is implied. [ELC2026; M5]\n\n"
        "3. Model and outcomes. Extend the existing severity-stratified cohort model, not the clinical pathways."
        " Reference video effectiveness and delivery are equal by assumption, not demonstrated equivalence. Retain"
        " telephone fallback, critical transfers, rescue and local/receiving-hospital consequences. Report resource"
        " costs, family burden and actual budgets separately from NWAU \u00d7 NEP and QWAU \u00d7 QEP. Unverified QEP"
        " remains blank. Survival with major morbidity remains an exploratory extension, not an assumed primary"
        " benefit. [M2; M5]\n\n"
        "4. Analyses now completed. Eighteen paired 20,000-draw PSA structures compare five options with shared"
        " systematic uncertainty. Twelve one-way dimensions and four two-way pairs cover pilot/state decisions. Exact"
        " 3,125-point five-way and 2,401-point equipment grids, independent 12-dimensional designs and Sobol variance"
        " analyses address interactions. Existing v4 scenarios and survival analyses are retained. Deterministic"
        " design frequencies are not probabilities. [M5]\n\n"
        "5. What the results imply. Under equal-video/new-purchase assumptions, the proposed kit has 53.9% probability"
        " of being cost-optimal; Panda has 46.0% probability of saving resources versus telephone but is never the"
        " cheapest video choice. Retaining installed Panda instead makes Panda cost-optimal in 61.4% of draws. With"
        " uncertain prototype cost/delivery, pilot probabilities become telephone 51.0%, Panda 27.2% and kit 21.8%;"
        " the state expected-value choice switches to Panda. These are conditional model results, not clinical"
        " rankings. [M5]\n\n"
        "6. Interpretation and publication. Input-only clustering was weak and unstable; do not infer patient groups."
        " A decision-focused classifier achieved 95.0% holdout agreement, but its worst annual pilot regret was"
        " $8,970; exact model evaluations remain authoritative. First journal target: Journal of Telemedicine and"
        " Telecare. Complete critical full-text source verification, independent model review, a clean reproducible"
        " release and governance/authorship/data-rights statements before submission. [M5; JTT]"
    )
    for i, t in [
        (
            1,
            "Report family costs and separation; no consumer-derived utility or disability-based exclusion is imposed.",
        ),
        (
            2,
            (
                "Use existing clinical and operational knowledge. Formal elicitation and new prospective recruitment"
                " are"
                " not prerequisites."
            ),
        ),
        (3, "No Queensland Health, RSQ, neonatal-network or vendor endorsement of this comparative model is claimed."),
    ]:
        d.tables[3].cell(i, 1).text = t
    vals = [
        (
            "Separate full procurement cash, annualised resource cost, sunk capital and cross-service attribution. An"
            " allocation fraction does not reduce the purchase bill. Prototype prices are unquoted."
        ),
        (
            "Readiness, training, specialist support and network capacity remain model assumptions. No new positions or"
            " funding allocation are approved."
        ),
        (
            "Sparse device-specific evidence; assumed common video effects; historical denominators; uncertain marginal"
            " retrieval cost and prototype reliability. Null/harm and eligibility-restricted comparisons are explicit."
        ),
        (
            "Existing aggregate-evidence model. Confirm governance, coauthor agreement and rights before any linked"
            " records, public code/data release or submission. No exemption or approval is invented."
        ),
        (
            "Panda Vision and OBSBOT are not interchangeable labels: the latter arm is a complete tablet-based"
            " alternative. Establish technical eligibility before interpreting a cost-optimal choice as procurable."
        ),
        (
            "Preserve rural access and family-displacement consequences. Cost saving alone is not the decision"
            " criterion;"
            " extra survival may appropriately increase future care expenditure."
        ),
    ]
    for i, t in enumerate(vals, 1):
        d.tables[4].cell(i, 1).text = t
    d.tables[5].cell(1, 0).text = (
        "Our care: appropriate specialist support. Our people: usable, reliable systems. First Peoples health:"
        " equitable access. Our sustainability: transparent procurement, resource costs and uncertainty."
    )
    d.tables[6].cell(1, 0).text = (
        "1. Comparative supplement and publication strategy v5. 2. Results workbook, full CSV tables and 15"
        " PNG/SVG figures. 3. CHHHS presentation v5. 4. Repository, Git history, Conductor tracks and actual assurance"
        " receipts. M2/M5 denote model outputs, not external observations; source registers identify all citations."
        " Full"
        " connected-toolchain and hosted-CI acceptance remain incomplete."
    )
    for t in list(d.tables)[7:]:
        t._element.getparent().remove(t._element)  # ruff: ignore[private-member-access] -- python-docx exposes no public OOXML node handle
    for node in d._element.xpath(".//w:t"):  # ruff: ignore[private-member-access] -- lxml element access is the only template-editing route
        if node.text and "<select document type>" in node.text:
            node.text = "MEMORANDUM"
        elif node.text and "Choose an item" in node.text:
            node.text = ""
    for p in list(d.paragraphs):
        if p.text.strip() in {"/", "☐ / ☐"}:
            p.text = ""
        if not p.text.strip() and p._p.xpath(".//w:sdt"):  # ruff: ignore[private-member-access] -- python-docx exposes no public element handle
            p._p.getparent().remove(p._p)  # ruff: ignore[private-member-access] -- python-docx exposes no public element handle
        for run in p.runs:
            run.font.name = "Arial"
            run.font.size = Pt(9)
    for table in d.tables:
        for row in table.rows:
            row.height = None
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.line_spacing = 1
                    for run in p.runs:
                        run.font.name = "Arial"
                        run.font.size = Pt(9)
        for cell in table.rows[0].cells:
            for p in cell.paragraphs:
                p.paragraph_format.keep_with_next = True
    for run in d.paragraphs[1].runs:
        run.font.size = Pt(15)
        run.bold = True
    d.tables[3].cell(0, 0).paragraphs[0].paragraph_format.page_break_before = True
    save_neutralised(d, OUT / "Panda_Vision_two_page_plan_v5.docx")


brief()
# A separate supplement keeps the decision memo at two pages.
s = Document()
sec = s.sections[0]
sec.page_height = Inches(11.7)
sec.page_width = Inches(8.3)
sec.top_margin = sec.bottom_margin = Inches(0.6)
sec.left_margin = sec.right_margin = Inches(0.7)
s.styles["Normal"].font.name = "Arial"
s.styles["Normal"].font.size = Pt(10)
s.styles["Normal"].paragraph_format.space_after = Pt(6)
for k in ["Heading 1", "Heading 2"]:
    s.styles[k].font.name = "Arial"
    s.styles[k].font.color.rgb = RGBColor.from_string("15535C")
sec.header.paragraphs[0].text = "PANDA VISION | Comparative analysis and publication strategy v5 | 28 October 2026"
f = sec.footer.paragraphs[0]
f.text = "Conditional economic model • Not procurement approval | Page "
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
f._p.append(field)  # ruff: ignore[private-member-access] -- python-docx exposes no public element handle


def heading(t: str, *, new: bool = True) -> None:
    """Start a numbered supplement section, optionally on a new page."""
    if new:
        s.add_page_break()
    s.add_heading(t, 1)


def p(t: str) -> None:
    """Add a body paragraph to the supplement."""
    s.add_paragraph(t)


def table(headers: list[object], rows: list[list[object]], _width: float | None = None) -> object:
    """Add a styled table whose header and body cells are stringified.

    Returns:
        The new table.
    """
    t = s.add_table(rows=1, cols=len(headers))
    t.style = "Light Shading Accent 1"
    for c, h in zip(t.rows[0].cells, headers, strict=False):
        c.text = h
    for row in rows:
        for c, v in zip(t.add_row().cells, row, strict=False):
            c.text = str(v)
    for row in t.rows:
        for c in row.cells:
            for para in c.paragraphs:
                para.paragraph_format.space_after = Pt(3)
                for run in para.runs:
                    run.font.size = Pt(9)
    return t


def fig(name: str, width: float = 6.7) -> None:
    """Insert a PNG figure from the v5 output directory."""
    s.add_picture(str(FIG / f"{name}.png"), width=Inches(width))


heading("1. The question is configuration and investment timing", new=False)
p(
    "Compare five complete services: telephone advice, mobile teleconference, Panda Vision, fixed ceiling/wall"
    " pan\u2013tilt\u2013zoom (PTZ), and a proposed tablet/OBSBOT kit. Consultation occurs in all arms. This extends,"
    " rather than replaces, the original pilot and Queensland model. The existing Panda deterministic and paired"
    " probabilistic results are numerically unchanged. [M5]"
)
table(
    ["Configuration", "Installed capital/site", "Evidence boundary"],
    [
        ["Telephone", "$0 incremental", "Existing telephone consultation remains; not zero healthcare cost"],
        ["Mobile teleconference", "$45,000", "ELC indicative comparator; actual purchase/share unverified"],
        ["Panda Vision", "$10,000", "ELC and user estimate; invoices/components not checked"],
        ["Ceiling/wall PTZ", "$47,000", "ELC comparator; room coverage and suitability site-dependent"],
        ["Tablet + OBSBOT kit", "$4,500 reference", "$2,500\u2013$10,000 range; $7,500 scenario; no supplier quote"],
    ],
)
p(
    "OBSBOT is a camera brand/component, not a separate clinical intervention by itself. The fifth arm includes the"
    " tablet, mount, power, integration, support and approved workflow. It is not priced at the ELC\u2019s camera-only"
    " $349. Reference video effects and usable-connection probabilities are identical as an explicit"
    " hypothesis\u2014not established equivalence. [ELC2026; M5]"
)
p(
    "Three distinct decisions are analysed: acquire new equipment; retain an installed system; and attribute shared"
    " equipment costs to neonatal activity. Existing equipment removes sunk purchase expenditure only for that arm."
    " Cross-use attribution does not reduce the full cash procurement bill. Hypothetical fixed-unit sharing may be"
    " infeasible and must be checked locally."
)
p(
    "All five arms are retained in conceptual comparisons, with separate eligibility-restricted results excluding the"
    " proposed kit. No ranking supplies biomedical, privacy, cyber, cleaning or clinical-governance approval."
)
heading("2. Exact model, inputs and evidentiary limits")
p(
    "The annual cohort has low-, moderate- and critical-acuity pathways. Critical cases receive no transfer-avoidance"
    " credit. Connection failure returns to telephone; retained patients may later need rescue. Shared effect/cost"
    " draws preserve systematic uncertainty across arms and sites. Incremental resource consequences, family costs and"
    " cash expenditure remain separate. [M2; M5]"
)
p(
    "Local activity remains 10\u201315 video consultations per site/year (37.5 across three sites at midpoint);"
    " 4\u20135 episodes occurred at Atherton. Historical 2022 births are 157, 134 and 195 at Atherton, Mareeba and"
    " Innisfail. The 65-site public roster and illustrative 33-spoke portfolio are not a verified 2026 capability"
    " census. No new patient-level dataset was collected."
)
p(
    "The primary clinical effect is an attenuated observational transfer odds ratio, with published, sceptical and"
    " null alternatives. No device-specific clinical effect is estimated from the four-to-five pilot episodes."
    " Published economic evaluations provide model precedents, not independent clinical replications. A new full-text"
    " systematic review has not been completed. [HAY2020; ARM2012; THAO2022; YOO2022; LIETZ2026]"
)
p(
    "The indexed public air-retrieval anchor is not a neonatal marginal tariff. Transport mix, avoidable fractions and"
    " net downstream costs retain their uncertainty. NEP26 = $7,418; current QEP/local QWAU adjustments remain"
    " unverified. Resource saving is not automatically cash released, reduced funding or additional health. Original"
    " source/parameter registers are retained in the repository."
)
table(
    ["Assumption group", "Deterministic range / treatment"],
    [
        [v["parameter"], v["low"] + " to " + v["high"]]
        for v in list(csv.DictReader((ROOT / "data/v5/sensitivity_ranges.csv").open()))
    ][:0]
    if False
    else [
        ["Clinical transfer OR", "0.35\u20131.30; no-effect/increased-transfer possibilities"],
        ["Activity", "5\u201325 calls/pilot site/year for sensitivity, not measured incidence"],
        ["Marginal resources / hospital delta", "10\u2013100%; hospital delta \u2212$4,000 to +$10,000"],
        ["Life / critical share", "3\u20137 years; critical 5\u201340%"],
        ["Usable video / workflow", "80\u2013100% established; 70\u2013100% prototype; $0\u2013$175/call"],
        [
            "Prototype kit / shared capital",
            "Kit $2,500\u2013$10,000; 5\u2013100% attribution, not procurement discount",
        ],
    ],
)
p(
    "The sensitivity space is a bounded researcher-defined design. It is neither an empirical distribution of"
    " Queensland hospitals nor a posterior distribution of clinical outcomes."
)
heading("3. Five-arm probabilistic comparison")
ps = r["psa"]["pilot_new"]["summary"]
table(
    ["Pilot: new equipment", "Mean saving/year", "95% uncertainty interval", "P(cost-optimal)"],
    [
        [k, money(v["mean"]), money(v["lower"]) + " to " + money(v["upper"]), f"{v['p_optimal']:.1%}"]
        for k, v in ps.items()
    ],
)
fig("02_paired_psa")
p(
    "Under equal video effects, delivery and support, the cheaper proposed kit is mechanically preferred to the more"
    " expensive video options. That finding is conditional on a complete clinically acceptable configuration costing"
    " the assumed amount. Panda\u2019s 46.0% probability of saving versus telephone is different from its zero"
    " probability of being the cheapest among these five in this particular structure. [M5]"
)
heading("4. Incumbency and prototype uncertainty reverse choices")
fig("03_decision_contexts")
p(
    "Retaining installed Panda yields mean annual resource saving $10,238 and 61.4% probability of being cost-optimal."
    " Buying a new kit instead retains its purchase cost; switching does not make the new hardware free. The same"
    " reasoning applies to an already-owned mobile or fixed system."
)
p(
    "A separate structural PSA assigns the kit uncertain installed cost (triangular $2,500/$4,500/$10,000, with common"
    " cost inflation) and uncertain delivery relative to the established system (triangular 0.65/0.95/1.0). These are"
    " explicit analyst priors. Pilot probabilities are telephone 51.0%, Panda 27.2%, kit 21.8%; kit has the slightly"
    " greater expected saving ($3,295 versus $2,428). Most likely optimal and greatest expected value are not the same"
    " statistic."
)
p(
    "In the illustrative 33-site network under that prototype uncertainty, Panda has the greatest expected resource"
    " saving ($135,429 versus $107,582 for the kit). These are not probabilities of superior clinical care."
)
p(
    "Cost-only annual EVPI is $6,179 for the pilot in the reference new-purchase structure. This is the expected loss"
    " from uncertainty under that objective and decision set, not a recommended research budget or a lifetime"
    " health-value estimate. Expected regret and all pairwise distributions are supplied."
)
heading("5. One-way sensitivity and exact decision surfaces")
fig("04_one_way", 6.7)
p(
    "Twelve dimensions are varied over 21 points for both pilot and state portfolios: 2,520 arm-level rows. The"
    " strongest single-arm drivers include clinical effect, hospital-resource difference and the avoidable retrieval"
    " fraction. Other inputs are held at reference. These endpoints are not a 95% interval."
)
p(
    "Four complete two-way pairs are evaluated at 31 \u00d7 31 points in both portfolios (7,688 design points):"
    " activity \u00d7 effect; prototype cost \u00d7 reliability; mobile capital attribution \u00d7 prototype"
    " reliability; and equipment life \u00d7 avoidable resources. Every plotted winner is obtained from the exact"
    " five-arm model."
)
heading("6. Prototype price and delivery are not interchangeable")
fig("06_surface_kit_delivery", 6.6)
p(
    "A low purchase cost is not enough if effective delivery falls. Conversely, a technically equivalent lower-cost"
    " complete kit can be preferred for new investment. These thresholds make validation questions explicit without"
    " pretending that a prototype has demonstrated equivalence."
)
fig("07_surface_shared_cart", 6.1)
p(
    "Shared-unit attribution can make a mobile configuration economically attractive. This applies only where use by"
    " other services and the attribution method are defensible; it does not reduce the total purchase payment."
)
heading("7. Joint deterministic and variance-based sensitivity")
fig("11_sobol", 6.6)
p(
    "The independent 12-dimensional design uses 8,192 training, 2,048 selection and 4,096 fresh holdout points."
    " Separate Sobol decompositions use base sizes 2,048 and 4,096: 86,016 model design evaluations across six"
    " outcomes. First-order and total-order estimates distinguish direct variation and interactions within the assumed"
    " independent uniform ranges. This is not a decomposition of the correlated clinical PSA prior. [SOBOL]"
)
p(
    "The five most influential decision coordinates on the selection sample drive a complete 5⁵ = 3,125-point grid:"
    " effect, hospital difference, avoidable fraction and fixed/mobile capital attribution. A separately prespecified"
    " 7⁴ = 2,401-point equipment grid varies kit cost, kit delivery, utilisation and effect. All grid outcomes are"
    " exact; their frequencies are design coverage, not probabilities."
)
heading("8. Unsupervised then supervised analysis: useful limits")
fig("12_clusters", 6.5)
p(
    "Input-only clustering was fitted without outcomes and without looking at the holdout. The silhouette was 0.052;"
    " repeated initialisations had adjusted Rand agreement 0.001 and 0.109. Thus the partitions are unstable and not"
    " convincing natural regimes. All clusters were retained. No patient, hospital or clinical subgroup was discovered."
)
p(
    "The initial cost-regression forest had high R² but poor decision agreement. Two classifiers were compared on a"
    " separate selection sample. That diagnostic holdout was retired; final reporting uses a new independent holdout"
    " (seed 504) without additional tuning. The chosen histogram-gradient classifier explains exact decision labels."
    " It is not used to replace the model."
)
table(
    ["Independent holdout metric", "Decision classifier"],
    [
        ["Accuracy / balanced accuracy", "95.0% / 93.3%"],
        ["Mean / worst annual pilot regret", "$60 / $8,970"],
        ["Within $100 / $1,000 of exact best", "95.3% / 98.0%"],
        ["Role", "Explanatory only; not clinical or procurement validation"],
    ],
)
heading("9. Which assumptions are worth clarifying?")
fig("13_decision_importance", 6.6)
p(
    "Held-out permutation diagnostics identify clinical effect as the leading decision driver, followed by net"
    " hospital costs, avoidable retrieval resources, shared-capital attribution and prototype delivery. Importance is"
    " measured as the increase in exact-model annual regret after permuting a coordinate, not as a causal effect or"
    " EVPPI. Correlated clinical priors are not inferred from this independent design. [PERM]"
)
p(
    "The selected classifier has a nontrivial worst-case error despite high average agreement. The shallow explanatory"
    " tree has much greater regret and is not suitable as a decision rule. Every headline result, grid and ranking in"
    " this report is evaluated by the exact model, not by a learned approximation."
)
p(
    "The analysis is broad but not exhaustive. Route-specific retrieval times, repeated consultations per infant,"
    " antenatal transfers, correlated outages/hub delays and a calibrated lifetime cost-utility model remain"
    " limitations. The original 58 scenarios, 108 survival/morbidity combinations and budget tables remain available;"
    " they are not reclassified as five-device clinical evidence."
)
heading("10. Publication recommendation and manuscript design")
table(
    ["Priority / journal", "Fit and suggested presentation"],
    [
        [
            "1. Journal of Telemedicine and Telecare",
            (
                "Best first choice; comparative/economic analyses encouraged. Generally 3,000 body words; 250-word"
                " structured abstract."
            ),
        ],
        [
            "2. Telemedicine and e-Health",
            (
                "Close topical alternative; prior teleneonatology model. Emphasise costs, access and diffusion; verify"
                " current detailed limits."
            ),
        ],
        [
            "3. Cost Effectiveness and Resource Allocation",
            "Strong methods-forward alternative: modelling, uncertainty and resource allocation explicitly in scope.",
        ],
        [
            "4. Australian Health Review",
            (
                "Best Australian commissioning audience; 2,500-word article. Funding/resource distinction and"
                " implications"
                " for HHSs."
            ),
        ],
        [
            "5. Journal of Medical Internet Research",
            "Stretch target; strengthen international generalisability and independent validation.",
        ],
    ],
)
p(
    "Suggested title: “Choosing neonatal teleconsultation technology for regional hospitals: a five-strategy economic"
    " model and uncertainty analysis in Queensland”. The contribution is not “telemedicine saves money”: prior studies"
    " exist. It is configuration choice, sunk versus new capital, transparent contemporary costs, paired uncertainty"
    " and a reusable decision framework. [JTT; TEH; CERA; AHR; JMIR]"
)
p(
    "JTT lists no fee for its subscription route; optional open access is separate. CERA currently lists an APC of"
    " £2,190 / US$2,890 / €2,490 before applicable taxes, determined at acceptance. Institutional agreements or"
    " waivers need verification. Other journal-specific fees have not been verified."
)
p(
    "Keep machine learning in the supplement. The main paper should show options/assumptions, evidence mapping,"
    " five-arm outcomes, incumbent decisions, one-way drivers and one or two exact decision surfaces. Use CHEERS 2022"
    " with a separate budget-impact section; it is a reporting framework, not proof of validity. No journal submission"
    " has been made. [CHEERS]"
)
heading("11. Publication readiness, reproducibility and sources")
p(
    "Before submission: verify the critical studies in full text; obtain independent clinical/economic model review;"
    " retain unverified quotes and costs as assumptions; resolve governance, authorship, conflicts, funding, data"
    " rights and AI-use disclosure; complete a connected locked-environment verification run. Neither new trial"
    " recruitment nor structured expert elicitation is a prerequisite. Do not invent an ethics exemption or external"
    " endorsement."
)
p(
    "The exact model adds no pandas/xarray dependency. Offline sensitivity/explanation uses NumPy/SciPy/scikit-learn"
    " arrays; the new target versions are SciPy 1.18.1 and scikit-learn 1.9.1, but this run used installed 1.17.0 and"
    " 1.8.0. Latest-toolchain compatibility and hosted CI are not certified. Conductor records implementation"
    " separately from blocked acceptance. Numerical results are not a substitute for clinical evidence."
)
p(
    "Source ZIP and Git bundle are working handoffs. Do not publicly redistribute the full ELC pack, corporate artwork"
    " or restricted records without permission. Prepare a clean research release from authorised code and derived data."
)
refs = list(csv.DictReader((ROOT / "evidence/v5/sources_v5.csv").open()))
for row in refs:
    para = s.add_paragraph(f"[{row['source_id']}] {row['source']}. {row['locator']}")
    para.paragraph_format.space_after = Pt(4)
    for run in para.runs:
        run.font.size = Pt(8)
p(
    "Full original source/parameter registers, current journal register, all numerical outputs, code and actual"
    " verification receipts are included in the repository. This supplement reports v5 model outputs [M5]; retained"
    " v2/v4 material is denoted [M2]."
)
save_neutralised(s, OUT / "Panda_Vision_comparative_supplement_v5.docx")
print("Created plan and supplement")  # ruff: ignore[print] -- build script reports completion to stdout
