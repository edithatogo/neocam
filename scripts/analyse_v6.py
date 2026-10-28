"""Reproducible v6 pathway analyses. No learned surrogate or new patient data."""
from __future__ import annotations
import csv
from dataclasses import asdict, replace
import itertools
import json
from pathlib import Path
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.statewide import Parameters, load_sites, select_sites, evaluate, index_air_cost
from src.pathways_v6 import PathwaySpec, compare_v6, sample_v6, cash_budget, WEIGHTS, NEP26
from src.strategies import KEYS, STRATEGIES, summarise
OUT=ROOT/'outputs/v6'; OUT.mkdir(exist_ok=True,parents=True)

def write(name,rows):
    if not rows:return
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def floats(d):return {k:float(v[0]) for k,v in d.items()}

def main():
    p=Parameters();s=PathwaySpec(); all_sites=load_sites()
    portfolios={k:select_sites(all_sites,k) for k in ['pilot','spokes']}
    metadata={'version':'6.0.0','seed':20261028,'draws':20000,'clinical_evidence':'Full-text completion is partial; no updated empirical OR',
              'primary_endpoint':'eventual transfer; delayed timing partition is assumed',
              'hospital_prices':'Unadjusted NEP episode prototypes; not actual clinical DRGs or marginal cash prices',
              'independent_subagent_panel':'not run; no available runner',
              'parameters':asdict(p),'pathway_spec':asdict(s),'deterministic':{},'psa':{}}
    deterministic=[]; bridge=[]; pathway_counts=[]; budget=[]; psa_rows=[]; pairs=[]; conservation=[]
    for portfolio,sites in portfolios.items():
        d=compare_v6(sites,p,s)
        metadata['deterministic'][portfolio]={k:floats(v) for k,v in d.items()}
        for k,a in d.items():
            row={'portfolio':portfolio,'strategy':k,**floats(a)};deterministic.append(row)
            pathway_counts.append({z:row[z] for z in ['portfolio','strategy','consultations','immediate_transfers','initially_local','delayed_rescues','final_local','eventual_transfers','conditional_rescue_risk','avoided_transfers']})
        old=evaluate(sites,p)
        old_hub=0 if len(sites)<=3 else p.hub_annual_cost+max(0,np.ceil((old['consultations']-p.capacity_threshold)/p.capacity_threshold))*p.capacity_step_cost
        bridge.append({'portfolio':portfolio,'v5_net_saving':old['net_saving'],
                       'remove_site_count_hub_charge':float(old_hub),
                       'after_hub_only_repair':old['net_saving']+old_hub,
                       'joint_pathway_and_hospital_pricing_change':float(d['panda']['net_saving'][0])-old['net_saving']-old_hub,
                       'v6_net_saving':float(d['panda']['net_saving'][0])})
        for arm,inc in [('panda',False),('panda',True),('obsbot',False),('mobile',True),('fixed',True)]:
            for r in cash_budget(sites,arm,years=7,incumbent=inc,parameters=p,spec=s):
                budget.append({'portfolio':portfolio,'strategy':arm,'incumbent':inc,**r})
        structures=[('reference','attenuated',s,()),('null','null',s,()),('skeptical','skeptical',s,()),
                    ('published_effect','published',s,()),('retain_panda','attenuated',s,('panda',)),
                    ('prototype_uncertain','attenuated',s,()),
                    ('initial_decision_endpoint','attenuated',replace(s,endpoint='initial'),()),
                    ('video_delays_more','attenuated',replace(s,video_delay_share=.20),()),
                    ('excess_rescue_2pct_retained','attenuated',replace(s,extra_rescue=.02),()),
                    ('no_hospital_offset','attenuated',replace(s,hospital_marginal_fraction=0),()),
                    ('higher_local_burden','attenuated',replace(s,local_care_multiplier=1.5),())]
        for name,mode,ss,sunk in structures:
            x,e=sample_v6(p,ss,n=20000,seed=20261028,effect_mode=mode)
            overrides={}
            if name=='prototype_uncertain':
                rng=np.random.default_rng(62026)
                overrides={'obsbot':{'installed_cost':rng.triangular(2500,4500,10000,20000)*x['equipment_cost']/10000,
                                     'reliability':x['reliability']*rng.triangular(.65,.95,1.,20000)}}
            r=compare_v6(sites,p,ss,inputs=x,structural_draws=e,sunk=sunk,overrides=overrides)
            summ=summarise(r)
            metadata['psa'][portfolio+'_'+name]=summ
            for k,a in summ['summary'].items():psa_rows.append({'portfolio':portfolio,'scenario':name,'strategy':k,**a})
            for pr in summ['pairwise']:pairs.append({'portfolio':portfolio,'scenario':name,**pr})
            errs=[]
            for a in r.values():
                errs.append(float(np.max(np.abs(a['immediate_transfers']+a['delayed_rescues']+a['final_local']-a['consultations']))))
            conservation.append({'portfolio':portfolio,'scenario':name,'max_cohort_residual':max(errs),'finite':all(np.all(np.isfinite(v)) for a in r.values() for v in a.values())})
            if name in {'reference','prototype_uncertain'}:
                np.savez_compressed(OUT/(portfolio+'_'+name+'_draws.npz'),**{k+'_net':a['net_saving'] for k,a in r.items()},
                                    panda_rescue=r['panda']['delayed_rescues'],panda_hours=r['panda']['hub_hours'])
    # Decision-relevant deterministic sensitivity: no frequencies represented as priors.
    axes=[('odds_ratio',.35,1.30,'p'),('calls_per_pilot_site',5,25,'p'),('marginal_fraction',.1,1.,'p'),
          ('life_years',3,7,'p'),('hub_minutes_per_call',0,60,'s'),('hub_hourly_rate',100,350,'s'),
          ('video_delay_share',0,.3,'s'),('extra_rescue',0,.1,'s'),('hospital_marginal_fraction',0,1,'s'),
          ('local_care_multiplier',.7,2,'s'),('extra_pre_rescue_cost',0,10000,'s'),('rescue_receiving_premium',0,30000,'s')]
    one=[]
    for portfolio,sites in portfolios.items():
        for name,lo,hi,kind in axes:
            for v in np.linspace(lo,hi,21):
                pp=replace(p,**{name:float(v)}) if kind=='p' else p
                ss=replace(s,**{name:float(v)}) if kind=='s' else s
                r=compare_v6(sites,pp,ss);winner=max(KEYS,key=lambda k:r[k]['net_saving'][0])
                for k,a in r.items():one.append({'portfolio':portfolio,'parameter':name,'value':float(v),'strategy':k,'net_saving':float(a['net_saving'][0]),'winner':winner})
    two=[]
    grids=[('effect_local_burden','odds_ratio',np.linspace(.35,1.3,21),'local_care_multiplier',np.linspace(.7,2,21)),
           ('effect_rescue','odds_ratio',np.linspace(.35,1.3,21),'extra_rescue',np.linspace(0,.1,21)),
           ('activity_hubtime','calls_per_pilot_site',np.linspace(5,25,21),'hub_minutes_per_call',np.linspace(0,60,21))]
    for portfolio,sites in portfolios.items():
        for name,xname,xs,yname,ys in grids:
            for xx,yy in itertools.product(xs,ys):
                rr=compare_v6(sites,replace(p,**{xname:float(xx)}),replace(s,**{yname:float(yy)}))
                winner=max(KEYS,key=lambda k:rr[k]['net_saving'][0])
                two.append({'portfolio':portfolio,'grid':name,'x_name':xname,'x_value':float(xx),'y_name':yname,'y_value':float(yy),'winner':winner,**{k+'_net':float(a['net_saving'][0]) for k,a in rr.items()}})
    joint=[]
    for effect,burden,rescue,minutes in itertools.product(np.linspace(.4,1.2,5),np.linspace(.7,1.8,5),np.linspace(0,.1,5),np.linspace(0,45,5)):
        r=compare_v6(portfolios['pilot'],replace(p,odds_ratio=float(effect)),replace(s,local_care_multiplier=float(burden),extra_rescue=float(rescue),hub_minutes_per_call=float(minutes)))
        joint.append({'effect':float(effect),'local_burden':float(burden),'excess_rescue':float(rescue),'hub_minutes':float(minutes),'winner':max(KEYS,key=lambda k:r[k]['net_saving'][0]),**{k+'_net':float(a['net_saving'][0]) for k,a in r.items()}})
    threshold=[]
    for calls in [0,12.5,37.5,100,399.9,400,400.1,800,1114.543,1200]:
        from src.pathways_v6 import hub_cost
        h=hub_cost(np.array([calls]),np.array([15.]),s)
        threshold.append({'consultations':calls,'sites':'not used',**{k:float(v[0]) for k,v in h.items()}})
    checks={'max_mass_residual':max(c['max_cohort_residual'] for c in conservation),'all_outputs_finite':all(c['finite'] for c in conservation)}
    for name,rows in [('deterministic.csv',deterministic),('pathways.csv',pathway_counts),('v5_v6_bridge.csv',bridge),('budget.csv',budget),('psa_summary.csv',psa_rows),('pairwise.csv',pairs),('conservation.csv',conservation),('one_way.csv',one),('two_way.csv',two),('four_way.csv',joint),('hub_thresholds.csv',threshold)]:write(name,rows)
    write('hospital_prototypes.csv',[{'drg':k,'unadjusted_weight':v,'nep26':NEP26,'episode_price':v*NEP26,'mapping_status':'Illustrative episode prototype; not patient-level grouping','source':'IHACPA NEP Determination 2026-27 Appendix A, PDF pp82-83'} for k,v in WEIGHTS.items()])
    metadata['analysis_counts']={'psa_structures':len(metadata['psa']),'draws_each':20000,'one_way_arm_rows':len(one),'two_way_points':len(two),'four_way_points':len(joint),'budget_rows':len(budget)}
    metadata['checks']=checks
    (OUT/'results_v6.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps({'counts':metadata['analysis_counts'],'checks':checks,'bridge':bridge},indent=2))
if __name__=='__main__':main()
