"""Reproducible publication figures; each plot is a separate figure with no seaborn."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter,PercentFormatter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.strategies import KEYS
from src.sensitivity import VARIABLES
OUT=ROOT/'outputs/v5';FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
R=json.loads((OUT/'results_v5.json').read_text())
LABELS=['Telephone','Mobile unit','Panda Vision','Ceiling/wall PTZ','Tablet + OBSBOT']
SHORT=['Telephone','Mobile','Panda','Fixed PTZ','OBSBOT kit']
LABEL=dict(zip(KEYS,LABELS));V={v.name:v.label for v in VARIABLES}
records=[]
def rows(name):
 with (OUT/name).open(newline='') as f:return list(csv.DictReader(f))
def base(title,xlabel=None,ylabel=None,height=5.3):
 fig,ax=plt.subplots(figsize=(9.4,height));ax.set_title(title,loc='left',pad=14,fontsize=14)
 if xlabel:ax.set_xlabel(xlabel)
 if ylabel:ax.set_ylabel(ylabel)
 ax.spines[['top','right']].set_visible(False)
 return fig,ax
def save(fig,name,caption):
 fig.text(.02,.018,caption,fontsize=8,va='bottom',wrap=True)
 fig.tight_layout(rect=(0,.07,1,1))
 for ext in ['png','svg']:fig.savefig(FIG/f'{name}.{ext}',dpi=180,bbox_inches='tight')
 plt.close(fig);records.append({'figure':name,'caption':caption})
fmt=FuncFormatter(lambda value,_:f'{value/1000:,.0f}k')
# Exact reference costs, not observations.
d={x['strategy']:x for x in rows('deterministic_strategies.csv') if x['decision']=='pilot_new'}
f,a=base('Five options: deterministic new-investment comparison','Annual net resource saving (AUD)','Configuration')
vals=np.array([float(d[k]['net_saving']) for k in KEYS]);a.barh(LABELS,vals);a.invert_yaxis();a.axvline(0,linestyle='--');a.xaxis.set_major_formatter(fmt)
save(f,'01_deterministic','Three-site pilot; equal video effects/reliability assumed. Complete OBSBOT kit cost is unquoted. Not cash savings.')
s=R['psa']['pilot_new']['summary'];m=np.array([s[k]['mean'] for k in KEYS]);lo=np.array([s[k]['lower'] for k in KEYS]);hi=np.array([s[k]['upper'] for k in KEYS])
f,a=base('Joint uncertainty is wide for every video option','Annual net resource saving (AUD)','Configuration')
a.errorbar(m,np.arange(5),xerr=np.vstack((m-lo,hi-m)),fmt='o',capsize=4);a.set_yticks(range(5),LABELS);a.invert_yaxis();a.axvline(0,linestyle='--');a.xaxis.set_major_formatter(fmt)
save(f,'02_paired_psa','20,000 paired draws; points = means, bars = 95% model uncertainty intervals. These are not observed clinical confidence intervals.')
f,a=base('Which option is cost-optimal depends on the investment decision','Conditional probability cost-optimal','',height=5.7)
contexts=['pilot_new','pilot_retain_panda','pilot_prototype_cost_and_reliability_uncertain'];labels=['New equipment: equal video performance','Retain installed Panda Vision','New equipment: uncertain prototype cost + delivery']
y=np.arange(3);left=np.zeros(3)
for k in KEYS:
 values=np.array([R['psa'][c]['summary'][k]['p_optimal'] for c in contexts]);a.barh(y,values,left=left,label=LABEL[k]);left+=values
 for j,v in enumerate(values):
  if v>.07:a.text(left[j]-v/2,j,f'{v:.0%}',ha='center',va='center',fontsize=10)
a.set_yticks(y,labels);a.set_xlim(0,1);a.invert_yaxis();a.xaxis.set_major_formatter(PercentFormatter(1));a.legend(ncol=3,loc='upper center',bbox_to_anchor=(.5,-.16),frameon=False)
save(f,'03_decision_contexts','All five arms considered; prototype may be infeasible until technical approval. Cost-optimal is not clinically best.')
# One-way extrema around reference, exact output.
ow=[x for x in rows('one_way.csv') if x['portfolio']=='pilot' and x['strategy']=='obsbot'];ext=[]
for name in V:
 values=[float(x['net_saving']) for x in ow if x['parameter']==name];ext.append((name,min(values),max(values)))
ext.sort(key=lambda x:x[2]-x[1]);f,a=base('One-way sensitivity: tablet/OBSBOT versus telephone','Annual net resource saving (AUD)','',height=6.6)
for i,(name,l,h) in enumerate(ext):a.plot([l,h],[i,i],linewidth=6)
a.set_yticks(range(len(ext)),[V[x[0]] for x in ext]);a.axvline(float(d['obsbot']['net_saving']),linestyle=':');a.axvline(0,linestyle='--');a.xaxis.set_major_formatter(fmt)
save(f,'04_one_way','21 exact values per parameter, others fixed at reference. Interval = deterministic range, not a probability interval.')
tw=rows('two_way.csv')
def surface(portfolio,x,y,name,title):
 rr=[r for r in tw if r['portfolio']==portfolio and r['x_parameter']==x and r['y_parameter']==y]
 xs=sorted({float(r['x_value']) for r in rr});ys=sorted({float(r['y_value']) for r in rr});z=np.empty((len(ys),len(xs)))
 for r in rr:z[ys.index(float(r['y_value'])),xs.index(float(r['x_value']))]=KEYS.index(r['best'])
 f,a=base(title,V[x],V[y],height=5.7)
 image=a.pcolormesh(xs,ys,z,shading='nearest',vmin=-.5,vmax=4.5)
 cb=f.colorbar(image,ax=a,ticks=range(5));cb.ax.set_yticklabels(SHORT)
 save(f,name,'31 × 31 exact grid; remaining inputs fixed. Colours denote cost-optimal configurations, not clinical outcomes or probabilities.')
surface('pilot','calls_per_site','odds_ratio','05_surface_activity_effect','Pilot: utilisation and clinical-effect assumptions')
surface('pilot','obsbot_installed_cost','obsbot_reliability','06_surface_kit_delivery','Pilot: prototype complete cost and usable connection')
surface('pilot','mobile_capital_share','obsbot_reliability','07_surface_shared_cart','Pilot: a shared mobile unit changes attribution')
surface('pilot','life_years','marginal_fraction','08_surface_life_marginal','Pilot: equipment life and avoidable retrieval resources')
surface('state','obsbot_installed_cost','obsbot_reliability','09_surface_state','33-site scenario: prototype cost and delivery')
grid=rows('five_way_selected_grid.csv');counts=[sum(r['best']==k for r in grid) for k in KEYS]
f,a=base('All five options can be preferred within joint assumptions','Number of exact five-way design points','Configuration')
a.barh(LABELS,counts);a.invert_yaxis()
for i,v in enumerate(counts):a.text(v+20,i,str(v),va='center')
a.set_xlim(0,max(counts)*1.15)
save(f,'10_five_way','3,125 equally spaced design points in five selected dimensions. Counts depend on the design and ARE NOT probability-best estimates.')
sob=[r for r in rows('sobol_indices.csv') if r['n_base']=='4096' and r['outcome']=='best_attainable_net']
assert sob, 'Missing best-attainable Sobol results'
sob.sort(key=lambda r:float(r['total_order']));f,a=base('Global variance: best attainable annual net saving','Estimated variance-sensitivity index','',height=6.6)
y=np.arange(len(sob));a.barh(y-.16,[float(r['first_order']) for r in sob],height=.3,label='First order');a.barh(y+.16,[float(r['total_order']) for r in sob],height=.3,label='Total order');a.set_yticks(y,[V[r['parameter']] for r in sob]);a.legend(frameon=False)
save(f,'11_sobol','Independent uniform 12-dimensional design; not decomposition of the correlated PSA prior. Monte Carlo estimates can stray below zero.')
cl=rows('input_clusters_projection.csv');f,a=base('Input-only clustering did not reveal stable natural groups','Input principal component 1','Input principal component 2')
for c in range(4):
 rr=[r for r in cl if int(r['input_cluster'])==c];a.scatter([float(r['pc1']) for r in rr],[float(r['pc2']) for r in rr],s=5,alpha=.35,label=f'Design cluster {c+1}')
a.legend(frameon=False,markerscale=2)
save(f,'12_clusters','Held-out design projection; first two components explain 16.7%. Silhouette 0.052 and weak seed agreement: not patient subgroups.')
imp=rows('heldout_permutation_importance.csv');imp.reverse();f,a=base('Which inputs change the learned decision most?','Increase in mean exact-model regret after permutation (AUD/year)','',height=6.6)
a.barh([V[r['parameter']] for r in imp],[float(r['increase_in_mean_regret']) for r in imp],xerr=[float(r['sd_across_permutations']) for r in imp],capsize=2)
save(f,'13_decision_importance','Independent holdout, six permutations. Bars are predictive importance; whiskers show permutation SD, not causal effects or EVPPI.')
l=R['learning'];f,a=base('Cost-prediction accuracy alone was insufficient for decisions','Mean exact-model decision regret (AUD/pilot-year)','Explanatory model')
models=['forest','shallow_tree','classifier'];names=['Cost regression forest','Shallow rule tree','Decision-focused classifier'];a.barh(names,[l[k]['mean_regret'] for k in models]);a.invert_yaxis()
save(f,'14_surrogate_regret','4,096 fresh held-out model evaluations. Even the selected classifier has worst-case regret of $8,970: exact model remains authoritative.')
f,a=base('Decision-focused classifier: independent holdout agreement','Predicted cost-optimal configuration','Exact-model cost-optimal configuration',height=6)
conf=np.array(l['classifier']['confusion_matrix']);im=a.imshow(conf);a.set_xticks(range(5),SHORT,rotation=25,ha='right');a.set_yticks(range(5),SHORT)
for i in range(5):
 for j in range(5):a.text(j,i,str(conf[i,j]),ha='center',va='center',bbox={'alpha':.8,'pad':1})
f.colorbar(im,ax=a,label='Held-out design points')
save(f,'15_classifier_confusion','95.0% accuracy; 93.3% balanced accuracy. This validates agreement with synthetic model decisions, not real-world clinical effectiveness.')
(FIG/'figure_register.json').write_text(json.dumps(records,indent=2)+'\n')
print(f'Created {len(records)} separate figures in PNG and SVG.')
