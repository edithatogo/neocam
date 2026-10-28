"""Write bounded source-verification and validation-status registers."""
import csv,json
from pathlib import Path
from dataclasses import asdict
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.pathways_v6 import PathwaySpec,NEP26,WEIGHTS
E=ROOT/'evidence/v6';D=ROOT/'docs/validation/v6';E.mkdir(exist_ok=True,parents=True);D.mkdir(exist_ok=True,parents=True)
rows=[
('HAY2020','Haynes et al 2020','10.1016/j.acap.2020.02.013','https://pubmed.ncbi.nlm.nih.gov/32081766/','ABSTRACT_ONLY; full text blocked','PubMed ID mapping; publisher full-page fetch; institutional repository/title search; TinyFish bot_blocked','Retain OR .48 (CI .26-.90) as provisional observational input; do not certify timing endpoint or all exclusions','Core effect; further full-text check required'),
('ARM2012','Armfield et al 2012','10.1258/jtt.2012.gth101','https://pubmed.ncbi.nlm.nih.gov/23148301/','ABSTRACT_ONLY; full text blocked','PubMed mapping; Sage fulltext and alternate publisher route; Library exact-title search','19 consultations and five independently assessed avoided transports; no reconstructed original cost table claimed','Core economic precedent; original cost year/components remain unverified'),
('YOO2022','Yoo et al 2022','10.1016/j.jpeds.2021.11.076','https://pubmed.ncbi.nlm.nih.gov/35074308/','ABSTRACT_ONLY; full text blocked','PubMed mapping; ScienceDirect/J Pediatr fullpage; TinyFish bot_blocked','Decision model/PSA and 2017 USD reported; do not import missing unit-cost tables or claim independent effect replication','Core economic precedent; likely overlapping California effect evidence, not independently pooled'),
('THAO2022','Thao et al 2022','10.1089/tmj.2021.0527','https://pubmed.ncbi.nlm.nih.gov/35235430/','ABSTRACT_ONLY; full text blocked','PubMed mapping; Sage fullpage/pdf and alternate route; Mayo bibliographic record; TinyFish bot_blocked','Transport plus NICU/non-NICU costs are model precedents; exact full input table not verified','Core economic precedent; not an independent clinical estimate'),
('HAY2021','Haynes et al 2021','10.1089/tmj.2020.0503','https://pubmed.ncbi.nlm.nih.gov/33691080/','ABSTRACT_ONLY; full text not obtained','PubMed record and publisher page','Adjusted stabilisation difference crosses zero; do not assume proven time or survival benefit','Supporting clinical evidence; full-text verification pending'),
('LIETZ2026','Lietz et al 2026','10.1159/neo/adsag002','https://pmc.ncbi.nlm.nih.gov/articles/PMC13688369/','FULL_BODY_VERIFIED','PubMed/PMC full body, 23573 characters; CC BY','Simulation: 93 participants, mostly students; supported and unsupported scenarios differed. No detected device difference is not proof of equivalence. No real-neonate mortality or transfer endpoint','Supports null/uncertain device-effect structure; not a real clinical-effect estimate'),
('MADDOX2021','Maddox et al 2021','10.3389/fped.2021.648536','https://pmc.ncbi.nlm.nih.gov/articles/PMC8102672/','FULL_BODY_VERIFIED','PubMed/PMC body read including tail at text offset 20000; total 30747 characters; CC BY','Selected >=34-week infants receiving early oxygen; excluded deaths, mandatory/maternal transfers and late video calls. Some extracted table counts/percentages differ from stated sample counts. Do not pool blindly or infer mortality benefit','Qualitative triangulation only; related Intermountain programme is not independent of its earlier evaluation'),
('FOX2024','Fox et al 2024','10.22605/RRH8572','https://www.rrh.org.au/journal/article/8572/','FULL_ARTICLE_TEXT_VERIFIED','Publisher methods/results/discussion read; Table 3 amount also stated in prose','AUD18670 aeromedical cost sourced from QH for Torres Strait skin-infection care in 2018-2019. Not neonatal or mode-specific; source tariff year not separately explicit','Retain as broad resource anchor; source2019 assumption and CPI indexing remain explicit'),
('ARMPOSTER2009','Armfield et al NEMO case-series poster','not assigned','https://chsr.centre.uq.edu.au/files/1037/390_Armfield_poster_4.pdf','COMPLETE_POSTER_TEXT; visual render unavailable','All one-page extracted text; screenshot attempted, cache miss','Ten-case preliminary poster; 2009 AUD, median27-minute total video sessions. This is NOT the 2012 19-case economic paper. Total video time is not incremental time over telephone','Historical comparator only; no duplicate pooling or present-day price replacement'),
('NEP26','IHACPA NEP determination 2026-27','not assigned','https://www.ihacpa.gov.au/sites/default/files/2026-03/national_efficient_price_determination_2026-27.pdf','RELEVANT_PRICE_TEXT_VERIFIED; table screenshot unavailable','Official PDF Appendix A text rows; screenshots attempted, cache miss','NEP7418; P68D .6454, P68B1.4581, P60B.8224, P60A1.6530, P06B7.1826. These are unadjusted episode weights, not daily prices or patient-level coding','Pricing prototype sensitivity; full NWAU calculator and local marginal prices are not validated')]
headers=['id','citation','doi','url','verification_status','retrieval_evidence','critical_finding','model_use']
with (E/'full_text_verification.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(headers);w.writerows(rows)
(E/'retrieval_status.json').write_text(json.dumps({'date':'2026-10-28','complete_critical_full_text_review':False,'core_full_text_gaps':['HAY2020','ARM2012','YOO2022','THAO2022'],'additional_gap':'HAY2021','full_articles_reviewed':['LIETZ2026','MADDOX2021','FOX2024'],'not_substitutes_for_missing_papers':['ARMPOSTER2009'],'automated_independent_panel_executed':False,'additional_provider_attempt':{'provider':'Elicit','result':'api_access_denied','consequence':'No paper content returned; no verification credit'}},indent=2))
definitions = {
 'phone_delay_share': ('proportion', 'Primary: delayed share of eventual transfers; alternate initial structure: rescue risk among initially local infants', 'Beta(1,19) at reference mean0.05; analyst assumption'),
 'video_delay_share': ('proportion', 'Same denominator as phone within each endpoint structure; used after successful video only', 'Common phone draw plus specified video-minus-phone offset, bounded0–1; reference equal timing'),
 'extra_rescue': ('conditional probability', 'Proportion of otherwise finally retained infants shifted to delayed rescue after successful video; NOT absolute percentage points among all calls', 'Reference0; scenario0.02; deterministic0–0.10; not empirically fitted'),
 'endpoint': ('structure', 'Whether the clinical transfer odds ratio concerns eventual transfer or initial decision', 'Eventual reference; initial-decision alternative; critical full-text endpoint unresolved'),
 'local_coordination_per_call': ('AUD/call', 'Additional local video coordination only, above common telephone care', '25reference; jointly scaled by historical video-workflow draw; assumed decomposition'),
 'hub_minutes_per_call': ('minutes/call', 'Additional specialist video time ABOVE telephone consultation time', '15reference, deterministic0–60; jointly scaled by historical workflow draw'),
 'hub_hourly_rate': ('AUD/hour', 'Loaded resource value of incremental specialist time; not automatically new paid hours', '200reference; deterministic100–350; assumption not award-derived'),
 'hub_spare_hours': ('hours/year', 'Workload absorbable without an additional paid capacity block; still has economic value', '100reference; explicit capacity assumption, not measured availability'),
 'hub_block_hours': ('hours/block', 'Additional paid capacity purchased when workload exceeds spare hours', '200reference; positive only; cash sensitivity separate from economic ledger'),
 'hub_block_cost': ('AUD/block/year', 'Cash price per extra capacity block; not added to hourly economic cost', '40000reference; assumption, not funded establishment'),
 'hospital_marginal_fraction': ('proportion', 'Avoidable resource fraction applied to hospital episode-price prototypes; distinct from transport fraction', 'Beta(2,2) reference mean0.5; alternative references rescale and bound; deterministic0–1'),
 'hospital_resource_multiplier': ('multiplier', 'Common hospital-price scale shared across arms and sites', 'Lognormal with mean1 and log-SD0.25, multiplied by reference; assumption'),
 'local_care_multiplier': ('multiplier', 'Local episode resource burden relative to same-stratum receiving prototype', 'Triangular(0.7,1.0,1.8) times reference; reference is MODE, not mean; deterministic0.7–2'),
 'extra_pre_rescue_cost': ('AUD/rescue', 'Additional pre-rescue hospital-care benchmark beyond originating and receiving episodes', 'Triangular(0,2000,6000) scaled by reference; reference2000 is MODE, not mean; resource fraction applied'),
 'rescue_receiving_premium': ('AUD/rescue', 'Additional rescue-associated resource penalty; not a second full hospital episode', 'Reference0; deterministic0–30000; separate from hospital benchmark fraction')
}
assum=[]
for k,v in asdict(PathwaySpec()).items():
 unit,definition,uncertainty=definitions[k]
 assum.append({'parameter':k,'reference':v,'unit':unit,'interpretation':definition,'uncertainty':uncertainty,'provenance':'Analyst assumption or structural interpretation; not a new empirical observation'})
with (ROOT/'data/v6/structural_assumptions.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=assum[0]);w.writeheader();w.writerows(assum)
(ROOT/'data/v6/spec.json').write_text(json.dumps(asdict(PathwaySpec()),indent=2))
(ROOT/'data/v6/hospital_prototypes.json').write_text(json.dumps({'nep':NEP26,'weights':WEIGHTS,'origin':['P60B','P60B','P60A'],'receiving':['P68D','P68B','P06B'],'local':['P68D','P68B','P06B'],'mapping':'Hypothetical price prototypes, not observed DRG allocation','resource_fraction':.5,'qep':None,'qwau_adjustments':None},indent=2))
(E/'retired_parameter_uses.md').write_text('''# Historical inputs not active in the primary v6 kernel

`hub_annual_cost`, `capacity_threshold` and `capacity_step_cost` are retired from active economic calculations. Their v5 values survive only for the numerical bridge.

`downstream_delta` is replaced by explicit non-overlapping hospital episodes. `rescue_rate` and `rescue_premium` no longer impose penalties on net avoided transfers. New timing and additional rescue assumptions are separately registered. Historical draws may still be generated by the frozen sampler, but these retired variables do not affect v6 results.

No mortality effect or complete societal utility valuation is claimed. Lifetime and machine-learning experiments remain historical supplements, not active primary inference. Price-equivalent units must not be called actual coded NWAU/QWAU or cash.
''')
# Distinct validation domains, with no invented independent reviewers.
checks=[
('ISPOR face validity','PARTIAL_SELF_REVIEW','Explicit pathways, target population and outcome boundary documented','Independent neonatal/retrieval/health-economic reviewers have not assessed the model'),
('ISPOR internal verification','EXECUTED','Separate scalar oracle, hand calculation, mass conservation, null/boundary and cost-ledger tests','Same author wrote implementation and oracle; no independent authorship'),
('ISPOR cross validation','PARTIAL','Numerical v5-v6 bridge and comparison of model structures with published precedents','Not an independent replication of missing full-text economic models'),
('ISPOR external validation','NOT_AVAILABLE','No external episode-level calibration data used','Not a validated clinical forecast'),
('ISPOR predictive validation','NOT_PERFORMED','No prospective predictions tested','Not required to begin early modelling; cannot claim demonstrated performance'),
('AdViSHE conceptual structure','DOCUMENTED; independent review pending','Spec, pathway equations and absolute counts','Formal independent face-validity sign-off absent'),
('AdViSHE input data','PARTIAL','Historical source register, newly separated assumptions, full-text audit','Four core papers and local costs/capability not fully verified'),
('AdViSHE implementation','TECHNICALLY_CHECKED','Regression and scalar-oracle tests; separate site aggregation test','Latest locked environment and independent code reviewer remain pending'),
('AdViSHE outcomes','PARTIAL','Scenario/PSA checks and historical bridge','No empirical validation of predicted avoided transfers'),
('TECH-VER input calculations','EXECUTED_WITH_LIMITS','Bounds, component sums, unadjusted price weights, missing QEP retained','Benchmarks are not patient-level DRG classification'),
('TECH-VER patient flow','EXECUTED','Arm/stratum conservation; initial/local/rescue/final counts; failure fallback','Timing shares and rescues are assumptions'),
('TECH-VER result calculations','EXECUTED','Hospital components counted once; separate economic/cash ledgers; hand example655','Cash release is not inferred from resource benefit'),
('TECH-VER uncertainty calculations','EXECUTED','Paired PSA, null and harmful-effect scenarios, coherent shared draws','Researcher priors; not posterior uncertainty'),
('TECH-VER overall independent verification','PENDING','Four reviewer briefs and acceptance schema provided','No available subagent runner; not independently reviewed'),
('CHEERS reporting','PARTIAL','Decision, comparators, perspective, horizon, assumptions, uncertainty and results reported','Manuscript abstract, authorship, governance, conflicts, consumer involvement statements await author approval')]
with (D/'standards_assessment.csv').open('w',newline='') as f:w=csv.writer(f);w.writerow(['domain','status','evidence','limitation']);w.writerows(checks)
(D/'README.md').write_text('''# Validation status — not an independent-panel endorsement

Actual work: author-led source review and code review; separately expressed scalar arithmetic for 20 seeded cases; exact component and cohort conservation; null/failure/critical-case tests; historical result bridge. These checks verify implementation, not clinical validity.

Requested panel: **not executed**. No subagent execution tool or installed agent CLI was available. Plugin discovery found no usable independent-review execution route. Do not convert four role descriptions into four reviewers or label author self-review independent.

`reviewer_*.md` are ready-to-run briefs, not completed reviews. An eventual panel must use separate fresh contexts, inspect sources/code independently, provide findings with severity and reproducible evidence, and identify model/version/hash. Agent agreement does not replace qualified clinical/economic face validation.

Sources: ISPOR-SMDM report7 https://www.ispor.org/heor-resources/good-practices/article/model-transparency-and-validation ; AdViSHE https://doi.org/10.1007/s40273-015-0327-2 ; TECH-VER https://doi.org/10.1007/s40273-019-00844-y ; CHEERS2022 https://www.ispor.org/heor-resources/good-practices/cheers . This assessment is aligned to their domains; it is not an endorsed certification or numeric quality score.
''')
briefs={
 'clinical':'Assess whether final-transfer versus initial-decision endpoints, failed-video fallback, critical strata, delayed rescue timing and discharge/local-care endpoints represent plausible neonatal practice. Identify harms excluded by cost-only ranking. Do not provide invented numerical estimates.',
 'economics':'Independently reconstruct hub resource time, paid capacity blocks, hospital component costs, replacement schedules and counterfactual economic versus cash costs. Check comparators and use of unadjusted DRG prototypes. Test double counting and explain which assumptions can reverse the choice.',
 'evidence':'Verify full papers independently; classify what was actually retrieved. Check transfer endpoint timing, exclusions, cohort overlap, price years, session versus incremental time and applicability. Do not equate lack of detected device difference with equivalence.',
 'software':'Independently test the active v6 kernel, scalar oracle and analysis driver. Review probability conservation, branch definitions, typed boundaries, budgets, paired uncertainty, source fingerprint and results. Run a clean environment and do not treat absent tools as passes.'}
for role,text in briefs.items():
 (D/f'reviewer_{role}.md').write_text(f'''# {role.title()} reviewer brief — NOT YET EXECUTED

Work from a fresh context; do not adopt the author\'s conclusion. Review `src/pathways_v6.py`, `tests/test_v6_validation.py`, `conductor/tracks/v6-01-pathways/spec.md`, `data/v6`, `evidence/v6` and `outputs/v6`. Do not read another reviewer\'s findings before making your own assessment.

{text}

Return: scope actually inspected; exact model/source commit; critical/major/minor findings; evidence and reproduction commands; proposed remedies; uncertainties; and explicit independence limitations. No patient information is included. Do not issue clinical approval, authorise procurement or upload restricted corporate assets.

Acceptance: reviewer identity/tool/run ID and timestamps are required; missing reports remain pending. The orchestrator records disagreements and fixes, then reruns affected checks.
''')
(D/'panel_status.json').write_text(json.dumps({'requested':True,'executed':False,'reason':'No native subagent runner or agent CLI available; no reviewer tool execution occurred','members':[{'role':r,'status':'pending','run_id':None,'report':None} for r in briefs],'author_self_review':True,'separate_arithmetic_expression':True,'independent_clinical_validation':False},indent=2))
print('Evidence, assumptions and validation boundary registers written.')
