"""Parameter, privacy, dependency and simulated-review evidence inventory."""
from __future__ import annotations
from pathlib import Path
import ast,csv,hashlib,json,shutil,subprocess,sys,importlib.metadata
from dataclasses import asdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.statewide import Parameters
from src.pathways_v6 import PathwaySpec
E=ROOT/'evidence/v7';V=ROOT/'verification/v7';D=ROOT/'docs/validation/v7'
for p in (E,V,D):p.mkdir(parents=True,exist_ok=True)
retired={'rescue_rate','rescue_premium','downstream_delta','hub_annual_cost','capacity_threshold','capacity_step_cost'}
distributions={
 'equipment_cost':('triangular','8000;10000;15000','ELC2026; USER2026','10000 is mode; mean11000; source point estimate not invoice'),
 'life_years':('triangular','3;5;7','ASSUMED','symmetric mode/mean5'),
 'calls_per_pilot_site':('triangular','10;12.5;15','USER2026','forecast per site; not fitted to4-5cases'),
 'reliability':('beta mean/precision','mean.95;precision20','ASSUMED','nonreference mean reparameterised; no clipping'),
 'baseline_transfer':('beta; critical fixed','(.30,.65,.98);precision20 for first2','ASSUMED','not observed local fractions; critical .98 is not certain transfer'),
 'case_mix':('Dirichlet','(.35,.50,.15);concentration20','ASSUMED','concentration is judgement, not observed sample size'),
 'odds_ratio':('normal log-OR','log(sqrt(.48));SE from.26-.90;transport SD.35','HAY2020','transported observational association; no local posterior or causal fit'),
 'road_cost':('triangular','2000;4000;8000','ASSUMED','4000 mode; mean4667; not QAS tariff'),
 'air_multiplier':('lognormal anchor','log(indexed18670);SDlog.35','AIR2019; CPI2019; CPIBASE; CPI2026','indexed point is median; mean is higher; source-price year uncertain'),
 'marginal_fraction':('beta mean/precision','mean.5;precision4','ASSUMED','resource avoidability, not guaranteed cash release'),
 'family_delta':('triangular','0;1500;4000','ASSUMED','gross travel/time aggregate; not measured parent costs; avoid productivity double counting'),
 'workflow_per_call':('triangular','0;75;175','ASSUMED','split local25 and15minhub200/h at reference; common phone time excluded'),
 'check_minutes':('triangular','5;10;20','ELC2026; ASSUMED','weekly checks documented; duration assumed'),
 'support':('triangular','0;300;1000','ASSUMED','mean433 not mode300'),
 'training':('triangular','100;400;1200','ASSUMED','mean567 not mode400'),
 'birth_growth':('triangular','.8;1;1.2','ASSUMED','not fitted birth trend'),
 'mode_air_shift':('clipped normal','mean0;SD.1;limits+/- .6','ASSUMED; NEOSTRESS2020','geographic proxy; structural alternatives more important than exact tail'),
 'phone_delay_share':('beta mean/precision','mean.05;precision20','ASSUMED','eventual-transfer partition, not second failed-retention penalty'),
 'video_delay_share':('shared delay plus scenario difference','reference equal phone','ASSUMED','shared reference timing; no independently fitted video effect'),
 'hospital_marginal_fraction':('beta mean/precision','mean.5;precision4','ASSUMED','benchmark fraction; not actual finance data'),
 'hospital_resource_multiplier':('mean-one lognormal','SDlog.25','ASSUMED; NEP26','all hospital component prices share multiplier'),
 'local_care_multiplier':('triangular','.7;1;1.8','ASSUMED','mode1;mean1.1667; plausible increased local care allowed'),
 'extra_pre_rescue_cost':('triangular','0;2000;6000','ASSUMED','mode2000;mean2667; duration not empirically calibrated')}
rows=[]
for group,values in [('Parameters',asdict(Parameters())),('PathwaySpec',asdict(PathwaySpec()))]:
 for name,value in values.items():
  dist,range_,source,note=distributions.get(name,('fixed/scenario',str(value),'ASSUMED','no empirical fitting; see structural sensitivity'))
  if name in retired:dist='retired';range_='not active';note='Retained for historical v2-v5 compatibility, not used in active pathway costs'
  rows.append({'group':group,'parameter':name,'reference':json.dumps(value),'active':name not in retired,'distribution':dist,'range_or_parameters':range_,'source_id':source,'verification':note})
for name,ref,bounds,note in [
 ('receiver_share',.5,'0-1','CHHHS share of receiving resource changes; routing/payment unknown'),
 ('retrieval_chhhs_share',1.,'0-1','origin CHHHS allocation, not confirmed current inter-HHS contract'),
 ('family_travel_share',.4,'0-1','within existing aggregate; remaining share time; no added gross cost'),
 ('subsidy_fraction',.5,'0-1','hypothetical subsidy on travel share, not actual PTSS eligibility/rates'),
 ('funding_response',0.,'0 or.405 illustrative','fixed reference; .405 uncapped benchmark floor case, not entitlement calculator'),
 ('readiness_calls',0.,'0;1 per site/year','zero reference is zero credited benefit, not zero need'),
 ('Cooktown_reopened_births',50.,'assumed50; not observed','2022suspension makes historical denominator incomplete')]:
  rows.append({'group':'Perspective/regional scenario','parameter':name,'reference':ref,'active':True,'distribution':'fixed scenario; NOT fitted','range_or_parameters':bounds,'source_id':'ASSUMED','verification':note})
with (E/'parameter_audit.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
# Check project imports only; the shared authoring host may contain pandas.
imports=[]
for folder in ('src','quality','scripts','tests'):
 for p in (ROOT/folder).rglob('*.py'):
  tree=ast.parse(p.read_text())
  for node in ast.walk(tree):
   modules=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or ''] if isinstance(node,ast.ImportFrom) else []
   for module in modules:
    if module.split('.')[0] in ('pandas','xarray'):imports.append({'path':str(p.relative_to(ROOT)),'module':module})
# A bounded complementary scan; explicitly not Gitleaks or a secret-free guarantee.
import re
patterns={'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
          'github_token':re.compile(r'gh[pousr]_[A-Za-z0-9]{36,}'),
          'aws_access_id':re.compile(r'AKIA[0-9A-Z]{16}')}
hits=[];scanned=0
for p in ROOT.rglob('*'):
 if not p.is_file() or any(k in p.parts for k in ('.git','extensions','.venv','outputs','verification','sources')) or p.stat().st_size>2_000_000:continue
 if p.suffix not in ('.py','.md','.json','.yml','.yaml','.toml','.csv','.txt','.js'):continue
 scanned+=1;text=p.read_text(errors='replace')
 for label,pat in patterns.items():
  for match in pat.finditer(text):hits.append({'path':str(p.relative_to(ROOT)),'rule':label,'line':text[:match.start()].count('\n')+1,'value':'REDACTED'})
probes={}
for tool in ('ruff','ty','basedpyright','gitleaks','vale','actionlint','zizmor','prek'):
 try:
  a=subprocess.run([tool,'version' if tool=='gitleaks' else '--version'],capture_output=True,text=True,timeout=15,check=False)
  probes[tool]={'status':'available' if a.returncode==0 else 'failed','exit_code':a.returncode,'output':a.stdout[:200]}
 except (FileNotFoundError,subprocess.TimeoutExpired) as exc:probes[tool]={'status':'blocked','reason':type(exc).__name__}
# No scan is claimed when the actual requested executable is unavailable.
report={'project_pandas_xarray_imports':imports,'bounded_text_scan_files':scanned,'bounded_text_findings':hits,
 'gitleaks_actual':probes['gitleaks'],'gitleaks_passed':False,'tool_probes':probes,
 'privacy':'No patient-level records added. Corporate originals and selected ELC extract remain private. No cloud inference or code upload for profiling.',
 'release':'No hosted CI, full locked environment, independent agent review or public publication is claimed.'}
(V/'privacy_security.json').write_text(json.dumps(report,indent=2))
print('Parameters audited:',len(rows),'forbidden imports:',len(imports),'bounded findings:',len(hits),'Gitleaks:',probes['gitleaks']['status'])
