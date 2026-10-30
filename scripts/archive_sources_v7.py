# ruff: ignore[implicit-namespace-package] -- scripts/ is a namespace package run via python -m
"""Record actual source holdings. Missing original bytes stay explicitly missing."""

import csv
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "sources"
E = S / "extracts"
ORIGINAL = S / "original"
R = S / "restricted"
for p in (S, E, ORIGINAL, R):
    p.mkdir(exist_ok=True, parents=True)


def csvfile(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    """Write one header row and its data rows to a newline-safe CSV file."""
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(headers)
        w.writerows(rows)


weights = [("P60A", 1.6530, 82), ("P60B", 0.8224, 82), ("P06B", 7.1826, 82), ("P68B", 1.4581, 83), ("P68D", 0.6454, 83)]
csvfile(
    E / "IHACPA_NEP26_verified_rows.csv",
    ["drg", "inlier_weight", "nep", "price", "pdf_page_1based", "appendix", "verification"],
    [
        [
            d,
            w,
            7418,
            w * 7418,
            p,
            "H",
            "web PDF text and page image inspected 2026-10-28; transcription not original workbook",
        ]
        for d, w, p in weights
    ],
)
csvfile(
    E / "NHRA_2026_2031_input_rate_floor.csv",
    ["financial_year", "minimum_input_rate", "page", "warning"],
    [
        [
            f"{y}-{str(y + 1)[-2:]}",
            r,
            27,
            "A36 floor; A35 prior-rate provisions and funding caps also apply. Not a marginal episode payment.",
        ]
        for y, r in zip(range(2026, 2031), (0.405, 0.410, 0.415, 0.420, 0.425), strict=True)
    ],
)
csvfile(
    E / "EPICure2_utility_extract.csv",
    [
        "metric",
        "EP_mean",
        "EP_sd",
        "control_mean",
        "control_sd",
        "adjusted_difference",
        "lower",
        "upper",
        "age",
        "perspective",
        "source",
    ],
    [
        [
            "HUI2 UK SI",
            0.789,
            0.176,
            0.930,
            0.089,
            -0.13,
            -0.18,
            -0.09,
            11,
            "parent proxy; UK adult tariff",
            "PMC9543967 Table4",
        ],
        [
            "HUI3 Canada",
            0.685,
            0.324,
            0.947,
            0.118,
            -0.28,
            -0.37,
            -0.18,
            11,
            "parent proxy; Canadian adult tariff",
            "PMC9543967 Table4",
        ],
    ],
)
(E / "EPICure2_reading_notes.md").write_text(
    "# EPICure2 source abstraction\nSource: Achana et al. Economic costs and health utility values associated "
    "with extremely preterm birth. DOI 10.1111/ppe.12906; PMID35830294; PMC9543967. CC BY4.0.\nFull article "
    "body was read through the rights-eligible PubMed connector in overlapping windows; supplementary files "
    "were not retrieved. This file is an author abstraction, NOT the original article.\n200 extremely preterm "
    "children (<=26 completed weeks, England2006 cohort) and143 term classmates assessed at age11; utility "
    "complete cases161/162 vs118/120. Proxy parent reports; adult preference tariffs. Attrition (200/1031 "
    "survivors assessed) and mainstream-school control selection limit transportability. Utility "
    "instruments/value sets differ and must not be pooled as if measuring an identical decrement.\nUse: "
    "threshold/scenario anchors only. Video does not prevent prematurity; no fraction of this decrement is "
    "empirically attributable to video. UK2019 education/productivity costs are contextual and were not "
    "imported or mechanically exchange-rate-converted.\nTable4 adjusted HUI2 UK MAUF confidence bounds are "
    "typographically inconsistent in parsed source; that row is excluded. Selected UK SI and HUI3 rows have "
    "coherent bounds.\n"
)
(E / "vop_method_contract.md").write_text(
    "# Inspected method contract\nRepository: edithatogo/vop_poc_nz. Commit "
    "ad84d3090a2d97f2805a86e94a7b9614a3d1ab14. File src/vop_poc_nz/perspective.py; "
    "blob6540312b2d46ca75f9f5dcd7e0e56b2f80d8dd88. Method contract1.1.0.\nCurrent-information directional "
    "regret chooses an expected-value optimal fixed strategy under perspective p and evaluates that same "
    "decision under q. Formula: max_d E[NMB_q(d)] - E[NMB_q(d_p)]. Ties require explicit policy; per-draw "
    "optimal decisions are a different diagnostic. Network-year arrays must not be multiplied by patient "
    "population a second time.\nImplementation in src/perspectives_v7.py is a small independently coded NumPy "
    "adapter. The whole upstream package and its tests were NOT executed. This is a method abstraction, not "
    "an original source-code snapshot.\n"
)
(E / "regional_capability_notes.md").write_text(
    "# Regional capability verification\nOfficial CHHHS facility listings support the "
    "hospital/emergency-network inventory, not universal camera eligibility. Primary/community health centres"
    " are outside this14-location scenario; Gordonvale/Herberton and other readiness entries are not claimed "
    "planned birth sites.\nCooktown: official Queensland Health/TCHHS news published9October2026 states "
    "birthing resumed14September2026, after suspension inFebruary2022. Its six recorded2022 births cannot "
    "represent a full operational year. Reopened scenario50/year is assumed and requires sensitivity, not a "
    "reported total.\nWeipa: TCHHS news11February2026 reports32 births2025,14 in2024; service "
    "resumed22May2024. These are separate from the common2022 perinatal denominator.\nCairns referral-only "
    "scenario removes its externally supported birth consultations but retains equipment readiness; referral "
    "handling remains in incremental specialist workload, not another infant cohort. Missing historic counts "
    "are None in roster, not measured zero.\n"
)
(E / "AIHW_burden_notes.md").write_text(
    "# Burden-of-disease source use\nAIHW Australian Burden of Disease Study2024, summary and technical "
    "framework. DALY=YLL+YLD; YLD combines prevalence with sequela-specific disability weights. Projected "
    "population disease burden is not intervention-attributable burden.\nNo neonatal age/condition-specific "
    "DALY table or disability-weight source file was downloaded in this environment. Do not use a national "
    "all-age DALY total per consultation, convert DW to utility by1-DW, or add QALYs and DALYs. The "
    "implemented DALY helper is arithmetic infrastructure, not a calibrated neonatal DALY result.\n"
)
# Supplied corporate originals already present in the project: preserve bytes.
for name in ("Briefing_note.docx", "A4-Report-1-light.docx", "chhhs-powerpoint-template.pptx"):
    path = Path("/mnt/data/source") / name
    if path.exists():
        shutil.copy2(path, ORIGINAL / name)
# Minimise confidential holdings: selected pricing slides only, not all541pages.
import fitz  # ruff: ignore[module-import-not-at-top-of-file] -- optional local PDF reader imported where used

path = Path("/mnt/data/source/ELC_Operational_2026-10-21.pdf")
if path.exists():
    source = fitz.open(path)
    d = fitz.open()
    for page in (219, 221):
        d.insert_pdf(source, from_page=page, to_page=page)
    d.save(R / "ELC_Panda_cost_slides_excerpt.pdf")
    d.close()
    source.close()
records = list(csv.DictReader((ROOT / "evidence/sources.csv").open()))
extra = [
    {
        "source_id": "NEP26_XLSX",
        "publisher": "IHACPA",
        "title": "2026-27 original price-weight workbook",
        "data_year": "2026-27",
        "url": "https://www.ihacpa.gov.au/sites/default/files/2026-03/National_Efficient_Price_Determination_2026-27_Price_Weight_Tables.XLSX",
        "limitations": "Original-byte download failed; selected PDF rows saved as transcription",
    },
    {
        "source_id": "NEP26_PDF",
        "publisher": "IHACPA",
        "title": "2026-27 Determination PDF",
        "data_year": "2026-27",
        "url": "https://www.ihacpa.gov.au/sites/default/files/2026-03/national_efficient_price_determination_2026-27_2.pdf",
        "limitations": "PDF text and page images read; binary download failed",
    },
    {
        "source_id": "NHRA26",
        "publisher": "Australian governments",
        "title": "NHRA2026-31 consolidated addendum",
        "data_year": "2026-31",
        "url": "https://federalfinancialrelations.gov.au/sites/federalfinancialrelations.gov.au/files/2026-04/nhra-2026-31-addendum-consolidated.pdf",
        "limitations": "Relevant clauses/pages read; full binary not downloaded",
    },
    {
        "source_id": "EPICURE2",
        "publisher": "Achana et al.",
        "title": "Economic costs and utilities EPICure2",
        "data_year": "2022",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC9543967/",
        "limitations": "Article body read; selected table transcription saved; not neonatal-treatment effect",
    },
    {
        "source_id": "VICS2021",
        "publisher": "Peart et al.",
        "title": "Victorian extremely preterm HRQoL at age8",
        "data_year": "2021",
        "url": "https://pubmed.ncbi.nlm.nih.gov/33597226/",
        "limitations": "Abstract only; not numerically pooled with EPICure2",
    },
    {
        "source_id": "AIHW_ABDS",
        "publisher": "AIHW",
        "title": "Australian Burden of Disease Study2024",
        "data_year": "2024",
        "url": "https://www.aihw.gov.au/reports/burden-of-disease/australian-burden-of-disease-study-2024/contents/summary",
        "limitations": "Definitions and context only; no neonatal disability weights imported",
    },
    {
        "source_id": "VOP",
        "publisher": "Dylan Mordaunt",
        "title": "vop_poc_nz perspective.py",
        "data_year": "2026",
        "url": "https://github.com/edithatogo/vop_poc_nz/blob/ad84d3090a2d97f2805a86e94a7b9614a3d1ab14/src/vop_poc_nz/perspective.py",
        "limitations": "Method implementation inspected via connector; package not imported",
    },
    {
        "source_id": "CHHHS_DIR",
        "publisher": "CHHHS",
        "title": "Hospital and health centres",
        "data_year": "2026",
        "url": "https://www.cairns-hinterland.health.qld.gov.au/hospitals-and-health-centres",
        "limitations": "Regional hospital/emergency scenario not all community clinics",
    },
    {
        "source_id": "TCHHS_DIR",
        "publisher": "TCHHS",
        "title": "Hospitals and health centres",
        "data_year": "2026",
        "url": "https://www.torres-cape.health.qld.gov.au/hospitals-and-health-centres",
        "limitations": "Four hospital scenario, not every primary-health outpost",
    },
    {
        "source_id": "COOKTOWN26",
        "publisher": "Queensland Health",
        "title": "Cooktown birthing returns",
        "data_year": "2026",
        "url": "https://www.health.qld.gov.au/newsroom/news/cooktown-welcomes-first-baby-following-return-of-birthing-services",
        "limitations": "Reopening date verified, no annualised2026 count inferred",
    },
]
records.extend(extra)
# Register previously used biomedical sources without claiming full-text capture.
for row in csv.DictReader((ROOT / "evidence/literature_parameter_map.csv").open()):
    sid = row.get("source_id") or row.get("study_id") or row.get("study")
    if sid and sid not in {r["source_id"] for r in records}:
        records.append({
            "source_id": sid,
            "publisher": row.get("authors", "Primary research"),
            "title": row.get("title", sid),
            "data_year": row.get("year", ""),
            "url": row.get("url", row.get("doi", "")),
            "limitations": "See retained full-text verification register; not automatically full-text archived",
        })
with (S / "source_register.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["source_id", "publisher", "title", "data_year", "url", "limitations"])
    w.writeheader()
    w.writerows(records)
manifest = []
manifest.extend(
    {
        "path": str(path.relative_to(ROOT)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "bytes": path.stat().st_size,
        "representation": "supplied original"
        if path.parent == ORIGINAL
        else "restricted derived excerpt"
        if path.parent == R
        else "abstraction/extract/registry",
        "redistribution": "not authorised for public release"
        if path.parent in {ORIGINAL, R}
        else "check underlying rights; original source attribution retained",
    }
    for path in sorted(S.rglob("*"))
    if (path.is_file() and path.name != "manifest.json" and "__pycache__" not in path.parts and path.suffix != ".pyc")
)
(S / "manifest.json").write_text(
    json.dumps(
        {
            "date": "2026-10-28",
            "original_public_downloads_complete": False,
            "reason": "Container DNS and container.download failed; no original public PDF/XLSX byte claim",
            "files": manifest,
            "registered_sources": len(records),
        },
        indent=2,
    )
)
(S / "README.md").write_text(
    "# Source archive status\nThis is a PRIVATE working archive. Original supplied corporate templates, a "
    "narrowly selected restricted ELC excerpt, verified numeric transcriptions and source abstractions are "
    "saved. Public original PDFs/XLSX could be read via web but not downloaded as bytes. No fabricated "
    "original files are provided.\nEvery scientific source is registered where present in the inherited "
    "registers; the numerical active inputs retain their source IDs. Missing public originals, four critical "
    "full texts, current QEP, local invoices and local transport invoices remain outstanding.\nRun the opt-in "
    "retrieval script in a network-enabled environment, review rights/content, and regenerate the checksum "
    "manifest before claiming archival completeness. Do not publish corporate originals or the ELC excerpt.\n"
)
print(  # ruff: ignore[print] -- CLI archive summary goes to stdout
    "Registered", len(records), "sources; stored", len(manifest), "files; public originals incomplete."
)
