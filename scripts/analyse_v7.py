"""Regional/perspective analysis from the exact model; no learned decisions."""
from __future__ import annotations
import csv,itertools,json,sys
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.statewide import Parameters,_base_arrays
from src.pathways_v6 import PathwaySpec,compare_v6,WEIGHTS,NEP26
from src.strategies import KEYS
from src.configuration import load_configuration
from src.equipment import apply_retention, mixed_cash_budget
from src.portfolios_v7 import CHHHS,TCHHS,portfolio,regional_roster,consultation_overrides
from src.audit_v7 import sample_v7,required_health_gain,discounted_health_years
from src.perspectives_v7 import reconcile_ledger,perspective_regret,optimal_probabilities
OUT=ROOT/'outputs/v12'
PERSPECTIVES=('health_system','societal_bounded','provider_chhhs','patient_family','state','commonwealth')


def write(name,rows):
    if not rows:return
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def compare_regional(sites,p,s,*,sunk=(),owned_assets=None,**kwargs):
    """Retain known Panda pilot installations, not hypothetical equipment everywhere."""
    if owned_assets is not None:
        result=compare_v6(sites,p,s,**kwargs)
        apply_retention(result,sites,owned_assets,sunk)
        return result
    other_sunk=tuple(k for k in sunk if k!='panda')
    result=compare_v6(sites,p,s,sunk=other_sunk,**kwargs)
    if 'panda' in sunk:
        fraction=sum(site.pilot for site in sites)/len(sites)
        item=result['panda'];avoided=item['capital_annualised']*fraction
        item['capital_annualised']=item['capital_annualised']-avoided
        item['programme_cost']=item['programme_cost']-avoided
        item['incremental_purchase_capital']=item['full_purchase_capital']*(1-fraction)
        item['net_saving']=item['net_saving']+avoided
        item['net_with_family_extension']=item['net_with_family_extension']+avoided
    return result

def evaluate_perspectives(sites,p,s,x,e,*,reopened=False,readiness_calls=0.,cairns_hub_only=False,
                          receiver_share=.5,retrieval_chhhs_share=1.,subsidy_fraction=.5,
                          family_travel_share=.4,funding_response=0.,sunk=(),overrides=None,owned_assets=None,activity=None):
    for v in (receiver_share,retrieval_chhhs_share,subsidy_fraction,family_travel_share,funding_response):
        if isinstance(v,bool) or not np.isfinite(v) or not 0<=v<=1:raise ValueError('Invalid perspective fraction')
    calls=consultation_overrides(sites,x,reopened=reopened,readiness_calls=readiness_calls,cairns_hub_only=cairns_hub_only)
    r=compare_regional(sites,p,s,inputs=x,structural_draws=e,site_calls=calls,sunk=sunk,overrides=overrides,owned_assets=owned_assets,activity=activity)
    local_sites=[z for z in sites if z.name in CHHHS]
    local=r if local_sites==sites else compare_regional(local_sites,p,s,inputs=x,structural_draws=e,site_calls={k:v for k,v in calls.items() if k in CHHHS},sunk=sunk,overrides=overrides,owned_assets=owned_assets,activity=activity) if local_sites else None
    # Receiving resources allocated to CHHHS must come from the explicitly
    # modelled regional catchment, not every origin in a statewide portfolio.
    catchment_sites=[z for z in sites if z.name in CHHHS+TCHHS]
    catchment=r if catchment_sites==sites else compare_regional(catchment_sites,p,s,inputs=x,structural_draws=e,site_calls={k:v for k,v in calls.items() if k in CHHHS+TCHHS},sunk=sunk,overrides=overrides,owned_assets=owned_assets,activity=activity) if catchment_sites else None
    base=r['telephone'];n=len(x['odds_ratio']);hf=e.get('hospital_fraction',np.full(n,s.hospital_marginal_fraction))
    ledgers={};components={}
    for key,a in r.items():
        health=-a['net_saving'];family=-a['avoided_transfers']*x['family_delta']
        subsidy=family*family_travel_share*subsidy_fraction
        # No actual statutory payment is inferred: response0 is fixed-funding,
        # response.405 is a deliberately uncapped illustrative benchmark scenario.
        cth=(a['hospital_benchmark_cost']-base['hospital_benchmark_cost'])*funding_response
        provider=np.zeros(n)
        if local is not None:
            la,lb=local[key],local['telephone']
            localcare=sum(la[f]-lb[f] for f in ('origin_benchmark_cost','local_benchmark_cost','pre_rescue_benchmark_cost'))*hf
            receiver=(catchment[key]['receiving_benchmark_cost']-catchment['telephone']['receiving_benchmark_cost'])*hf*receiver_share if catchment is not None else np.zeros(n)
            provider=localcare+receiver+(la['transport_resource_cost']-lb['transport_resource_cost'])*retrieval_chhhs_share
            provider+=la['capital_annualised']+la['local_ready_cost']+la['local_workflow_cost']
        ledgers[key]=reconcile_ledger(health_cost=health,family_gross=family,family_subsidy=subsidy,commonwealth=cth,provider_cost=provider)
        components[key]={'family_out_of_pocket':family*family_travel_share-subsidy,'family_time_value':family*(1-family_travel_share),
                         'commonwealth_funding_transfer':cth,'patient_subsidy_transfer':subsidy}
    return r,ledgers,components


def summary(a):
    q=np.quantile(a,[.025,.5,.975]);return {'mean':float(a.mean()),'lower':float(q[0]),'median':float(q[1]),'upper':float(q[2])}


def utility_bridge_scenarios():
    """Illustrative improvements from age 11, discounted back to birth.

    Utility contrasts are observational, not effects of video on prematurity.
    Durations and improved fractions remain assumptions. No effect is credited
    before the age at which the source measured the utility contrast.
    """
    rows=[]
    for u,label in ((.13,'EPICure2 adjusted UK HUI2 SI decrement'),(.28,'EPICure2 adjusted Canadian HUI3 decrement')):
        for duration,rate,improved in itertools.product((1,5,10), (0.,.03,.05), (.001,.005,.01)):
            per=discounted_health_years(np.ones(duration),np.full(duration,u),rate,start_year=11)
            rows.append({'utility_difference':u,'source_metric':label,'duration_years_assumed':duration,
              'start_age_years':11,'discount_rate':rate,
              'fraction_consultations_improved_assumed':improved,'qalys_per_1000_consultations':1000*improved*per,
              'warning':'illustrative disability-improvement bridge from age11; does not mean video prevents prematurity'})
    return rows


def main(config_path=None,output_dir=None):
    global OUT
    config=load_configuration(ROOT,config_path)
    p,s,n,seed=config.parameters,config.pathways,config.draws,config.seed
    OUT=Path(output_dir or ROOT/'outputs/v12').resolve()
    if OUT.exists() and any(OUT.iterdir()):
        raise FileExistsError('Refusing to overwrite an existing analysis directory')
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'resolved_inputs.json').write_text(json.dumps(config.snapshot(),indent=2)+'\n')
    inventories=regional_roster();write('regional_roster.csv',inventories)
    deterministic=[];summaries=[];regrets=[];checks=[];scenarios=[];thresholds=[];vop_draws={};allocation_sensitivity=[];predictive=[];budgets=[]
    networks={name:portfolio(name) for name in config.portfolios}
    x0=_base_arrays(p,1)
    for name,sites in networks.items():
        raw,ledger,parts=evaluate_perspectives(sites,p,s,x0,{},owned_assets=config.owned_assets)
        for key,a in raw.items():
            deterministic.append({'portfolio':name,'sites':len(sites),'strategy':key,'historical_reported_births':sum(z.births for z in sites),
              **{k:float(a[k][0]) for k in ('consultations','immediate_transfers','delayed_rescues','final_local','programme_cost','net_saving','hub_hours')},
              **{z+'_net':float(-ledger[key][z][0]) for z in PERSPECTIVES}})
        configurations=[('reference',{}),('null_effect',{}),('skeptical_effect',{}),('published_effect',{}),('reopened',{'reopened':True}),('readiness_1_call',{'readiness_calls':1.}),
                        ('cairns_referral_only',{'cairns_hub_only':True}),('retain_panda',{'sunk':('panda',)}),
                        ('prototype_uncertain',{}),('provider_local_only',{'receiver_share':0.,'retrieval_chhhs_share':0.}),('uncapped_funding_response_0405',{'funding_response':.405})]
        for scenario,kwargs in configurations:
            mode={'null_effect':'null','skeptical_effect':'skeptical','published_effect':'published'}.get(scenario,'attenuated')
            x,e=sample_v7(p,s,n,seed,mode)
            if scenario=='prototype_uncertain':
                rng=np.random.default_rng(62026)
                kwargs['overrides']={'obsbot':{'installed_cost':rng.triangular(2500,4500,10000,n)*x['equipment_cost']/10000,
                                  'reliability':x['reliability']*rng.triangular(.65,.95,1.,n)}}
            rr,ll,cc=evaluate_perspectives(sites,p,s,x,e,owned_assets=config.owned_assets,**kwargs)
            values={view:np.column_stack([-ll[k][view] for k in KEYS]) for view in PERSPECTIVES}
            for view,matrix in values.items():
                probs=optimal_probabilities(matrix)
                for j,key in enumerate(KEYS):
                    summaries.append({'portfolio':name,'scenario':scenario,'perspective':view,'strategy':key,
                                     **summary(matrix[:,j]),'probability_positive':float(np.mean(matrix[:,j]>0)),
                                     'probability_optimal':float(probs[j]),'unit':'AUD per network-year'})
            for src,dst in itertools.product(PERSPECTIVES,repeat=2):
                v=perspective_regret(values[src],values[dst]);v['choose_indices']='|'.join(KEYS[i] for i in v['choose_indices']);v['target_indices']='|'.join(KEYS[i] for i in v['target_indices'])
                regrets.append({'portfolio':name,'scenario':scenario,'choose_under':src,'evaluate_under':dst,**v})
            if scenario=='reference':
                for key,arm in rr.items():
                    for metric in ('consultations','immediate_transfers','delayed_rescues','final_local',
                                   'eventual_transfers','hub_hours','hospital_benchmark_cost'):
                        predictive.append({'portfolio':name,'strategy':key,'metric':metric,
                                           **summary(arm[metric]),'interpretation':'Prior predictive, not fitted local outcomes'})
            residual=max(float(np.max(np.abs(a['state']+a['commonwealth']+a['patient_family']-a['societal_bounded']))) for a in ll.values())
            mass=max(float(np.max(np.abs(a['immediate_transfers']+a['delayed_rescues']+a['final_local']-a['consultations']))) for a in rr.values())
            checks.append({'portfolio':name,'scenario':scenario,'max_perspective_reconciliation_error':residual,'max_cohort_error':mass})
            if scenario in ('reference','prototype_uncertain'):
                np.savez_compressed(OUT/(name+'_'+scenario+'_perspectives.npz'),**values)
                vop_draws[name+'_'+scenario]=values
            for key,a in rr.items():scenarios.append({'portfolio':name,'scenario':scenario,'strategy':key,**summary(a['net_saving']),
                   'mean_consultations':float(a['consultations'].mean()),'mean_avoided_transfers':float(a['avoided_transfers'].mean())})
        # No-effect health-gain threshold; no QALY is credited in reference analysis.
        pn=replace(p,odds_ratio=1.)
        nr=compare_v6(sites,pn,s)
        for key in KEYS[1:]:
            cost=float(-nr[key]['net_saving'][0]);calls=float(nr[key]['consultations'][0])
            for lam in (30000.,50000.,100000.):
                required=required_health_gain(cost,lam)
                thresholds.append({'portfolio':name,'strategy':key,'additional_annual_cost_no_transfer_effect':cost,
                  'scenario_value_per_qaly':lam,'required_qalys_per_network_year':required,
                  'required_qaly_days_per_consultation':required*365.25/calls if calls else None,
                  'status':'threshold, not estimated video benefit; not an official Australian threshold'})
    for name,sites in networks.items():
        for strategy in KEYS:
            for retain in (False,True):
                for row in mixed_cash_budget(sites,strategy,config.owned_assets,p,s,retain=retain):
                    budgets.append({'portfolio':name,'strategy':strategy,'retain_known_estate':retain,**row})
    write('mixed_estate_budget.csv',budgets)
    write('prior_predictive.csv',predictive)
    # Exact two-way allocation surface: no need to rerun clinical outcomes.
    for name in (key for key in config.portfolios if key!='spokes'):
        rr,ll,cc=evaluate_perspectives(networks[name],p,s,x0,{},owned_assets=config.owned_assets)
        # Receiver share changes provider accounting only; reimbursement changes
        # fiscal/patient accounts only, leaving societal resources invariant.
        for share in np.linspace(0,1,11):
            for subsidy in np.linspace(0,1,11):
                _,l,_=evaluate_perspectives(networks[name],p,s,x0,{},receiver_share=float(share),subsidy_fraction=float(subsidy),owned_assets=config.owned_assets)
                for view in ('health_system','societal_bounded','provider_chhhs','patient_family'):
                    m=np.array([-l[k][view][0] for k in KEYS]);chosen=np.flatnonzero(np.isclose(m,m.max(),rtol=0,atol=1e-9))
                    allocation_sensitivity.append({'portfolio':name,'receiver_share':float(share),'subsidy_share_of_travel':float(subsidy),
                        'perspective':view,'expected_best':'|'.join(KEYS[j] for j in chosen),'maximum_net_value':float(m.max())})
    # The kit is a conceptual comparator, not an approved current procurement option.
    eligibility=[]
    for network in networks:
        data=np.load(OUT/(network+'_reference_perspectives.npz'))
        for view in PERSPECTIVES:
            matrix=data[view][:,:4]
            probs=optimal_probabilities(matrix)
            for j,key in enumerate(KEYS[:4]):
                eligibility.append({'portfolio':network,'perspective':view,'strategy':key,
                  **summary(matrix[:,j]),'probability_optimal':float(probs[j]),
                  'decision_set':'four established categories; local technical suitability still required'})
    write('established_options.csv',eligibility)
    # Age-11 observational utilities are not credited before their evidence age.
    health=utility_bridge_scenarios()
    for name,rows in [('deterministic.csv',deterministic),('psa_perspectives.csv',summaries),('value_of_perspective.csv',regrets),
       ('reconciliation.csv',checks),('structural_scenarios.csv',scenarios),('health_thresholds.csv',thresholds),
       ('allocation_two_way.csv',allocation_sensitivity),('utility_bridge_scenarios.csv',health)]:write(name,rows)
    metadata={'version':'12.0.0','draws':n,'seed':seed,'portfolios':{k:len(v) for k,v in networks.items()},
       'perspectives':PERSPECTIVES,'simulated_review':'role-based author self-review, not independent agents',
       'counts':{'paired_psa_structures':len(checks),'psa_result_rows':len(summaries),'vop_directional_rows':len(regrets),
                 'two_way_allocation_rows':len(allocation_sensitivity),'qaly_thresholds':len(thresholds),'utility_bridge_scenarios':len(health),'prior_predictive_rows':len(predictive),'mixed_estate_budget_rows':len(budgets)},
       'max_mass_error':max(c['max_cohort_error'] for c in checks),'max_ledger_error':max(c['max_perspective_reconciliation_error'] for c in checks),
       'funding':'Fixed fiscal response reference; .405 is an uncapped illustrative benchmark response, not a Queensland entitlement calculator',
       'societal_scope':'Health resources plus existing family travel/time aggregate only; wider education/carer/environment effects unquantified',
       'source_vop_commit':'ad84d3090a2d97f2805a86e94a7b9614a3d1ab14','fit':'No local empirical fitting; labelled transported and researcher priors'}
    (OUT/'results.json').write_text(json.dumps(metadata,indent=2));print(json.dumps(metadata,indent=2))
if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=ROOT/'config/reference.json')
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/v12')
    args=parser.parse_args()
    main(args.config,args.output)
