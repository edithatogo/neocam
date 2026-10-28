from pathlib import Path
import csv, json, math
from artifact_tool import Workbook, SpreadsheetFile
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/v4'
result=json.loads((OUT/'results_v2.json').read_text())
wb=Workbook.create()
import math
def read_csv(path):
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def numeric(value):
    if value is None or value == "": return None
    if value in ("True","False"): return value=="True"
    if isinstance(value,(int,float,bool)): return value
    try:
        x=float(value)
        return int(x) if x.is_integer() else x
    except (ValueError,TypeError): return str(value)

def sheet_table(name, headers, rows, note, widths=None):
    sh=wb.worksheets.add(name)
    n=len(headers); last=max(4,n)
    sh.merge_cells(f"A1:{chr(64+min(last,26))}1")
    sh.get_range("A1").values=[[name+" | Panda Vision v4"]]
    sh.get_range_by_indexes(0,0,1,last).format={"fill":"#15535C","font":{"bold":True,"color":"#FFFFFF","size":16},"row_height":30}
    sh.merge_cells(f"A2:{chr(64+min(last,26))}2")
    sh.get_range("A2").values=[[note]]
    sh.get_range_by_indexes(1,0,1,last).format={"wrap_text":True,"font":{"size":10},"row_height":45}
    matrix=[headers]+rows
    sh.get_range_by_indexes(3,0,len(matrix),n).values=matrix
    sh.get_range_by_indexes(3,0,1,n).format={"fill":"#2F8993","font":{"bold":True,"color":"#FFFFFF"},"wrap_text":True,"row_height":34}
    if rows:
        sh.get_range_by_indexes(4,0,len(rows),n).format={"font":{"size":10},"row_height":20}
    sh.freeze_panes.freeze_rows(4)
    for j in range(n):
        sh.get_range_by_indexes(0,j,len(matrix)+4,1).format.column_width=(widths[j] if widths and j<len(widths) else 19)
    if rows:
        sh.tables.add(sh.get_range_by_indexes(3,0,len(matrix),n),True,"T_"+name.replace(" ","").replace("-",""))
    return sh

readme=sheet_table("Readme",["Item","Meaning"],[
["Status","Preliminary existing-evidence model; not observed CHHHS savings."],
["Scope","Three-site pilot and historical Queensland public-site portfolios."],
["This workbook","Inspectable output tables. PSA values are computed by Python, not recalculated by editing spreadsheet cells."],
["Reproduce","python scripts/run_v2.py --out outputs/v4 --iterations 20000; python scripts/complete_analysis_v4.py"],
["Inputs","No clinical/economic parameter added or changed in engineering v4."],
["Units","AUD; source-specific dates. Current episode pricing and marginal expenditure are different ledgers."],
["Unverified","Installation invoice, local retrieval marginal cost, current QEP/local QWAU, current capability roster."],
["Assurance","Local ordinary tests pass; full latest locked toolchain acceptance is incomplete."],
["Future use","Use the supplied Python source and verified inputs for recalculation; original v2 interactive workbook is retained in repo."],
["DataFrames","No pandas/xarray; artifact_tool authors this delivery workbook outside the numerical model environment."]
],"Read this before interpreting any figures.",[25,100])

summ=[]
for key,label in [("consultations","Forecast consultations"),("programme_cost","Annual economic programme cost"),
                  ("gross_resource_benefit","Gross resource benefit"),("net_saving","Net resource saving (formula)"),
                  ("family_benefit","Family-cost consequence"),("societal_net_saving","Societal net saving (formula)"),
                  ("cash_running_cost","Annual running cash cost")]:
    summ.append([label,result["deterministic"]["pilot"][key],result["deterministic"]["spokes"][key],
                 "Conditional deterministic model, not observed savings"])
summary=sheet_table("Summary",["Measure","Pilot: 3 sites","Illustrative 33-site network","Interpretation"],summ,
                    "Sources: unchanged data/parameters.json and outputs/v4/results_v2.json; positive net saving means lower valued resource use.",[40,20,26,55])
# Data begin row5: programme row6, gross row7, net row8, familyrow9,societalrow10.
summary.get_range("B8:C8").formulas=[["=B7-B6","=C7-C6"]]
summary.get_range("B10:C10").formulas=[["=B8+B9","=C8+C9"]]
summary.get_range("B6:C11").set_number_format('$#,##0;[Red]($#,##0);–')
summary.get_range("B5:C5").set_number_format("0.0")
psarows=[]
for key,val in result["psa"].items():
    psarows.append([key,val["iterations"],val["mean"],val["median"],val["lower"],val["upper"],val["probability_cost_saving"],val["mcse_probability"]])
psa_sheet=sheet_table("PSA",["Structure","Draws","Mean net saving","Median","2.5th percentile","97.5th percentile","Probability cost saving","Monte Carlo SE"],psarows,
                     "Analyst-prior uncertainty, not an empirical posterior. Do not confuse Monte Carlo error with clinical uncertainty.",[27,12,22,22,22,22,23,22])
psa_sheet.get_range("C5:F12").set_number_format('$#,##0;[Red]($#,##0)')
psa_sheet.get_range("G5:H12").set_number_format("0.00%")

files=[
("Scenarios","scenario_results.csv","58 primary deterministic comparisons; existing model assumptions varied."),
("Equipment life","equipment_life_checks.csv","Existing equipment-life parameter tested at 3/5/7 years; other inputs fixed."),
("Break even","break_even_thresholds.csv","Conditional maximum transfer odds ratio for resource break-even, not a causal effect or care recommendation."),
("MC precision","mc_precision.csv","Nested prefixes overlap. MC error does not represent clinical uncertainty."),
("Seed checks","independent_seed_checks.csv","Six fresh 20,000-draw reruns; identical priors, independent seeds."),
("Pilot budget","pilot_five_year_budget.csv","Cash expenditure includes establishment capital in year1, no inflation forecast."),
("State budget","spokes_five_year_budget.csv","Illustrative 33-site public scenario; cash and resource ledgers differ."),
("Sites","site_projection.csv","Historical 2022 birth roster, not a current 2026 capability list. Standalone site cost excludes shared-hub allocation."),
("Survival frontier","survival_morbidity_frontier.csv","108 exploratory combinations; survival effects, utilities and 40-year trajectories are assumed, not calibrated."),
("Funding sensitivity","funding_sensitivity.csv","QEP and QWAU are unverified. Ratio grid is hypothetical, NOT a Queensland payment schedule.")
]
for name,filename,note in files:
    recs=read_csv(OUT/filename);headers=list(recs[0])
    sh=sheet_table(name,headers,[[numeric(row[h]) for h in headers] for row in recs],note)
    for j,h in enumerate(headers):
        if any(t in h for t in ("cost","saving","expenditure","capital","mean_net","benefit","benchmark","total_nmb")) and h!="probability_cost_saving":
            sh.get_range_by_indexes(4,j,len(recs),1).set_number_format('#,##0.00;[Red](#,##0.00)')
        if h in ("p_saving","mcse_probability","survival_gain","major_share","discount","avoidable_fraction"):
            sh.get_range_by_indexes(4,j,len(recs),1).set_number_format("0.00%")
    if name in ("Scenarios","Sites"):sh.get_range("B:B").format.column_width=43

for name,path,note in [
("Parameters",ROOT/"evidence/parameter_register.csv","Source, distribution and limitation mapping; many inputs remain analyst assumptions."),
("Sources",ROOT/"evidence/sources.csv","Primary-source locators and known access/transportability limits. Not a claim of new full-text review."),
("Literature",ROOT/"evidence/literature_parameter_map.csv","Seven-study parameter map; primarily abstract-verified, not a completed systematic review.")
]:
    recs=read_csv(path);headers=list(recs[0])
    sh=sheet_table(name,headers,[[str(row[h]) for h in headers] for row in recs],note)
    sh.get_range_by_indexes(4,0,len(recs),len(headers)).format.wrap_text=True
    sh.get_range_by_indexes(4,0,len(recs),len(headers)).format.row_height=68
    for j in range(len(headers)):sh.get_range_by_indexes(0,j,len(recs)+4,1).format.column_width=35

receipt=json.loads((ROOT/"verification/v4/full/receipt.json").read_text())
ass=sheet_table("Assurance",["Gate","Status","Exit code","Reason"],[[x["gate"],x["status"],x["returncode"],x["reason"]] for x in receipt["receipts"]],
               "Full acceptance unsuccessful: 6 passed, 22 blocked, 1 failed. Missing lock or unavailable tools cannot certify release.",[28,16,12,85])
ass.get_range("D5:D33").format.wrap_text=True
ass.get_range("D5:D33").format.row_height=35
# Chart from audited probabilities only.
summary.get_range("A15:C18").values=[["Effect structure","Pilot probability","State probability"],
["Published",result["psa"]["pilot_published"]["probability_cost_saving"],result["psa"]["spokes_published"]["probability_cost_saving"]],
["Attenuated",result["psa"]["pilot_attenuated"]["probability_cost_saving"],result["psa"]["spokes_attenuated"]["probability_cost_saving"]],
["Sceptical",result["psa"]["pilot_skeptical"]["probability_cost_saving"],result["psa"]["spokes_skeptical"]["probability_cost_saving"]]]
summary.get_range("B16:C18").set_number_format("0.0%")
chart=summary.charts.add("bar",summary.get_range("A15:C18"))
chart.title_text="Cost-saving probability depends on assumed effect"
chart.set_position("F4","O20")
chart.has_legend=True
SpreadsheetFile.export_xlsx(wb).save(str(OUT/"Panda_Vision_analysis_v4.xlsx"))
print(wb.inspect({"kind":"region","sheet_id":"Summary","range":"A4:D11","include":"values,formulas","max_chars":4500}).ndjson)