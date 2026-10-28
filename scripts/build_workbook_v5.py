"""Build the v5 workbook using artifact_tool; numerical model remains in Python."""
from pathlib import Path
import csv, json, math
from artifact_tool import Workbook, SpreadsheetFile

root = Path(__file__).resolve().parents[1]
out = root / "outputs/v5"
results = json.loads((out / "results_v5.json").read_text())
wb = Workbook.create()
built = []

def column_letter(n):
    letters = ""
    while n:
        n, r = divmod(n-1, 26)
        letters = chr(65+r) + letters
    return letters

def scalar(x):
    if not isinstance(x,str):
        return x
    if x in ("True","False"):
        return x == "True"
    try:
        v=float(x)
        return int(v) if v.is_integer() and abs(v)<1e15 else v
    except (ValueError, OverflowError):
        return x

def add_sheet(name, title, note, headers, records):
    sh=wb.worksheets.add(name)
    end=column_letter(len(headers))
    sh.get_range("A1").values=[[title]]
    sh.get_range("A1").format.font={"bold":True,"size":15,"color":"#15535C"}
    sh.merge_cells(f"A2:{end}2")
    sh.get_range("A2").values=[[note]]
    sh.get_range(f"A2:{end}2").format.wrap_text=True
    sh.get_range(f"A2:{end}2").format.row_height=35
    sh.get_range(f"A4:{end}4").values=[headers]
    sh.get_range(f"A4:{end}4").format={"fill":"#15535C","font":{"bold":True,"color":"#FFFFFF"},"wrap_text":True,"row_height":35}
    if records:
        sh.get_range_by_indexes(4,0,len(records),len(headers)).values=[[scalar(v) for v in row] for row in records]
    sh.get_range(f"A4:{end}{max(5,len(records)+4)}").format.column_width=20
    sh.get_range(f"A5:A{len(records)+4}").format.column_width=28
    sh.freeze_panes.freeze_rows(4)
    built.append((name,len(records),len(headers)))
    return sh

notes=[
["Scope","Five complete configurations; reference video effects equal by assumption, not demonstrated equivalence."],
["Meaning of costs","Incremental resource use versus telephone; not actual cash release or QWAU/NWAU income."],
["Prototype","Tablet/OBSBOT complete kit is unquoted and not technically approved."],
["Uncertainty","PSA probabilities depend on explicit priors; grid frequencies are not probabilities."],
["Learning","Input clustering is weak; classifiers explain synthetic exact-model results only."],
["Recalculation","Numerical simulations are produced in Python. Workbook edits do not rerun the economic model."],
["Coverage","18 paired PSA structures; one/two-way pilot/state; k-way and learning scoped to pilot."],
["Original evidence","Historical births, QEP, marginal retrieval cost and device-specific effects retain previous limitations."],
["Sources","See Sources and Journal targets; original source and parameter registers retained in repository."],
["Engineering","Ordinary tests and analysis checked; complete latest-toolchain/hosted CI remains unverified."],
]
add_sheet("Read me","Panda Vision — five-option evaluation v5","28 October 2026 | Research working model | Values in AUD unless specified",["Item","Interpretation"],notes).get_range("B5:B14").format.column_width=95
summary_rows=[]
for decision in ["pilot_new","pilot_retain_panda","pilot_prototype_cost_and_reliability_uncertain","state_new","state_prototype_cost_and_reliability_uncertain"]:
    for k,v in results["psa"][decision]["summary"].items():
        summary_rows.append([decision,k,v["mean"],v["lower"],v["upper"],v["p_saving_vs_telephone"],v["p_optimal"],v["expected_regret"]])
sh=add_sheet("Decision summary","Joint five-option PSA results","Mean resource saving and probability cost-optimal are different criteria; 20,000 paired draws.",["Decision","Strategy","Mean saving","2.5% quantile","97.5% quantile","P(saving vs phone)","P(cost-optimal)","Expected regret"],summary_rows)
sh.get_range("C5:E29").set_number_format('#,##0;[Red](#,##0);–')
sh.get_range("F5:G29").set_number_format("0.0%")
sh.get_range("H5:H29").set_number_format('#,##0')
# A simple formula-driven consistency check for each decision.
sh.get_range("J4:K4").values=[["Decision","Sum P(optimal)"]]
for index,decision in enumerate(["pilot_new","pilot_retain_panda","pilot_prototype_cost_and_reliability_uncertain","state_new","state_prototype_cost_and_reliability_uncertain"]):
    row=5+index
    sh.get_range(f"J{row}").values=[[decision]]
    sh.get_range(f"K{row}").formulas=[[f"=SUM(G{5+index*5}:G{9+index*5})"]]
sh.get_range("J4:K9").format.column_width=28
sh.get_range("K5:K9").set_number_format("0.0%")

def from_csv(name,file,note):
    with Path(file).open(newline="") as f:
        rows=list(csv.reader(f))
    return add_sheet(name,name,note,rows[0],rows[1:])

from_csv("Options",root/"data/v5/strategies.csv","Indicative ELC system prices versus unquoted complete-kit assumption.")
from_csv("Ranges",root/"data/v5/sensitivity_ranges.csv","Deterministic ranges, not estimated probability distributions.")
det=list(csv.DictReader((out/"deterministic_strategies.csv").open()))
det_rows=[[v["decision"],v["strategy"],v["gross_resource_benefit"],v["programme_cost"],None,v["incremental_purchase_capital"],v["attributed_capital"]] for v in det]
sh=add_sheet("Deterministic","Exact annual deterministic outcomes","Net saving = gross resource benefit minus incremental programme cost. Full cash purchase and attribution are separate.",["Decision","Strategy","Gross benefit","Programme cost","Net saving","New purchase cash","Attributed capital"],det_rows)
sh.get_range(f"E5:E{len(det_rows)+4}").formulas=[[f"=C{j}-D{j}"] for j in range(5,len(det_rows)+5)]
sh.get_range(f"C5:G{len(det_rows)+4}").set_number_format('#,##0;[Red](#,##0);–')
from_csv("PSA all",out/"psa_strategy_summary.csv","18 paired structures, five strategies; conditional economic probabilities.")
from_csv("Pairwise PSA",out/"pairwise_psa.csv","Differences are paired on the same systematic uncertainty draw.")
from_csv("Seed precision",out/"psa_seed_precision.csv","Independent repeat seeds; small Monte Carlo error does not resolve uncertain clinical evidence.")
from_csv("Journals",root/"evidence/v5/journal_targets.csv","Publisher instructions checked 28 October 2026; selection ranks are reasoned recommendations, not acceptance odds.")
from_csv("Sources",root/"evidence/v5/sources_v5.csv","Original historical evidence registers remain in the repository; restricted ELC material must not be publicly redistributed.")
print("Created",len(built),"sheets.")

from_csv("One way",out/"one_way.csv","12 dimensions × 21 values × 5 arms × 2 portfolios; other inputs fixed.")
from_csv("Two way",out/"two_way.csv","Four complete 31×31 surfaces in each portfolio. Winner is exact-model, not surrogate.")
from_csv("Five way",out/"five_way_selected_grid.csv","3,125 selected design points; design frequencies are NOT probabilities.")
from_csv("Equipment four way",out/"four_way_equipment_grid.csv","2,401 prespecified complete-kit cost/delivery/activity/effect combinations.")
from_csv("Sobol indices",out/"sobol_indices.csv","Independent uniform ranges; not decomposition of correlated clinical PSA. Includes replicate resolutions.")
from_csv("Holdout importance",out/"heldout_permutation_importance.csv","Increase in exact-model mean regret after permutation; not causal effects or EVPPI.")
from_csv("Input clusters",out/"input_cluster_summary.csv","Unsupervised design clusters were weak and unstable; no clinical subgroup inference.")
learn=results["learning"]
learning_rows=[]
for key,label in [("forest","Cost-regression forest"),("classifier","Decision-focused classifier"),("shallow_tree","Shallow explanatory tree")]:
    m=learn[key]
    learning_rows.append([label,m["accuracy"],m["balanced_accuracy"],m["mean_regret"],m["max_regret"],m["regret_95th"],m["near_optimal_100"],m["near_optimal_1000"]])
sh=add_sheet("Learning validation","Fresh held-out decision agreement","4,096 independent exact-model points; seed 504. Explanatory surrogate only, not clinical validation.",["Model","Accuracy","Balanced accuracy","Mean regret","Max regret","95th regret","Within AUD100","Within AUD1000"],learning_rows)
sh.get_range("B5:C7").set_number_format("0.0%")
sh.get_range("G5:H7").set_number_format("0.0%")
sh.get_range("D5:F7").set_number_format('#,##0.00')
# Make narrative and long decision identifiers readable without unbounded autofit.
for name in ["Options","Ranges","Journals","Sources"]:
    sh=wb.worksheets.get_item(name)
    n=next(n for nm,n,c in built if nm==name);c=next(c for nm,n,c in built if nm==name)
    sh.get_range_by_indexes(4,0,n,c).format.wrap_text=True
    sh.get_range_by_indexes(4,0,n,c).format.row_height=60
    sh.get_range_by_indexes(3,0,n+1,c).format.column_width=28
wb.worksheets.get_item("Journals").get_range("B4:H9").format.column_width=42
wb.worksheets.get_item("Sources").get_range("B4:D18").format.column_width=58
wb.worksheets.get_item("Decision summary").get_range("A5:B29").format.wrap_text=True
wb.worksheets.get_item("Decision summary").get_range("A5:H29").format.row_height=34
wb.worksheets.get_item("Read me").get_range("B5:B14").format.wrap_text=True
wb.worksheets.get_item("Read me").get_range("A5:B14").format.row_height=35
print("Workbook contains",len(built),"sheets,",sum(n for _,n,_ in built),"data rows.")
print(wb.inspect({"kind":"region","sheet_id":"Decision summary","range":"J4:K9","max_chars":2000}).ndjson)

print(wb.inspect({"kind":"region","sheet_id":"Deterministic","range":"A4:G9","max_chars":2200}).ndjson)
wb.render({"sheet_name":"Decision summary","range":"A1:H9","scale":1.6}).save(str(out/"Panda_Vision_workbook_preview_v5.png"))
SpreadsheetFile.export_xlsx(wb).save(str(out/"Panda_Vision_comparative_analysis_v5.xlsx"))
print("Exported comparative workbook.")

history = get_ipython().history_manager.input_hist_raw
workbook_cells = [c for c in history if (
    "from artifact_tool import Workbook, SpreadsheetFile" in c
    or c.startswith('from_csv("One way"')
    or c.startswith('print(wb.inspect({"kind":"region","sheet_id":"Deterministic"')
)]
source = '"""Build the v5 workbook using artifact_tool; numerical model remains in Python."""\n' + "\n\n".join(workbook_cells)
source = source.replace('root = Path(__file__).resolve().parents[1]','root = Path(__file__).resolve().parents[1]')
source = source.replace('str(out/"Panda_Vision_workbook_preview_v5.png")','str(out/"Panda_Vision_workbook_preview_v5.png")')
source = source.replace('str(out/"Panda_Vision_comparative_analysis_v5.xlsx")','str(out/"Panda_Vision_comparative_analysis_v5.xlsx")')
Path("/mnt/data/build_workbook_v5.py").write_text(source)
print("Workbook build script retained.")