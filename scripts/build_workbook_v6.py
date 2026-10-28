"""Build the v6 inspectable results workbook using artifact_tool."""
from pathlib import Path
import csv, json
from artifact_tool import Workbook, SpreadsheetFile

root = Path(__file__).resolve().parents[1]
out = root / "outputs/v6"
results = json.loads((out/"results_v6.json").read_text())
wb = Workbook.create()
sheets = []

def col(n):
    text = ""
    while n:
        n, x = divmod(n-1, 26)
        text = chr(65+x) + text
    return text

def number(value):
    if not isinstance(value, str):
        return value
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        n = float(value)
        return int(n) if n.is_integer() and abs(n) < 1e15 else n
    except ValueError:
        return value

def sheet(name, title, note, headers, records, narrative=False):
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
        "fill": "#15535C", "font": {"bold": True, "color": "#FFFFFF"},
        "wrap_text": True, "row_height": 40}
    if records:
        sh.get_range_by_indexes(4,0,len(records),len(headers)).values = [
            [number(v) for v in row] for row in records]
    sh.get_range(f"A4:{width}{max(5,4+len(records))}").format.column_width = 21
    sh.get_range(f"A5:A{max(5,4+len(records))}").format.column_width = 30
    sh.freeze_panes.freeze_rows(4)
    if narrative:
        sh.get_range_by_indexes(4,0,len(records),len(headers)).format.wrap_text = True
        sh.get_range_by_indexes(4,0,len(records),len(headers)).format.row_height = 72
        sh.get_range(f"B4:{width}{4+len(records)}").format.column_width = 43
    sheets.append((name,len(records),len(headers)))
    return sh

def csvsheet(name, path, note, narrative=False):
    with Path(path).open(newline="") as f:
        data = list(csv.reader(f))
    return sheet(name, name, note, data[0], data[1:], narrative)

readme = [
    ["Scope", "Five complete configurations; consultation occurs in every arm. V6 exposes immediate transfer, delayed rescue and final local care."],
    ["Main interpretation", "Early cost–consequence/investment model; not verified savings, clinical equivalence or procurement approval."],
    ["Hospital pricing", "Provisional unadjusted NEP26 × DRG-weight prototypes; not actual patient codes, full NWAU, marginal cash tariffs or QWAU."],
    ["Hub resources", "Incremental video time is costed once. Paid capacity blocks are a separate cash ledger; there is no site-count trigger."],
    ["Evidence", "Three article bodies reviewed; four critical economic/transfer full texts remain inaccessible. See Evidence sheet."],
    ["Independent review", "Requested subagent panel NOT executed; four briefs are pending. Scalar checks are same-author technical verification."],
    ["Uncertainty", "22 structures × 20,000 paired draws. Distribution assumptions are not empirical posterior estimates."],
    ["Recalculation", "Simulation results come from Python. Spreadsheet edits do not rerun the economic model. Formula checks reconcile exported values."],
    ["Funding", "Current QEP and local QWAU weights remain unknown. No hypothetical price is presented as an official Queensland tariff."],
    ["Release status", "Latest-toolchain, genuine lockfile, populated Conductor checkout, hosted CI and independent clinical validation are not certified."]
]
sh=sheet("Read me", "Panda Vision — explicit pathways and validation v6",
         "28 October 2026 | Working model | Monetary values in AUD unless specified",
         ["Topic","Interpretation"],readme,True)
sh.get_range("B4:B14").format.column_width = 100
sh.get_range("A5:B14").format.row_height = 42

summary=[]
for portfolio in ["pilot", "spokes"]:
    for scenario in ["reference", "retain_panda", "prototype_uncertain", "null"]:
        for key, item in results["psa"][f"{portfolio}_{scenario}"]["summary"].items():
            summary.append([portfolio,scenario,key,item["mean"],item["lower"],item["upper"],item["p_saving_vs_telephone"],item["p_optimal"],item["expected_regret"]])
sh=sheet("Decision summary","Paired comparative probabilistic results",
         "Same uncertainty draw across arms; probability-best is not probability-saving. Reference device equivalence is assumed.",
         ["Portfolio","Scenario","Strategy","Mean saving","2.5%","97.5%","P(saving)","P(optimal)","Expected regret"],summary)
sh.get_range("D5:F44").set_number_format('#,##0;[Red](#,##0);–')
sh.get_range("G5:H44").set_number_format("0.0%")
sh.get_range("I5:I44").set_number_format('#,##0')
sh.get_range("A5:C44").format.wrap_text = True
sh.get_range("A5:I44").format.row_height = 30
sh.get_range("K4:L4").values=[["Decision group","Sum P(optimal)"]]
for idx in range(8):
    row=5+idx
    sh.get_range(f"K{row}").values=[[f"{summary[5*idx][0]} / {summary[5*idx][1]}"]]
    sh.get_range(f"L{row}").formulas=[[f"=SUM(H{5+idx*5}:H{9+idx*5})"]]
sh.get_range("K4:K12").format.column_width=35
sh.get_range("L4:L12").format.column_width=20
sh.get_range("L5:L12").set_number_format("0.0%")

with (out/"deterministic.csv").open() as f:
    det = list(csv.DictReader(f))
checkrows=[[v["portfolio"],v["strategy"],v["consultations"],v["immediate_transfers"],
            v["delayed_rescues"],v["final_local"],None,v["gross_resource_benefit"],
            v["programme_cost"],None,v["net_saving"],None] for v in det]
sh=sheet("Accounting checks","Population and incremental-cost reconciliation",
         "Cohort residual and model/formula difference must be approximately zero. Net resource saving is not cash released.",
         ["Portfolio","Strategy","Consultations","Immediate","Rescue","Final local","Cohort residual","Gross benefit","Programme cost","Calculated net","Model net","Difference"],checkrows)
for row in range(5,5+len(checkrows)):
    sh.get_range(f"G{row}").formulas=[[f"=C{row}-SUM(D{row}:F{row})"]]
    sh.get_range(f"J{row}").formulas=[[f"=H{row}-I{row}"]]
    sh.get_range(f"L{row}").formulas=[[f"=J{row}-K{row}"]]
sh.get_range(f"C5:L{4+len(checkrows)}").set_number_format('#,##0.00;[Red](#,##0.00);–')

for name,filename,note in [
    ("Pathways","pathways.csv","Absolute arm-level outcomes, not only net avoided transfers; initially local is an intermediate node."),
    ("Hospital components","deterministic.csv","Full component output. Price-equivalent units are not actual NWAU. Economic and cash hub ledgers are separate."),
    ("PSA all","psa_summary.csv","22 paired scenario structures × 20,000 draws; no clinical equivalence established."),
    ("Pairwise","pairwise.csv","Within-draw pairwise differences, preserving shared systematic uncertainty."),
    ("V5 to V6 bridge","v5_v6_bridge.csv","Separate hub-rule repair from joint pathway and hospital-price changes; not new clinical evidence."),
    ("Cash budget","budget.csv","Seven annual constant-price cash schedules, including replacement. Local staffing cash is assumed."),
    ("Hub workload","hub_thresholds.csv","No dependence on site count; economic hours and paid capacity are separate."),
    ("Hospital prototypes","hospital_prototypes.csv","IHACPA unadjusted episode-price prototypes only. Not a validated patient-level grouper or calculator."),
    ("One way","one_way.csv","12 dimensions × 21 values for two portfolios; all other inputs fixed."),
    ("Two way","two_way.csv","Three 21×21 exact decision surfaces in two portfolios; grid fractions are not probabilities."),
    ("Four way","four_way.csv","625 exact pilot design points; not an estimated clinical distribution."),
    ("Conservation","conservation.csv","Maximum draw-level cohort residual and finite-output checks.")]:
    csvsheet(name,out/filename,note)
csvsheet("New assumptions",root/"data/v6/structural_assumptions.csv",
         "All new structure/cost/timing assumptions are explicit; no new structured elicitation or local observations.",True)
csvsheet("Evidence status",root/"evidence/v6/full_text_verification.csv",
         "Actual retrieval level, model use and limitations. Critical full-text verification is incomplete.",True)
csvsheet("Validation status",root/"docs/validation/v6/standards_assessment.csv",
         "Domain mapping is not ISPOR certification. Independent panel and clinical validation remain pending.",True)
print("Created",len(sheets),"sheets with",sum(n for _,n,_ in sheets),"data rows.")
print(wb.inspect({"kind":"region","sheet_id":"Accounting checks","range":"G4:L9","max_chars":2500}).ndjson)
print(wb.inspect({"kind":"region","sheet_id":"Decision summary","range":"K4:L12","max_chars":1700}).ndjson)
SpreadsheetFile.export_xlsx(wb).save(str(out/"Panda_Vision_analysis_v6.xlsx"))
