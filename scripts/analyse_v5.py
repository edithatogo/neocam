"""Paired five-strategy analysis; machine learning explains, never replaces, the exact model."""
from __future__ import annotations
import csv
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time
for env in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ.setdefault(env,'1')
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.statewide import Parameters, load_sites, select_sites, sample_inputs
from src.strategies import KEYS, compare, compare_psa, compare_inputs, summarise
from src.sensitivity import VARIABLES,NAMES,from_unit,evaluate_design,one_way,two_way,k_way,decision_quality
OUT=ROOT/'outputs/v5'

def save_csv(name,rows):
    if not rows:raise ValueError('Empty publication table')
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def write_manifest(directory: Path, root: Path = ROOT) -> None:
    """Write deterministic digests without a recursively changing self-digest."""
    manifest = {
        str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
        for f in sorted(directory.glob('*'))
        if f.is_file() and f.name != 'analysis_manifest.json'
    }
    (directory/'analysis_manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')

def main():
    start=time.monotonic();OUT.mkdir(exist_ok=True,parents=True)
    sites=load_sites();pilot=select_sites(sites,'pilot');state=select_sites(sites,'spokes');p=Parameters()
    seed=20261027;n=20000
    decisions=[('pilot_new',pilot,(),{}),('state_new',state,(),{}),
        ('pilot_retain_panda',pilot,('panda',),{}),('pilot_existing_mobile',pilot,('mobile',),{}),
        ('pilot_existing_fixed',pilot,('fixed',),{}),
        ('pilot_shared_mobile',pilot,(),{'mobile':{'capital_share':.1}}),
        ('pilot_shared_fixed',pilot,(),{'fixed':{'capital_share':.1}}),
        ('pilot_obsbot_7500',pilot,(),{'obsbot':{'installed_cost':7500}}),
        ('pilot_obsbot_reliability80',pilot,(),{'obsbot':{'reliability':.8}})]
    deterministic=[];psa_results={};psa_table=[];pairwise=[]
    for name,s,sunk,overrides in decisions:
        for key,values in compare(s,sunk=sunk,overrides=overrides).items():
            deterministic.append({'decision':name,'strategy':key,**values})
        r=compare_psa(s,n=n,seed=seed,sunk=sunk,overrides=overrides)
        r['without_proposed_obsbot']=summarise(r['draws'],eligible=KEYS[:-1])
        r['societal']=summarise(r['draws'],metric='societal_net_saving')
        psa_results[name]={k:v for k,v in r.items() if k not in {'inputs','draws'}}
        for key,v in r['summary'].items():psa_table.append({'decision':name,'effect':'attenuated','strategy':key,**v})
        for row in r['pairwise']:pairwise.append({'decision':name,**row})
        if name in {'pilot_new','state_new','pilot_retain_panda'}:
            np.savez_compressed(OUT/f'{name}_joint_draws.npz',
                **{f'{key}__{metric}':a for key,v in r['draws'].items() for metric,a in v.items()},
                **{f'input__{key}':a for key,a in r['inputs'].items()})
        print('PSA',name,r['preferred_expected_value'],flush=True)
    for portfolio,s in [('pilot',pilot),('state',state)]:
        for mode in ['published','null','skeptical']:
            r=compare_psa(s,n=n,seed=seed,effect_mode=mode);name=f'{portfolio}_{mode}'
            psa_results[name]={k:v for k,v in r.items() if k not in {'inputs','draws'}}
            for key,v in r['summary'].items():psa_table.append({'decision':name,'effect':mode,'strategy':key,**v})
    x=sample_inputs(p,n=n,seed=seed)
    relative=np.random.default_rng(seed+1).triangular(.65,.95,1,n)
    d=compare_inputs(pilot,p,x,overrides={'obsbot':{'reliability':x['reliability']*relative}})
    r=summarise(d);psa_results['pilot_prototype_reliability_uncertain']=r
    for key,v in r['summary'].items():psa_table.append({'decision':'pilot_prototype_reliability_uncertain','effect':'attenuated','strategy':key,**v})
    # Separate structural sensitivity: prototype cost and delivery uncertainty.
    # These are analyst priors, not new supplier or patient observations.
    kit_cost=np.random.default_rng(seed+2).triangular(2500,4500,10000,n)*x['equipment_cost']/10000
    for portfolio,s in [('pilot',pilot),('state',state)]:
        name=f'{portfolio}_prototype_cost_and_reliability_uncertain'
        d=compare_inputs(s,p,x,overrides={'obsbot':{'installed_cost':kit_cost,'reliability':x['reliability']*relative}})
        r=summarise(d);psa_results[name]=r
        for key,v in r['summary'].items():psa_table.append({'decision':name,'effect':'attenuated','strategy':key,**v})
    save_csv('deterministic_strategies.csv',deterministic);save_csv('psa_strategy_summary.csv',psa_table);save_csv('pairwise_psa.csv',pairwise)
    precision=[]
    for repeat_seed in [41,73,101]:
        for portfolio,s in [('pilot',pilot),('state',state)]:
            r=compare_psa(s,n=n,seed=repeat_seed)
            for key,v in r['summary'].items():precision.append({'portfolio':portfolio,'seed':repeat_seed,'n':n,'strategy':key,'mean':v['mean'],'p_optimal':v['p_optimal']})
    save_csv('psa_seed_precision.csv',precision)
    ow=[];tw=[]
    pairs=[('calls_per_site','odds_ratio'),('obsbot_installed_cost','obsbot_reliability'),
           ('mobile_capital_share','obsbot_reliability'),('life_years','marginal_fraction')]
    for portfolio,s in [('pilot',pilot),('state',state)]:
        ow.extend({'portfolio':portfolio,**row} for row in one_way(s,points=21))
        for a,b in pairs:
            for row in two_way(s,a,b,points=31):
                tw.append({'portfolio':portfolio,'x_parameter':a,'y_parameter':b,'x_value':row[a],'y_value':row[b],
                    **{k:row[k] for k in KEYS},'best':row['best'],'runner_up':row['runner_up'],
                    'margin':row['margin'],'design_kind':row['design_kind']})
    save_csv('one_way.csv',ow);save_csv('two_way.csv',tw)
    from scipy.stats import qmc,sobol_indices,uniform
    from sklearn.cluster import KMeans
    from sklearn.ensemble import ExtraTreesRegressor, HistGradientBoostingClassifier
    from sklearn.tree import DecisionTreeClassifier,export_text
    from sklearn.metrics import r2_score,mean_absolute_error,balanced_accuracy_score,confusion_matrix,silhouette_score,adjusted_rand_score
    from sklearn.decomposition import PCA
    u_train=qmc.Sobol(len(NAMES),scramble=True,seed=501).random_base2(13)
    u_select=qmc.Sobol(len(NAMES),scramble=True,seed=502).random_base2(11)
    u_test=qmc.Sobol(len(NAMES),scramble=True,seed=504).random_base2(12)
    train=from_unit(u_train);select=from_unit(u_select);test=from_unit(u_test)
    y_train=evaluate_design(pilot,train);y_select=evaluate_design(pilot,select);y_test=evaluate_design(pilot,test)
    labels_train=np.argmax(y_train,axis=1);labels_test=np.argmax(y_test,axis=1)
    # Unsupervised means outcome-blind: preprocessing/clustering fit on train inputs only.
    centre=u_train.mean(axis=0);scale=u_train.std(axis=0)
    ztrain=(u_train-centre)/scale;ztest=(u_test-centre)/scale
    km=KMeans(n_clusters=4,n_init=10,random_state=71).fit(ztrain);clusters=km.predict(ztest)
    silhouette=float(silhouette_score(ztest,clusters,sample_size=2000,random_state=72));aris=[]
    for cluster_seed in [79,83]:
        alt=KMeans(n_clusters=4,n_init=10,random_state=cluster_seed).fit(ztrain)
        aris.append(float(adjusted_rand_score(clusters,alt.predict(ztest))))
    pca=PCA(n_components=2).fit(ztrain);projection=pca.transform(ztest)
    save_csv('input_clusters_projection.csv',[{'pc1':float(projection[i,0]),'pc2':float(projection[i,1]),
        'input_cluster':int(clusters[i]),'exact_best':KEYS[int(labels_test[i])]} for i in range(len(test))])
    cr=[]
    for c in range(4):
        mask=clusters==c
        cr.append({'cluster':c,'n':int(mask.sum()),
          **{f'design_fraction_{key}':float(np.mean(labels_test[mask]==j)) for j,key in enumerate(KEYS)},
          **{f'mean_{name}':float(test[mask,j].mean()) for j,name in enumerate(NAMES)}})
    save_csv('input_cluster_summary.csv',cr)
    print('INPUT CLUSTER SILHOUETTE',silhouette,'ARI',aris,flush=True)
    print('FITTING REGRESSOR',time.monotonic()-start,flush=True)
    forest=ExtraTreesRegressor(n_estimators=192,min_samples_leaf=3,max_depth=24,n_jobs=2,random_state=81).fit(u_train,y_train)
    print('FITTING CLASSIFIER',time.monotonic()-start,flush=True)
    classifier=HistGradientBoostingClassifier(max_iter=250,max_leaf_nodes=15,l2_regularization=1,
        learning_rate=.08,random_state=102,early_stopping=True,validation_fraction=.15).fit(u_train,labels_train)
    def decision_scores(x):
        chosen=classifier.predict(x);scores=np.zeros((len(x),len(KEYS)))
        scores[np.arange(len(x)),chosen]=1
        return scores
    def importance(x,y,repeats,rng_seed):
        rng=np.random.default_rng(rng_seed);base=decision_quality(decision_scores(x),y)['mean_regret'];rows=[]
        for j,name in enumerate(NAMES):
            impacts=[]
            for _ in range(repeats):
                perm=x.copy();perm[:,j]=perm[rng.permutation(len(x)),j]
                impacts.append(decision_quality(decision_scores(perm),y)['mean_regret']-base)
            rows.append({'parameter':name,'increase_in_mean_regret':float(np.mean(impacts)),
                'sd_across_permutations':float(np.std(impacts,ddof=1)),'repeats':repeats,
                'scope':'predictive importance, not causal or EVPPI'})
        return sorted(rows,key=lambda r:r['increase_in_mean_regret'],reverse=True)
    print('SELECTION IMPORTANCE',time.monotonic()-start,flush=True)
    selected_importance=importance(u_select,y_select,4,84)
    axes=[row['parameter'] for row in selected_importance[:5]]
    save_csv('selection_importance.csv',selected_importance)
    grid5=k_way(pilot,axes,levels=5);save_csv('five_way_selected_grid.csv',grid5)
    grid4=k_way(pilot,['obsbot_installed_cost','obsbot_reliability','calls_per_site','odds_ratio'],levels=7)
    save_csv('four_way_equipment_grid.csv',grid4)
    print('HELDOUT IMPORTANCE',time.monotonic()-start,flush=True)
    save_csv('heldout_permutation_importance.csv',importance(u_test,y_test,6,85))
    pred=forest.predict(u_test);fm=decision_quality(pred,y_test)
    fm.update({'balanced_accuracy':float(balanced_accuracy_score(labels_test,np.argmax(pred,axis=1))),
        'r2_by_arm':dict(zip(KEYS,r2_score(y_test,pred,multioutput='raw_values').tolist())),
        'mae_by_arm':dict(zip(KEYS,mean_absolute_error(y_test,pred,multioutput='raw_values').tolist())),
        'confusion_matrix':confusion_matrix(labels_test,np.argmax(pred,axis=1),labels=np.arange(5)).tolist()})
    classified=decision_scores(u_test);cm=decision_quality(classified,y_test)
    cm['balanced_accuracy']=float(balanced_accuracy_score(labels_test,np.argmax(classified,axis=1)))
    cm['confusion_matrix']=confusion_matrix(labels_test,np.argmax(classified,axis=1),labels=np.arange(5)).tolist()
    tree=DecisionTreeClassifier(max_depth=5,min_samples_leaf=80,random_state=86).fit(train,labels_train)
    tree_choice=tree.predict(test);tree_pred=np.zeros_like(y_test);tree_pred[np.arange(len(y_test)),tree_choice]=1
    tm=decision_quality(tree_pred,y_test);tm['balanced_accuracy']=float(balanced_accuracy_score(labels_test,tree_choice))
    tm['confusion_matrix']=confusion_matrix(labels_test,tree_choice,labels=np.arange(5)).tolist()
    (OUT/'shallow_decision_rules.txt').write_text(export_text(tree,feature_names=[v.label for v in VARIABLES])+
        '\nClass mapping: '+str(dict(enumerate(KEYS)))+'\nSynthetic design explanation only; exact model remains authoritative.\n')
    save_csv('heldout_predictions.csv',[{'design_id':i,'exact_best':KEYS[int(labels_test[i])],
        'forest_choice':KEYS[int(np.argmax(pred[i]))],'classifier_choice':KEYS[int(np.argmax(classified[i]))],'tree_choice':KEYS[int(tree_choice[i])],
        'forest_regret':float(y_test[i].max()-y_test[i,np.argmax(pred[i])]),
        'tree_regret':float(y_test[i].max()-y_test[i,tree_choice[i]]),'classifier_regret':float(y_test[i].max()-y_test[i,np.argmax(classified[i])]),
        **{name:float(test[i,j]) for j,name in enumerate(NAMES)}} for i in range(len(test))])
    print('HELDOUT_CLASSIFIER',cm,'SELECTED',axes,flush=True)
    # Independent uniform design, explicitly NOT a Sobol decomposition of correlated PSA.
    def response(u):
        exact=evaluate_design(pilot,from_unit(u.T))
        return np.column_stack((exact[:,1:],exact[:,2]-exact[:,4],exact.max(axis=1))).T
    response_names=['mobile_net','panda_net','fixed_net','obsbot_net','panda_minus_obsbot','best_attainable_net']
    sr=[]
    for m,sd in [(11,91),(12,92)]:
        res=sobol_indices(func=response,n=2**m,dists=[uniform() for _ in NAMES],rng=np.random.default_rng(sd))
        for k,outcome in enumerate(response_names):
            for j,name in enumerate(NAMES):
                sr.append({'n_base':2**m,'seed':sd,'outcome':outcome,'parameter':name,
                    'first_order':float(res.first_order[k,j]),'total_order':float(res.total_order[k,j]),
                    'interaction_gap':float(res.total_order[k,j]-res.first_order[k,j]),
                    'scope':'Independent uniform design ranges; not PSA prior decomposition'})
    save_csv('sobol_indices.csv',sr)
    save_csv('global_heldout_design.csv',[{'design_id':i,**{name:float(test[i,j]) for j,name in enumerate(NAMES)},
        **{key:float(y_test[i,j]) for j,key in enumerate(KEYS)},'best':KEYS[int(labels_test[i])]} for i in range(len(test))])
    learning={'n_train':8192,'n_selection':2048,'n_independent_test':4096,'design_seeds':[501,502,504],'retired_diagnostic_holdout':503,
        'clustering':'Input-only train-fitted KMeans; all clusters retained; no clinical subgroup claim',
        'silhouette':silhouette,'seed_stability_ari':aris,'pca_variance_explained':pca.explained_variance_ratio_.tolist(),
        'forest':fm,'classifier':cm,'shallow_tree':tm,'selected_kway_axes':axes,'independent_design_samples':14336,
        'kway_points':len(grid5),'fourway_points':len(grid4),
        'interpretation':'Emulator agreement with this assumed exact model, not clinical validation'}
    old=json.loads((ROOT/'outputs/v4/results_v2.json').read_text());parity={}
    for portfolio,key in [('pilot','pilot_new'),('spokes','state_new')]:
        actual=psa_results[key]['summary']['panda'];previous=old['psa'][portfolio+'_attenuated']
        parity[portfolio]=all(np.isclose(actual[k],previous[k],rtol=1e-12,atol=1e-7) for k in ['mean','median','lower','upper'])
    if not all(parity.values()):raise AssertionError('Original Panda PSA changed')
    output={'version':'5.0.0-preliminary','date':'2026-10-28','protected_v4_result_parity':parity,
        'psa':psa_results,'learning':learning,'deterministic_count':len(deterministic),'one_way_rows':len(ow),
        'two_way_grid_points':len(tw),'psa_primary_structures':len(psa_results),'psa_iterations_each':n,
        'seed_precision_runs':6,'sobol_evaluations':(2048+4096)*(len(NAMES)+2),
        'scientific_runtime':{k:importlib.metadata.version(k) for k in ['numpy','scipy','scikit-learn']},
        'elapsed_seconds':time.monotonic()-start,
        'qualification':'Researcher-prior analysis; prototype unvalidated; deterministic design fractions are not probabilities'}
    (OUT/'results_v5.json').write_text(json.dumps(output,indent=2)+'\n')
    write_manifest(OUT)
    print('COMPLETED',output['elapsed_seconds'],flush=True)

if __name__=='__main__':main()
