"""Figures from exact v6 model outputs; one chart per figure, no fitted surrogate."""
from pathlib import Path
import csv,json,sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.pathways_v6 import hub_cost,PathwaySpec
OUT=ROOT/'outputs/v6';FIG=OUT/'figures';FIG.mkdir(exist_ok=True)
r=json.loads((OUT/'results_v6.json').read_text())
def read(name):
 with (OUT/name).open(newline='') as f:return list(csv.DictReader(f))
def save(fig,name):
 fig.text(.01,.015,'Conditional model; not observed savings. Source: v6 exact-model CSV outputs.',fontsize=8)
 fig.tight_layout(rect=[0,.05,1,1])
 for ext in ['png','svg']:fig.savefig(FIG/f'{name}.{ext}',dpi=180)
 plt.close(fig)
# Absolute patient pathways rather than only net avoided transfers.
a=r['deterministic']['pilot'];arms=['telephone','panda'];labels=['Telephone','Panda Vision']
fig,ax=plt.subplots(figsize=(9,5));bottom=np.zeros(2)
for name,label in [('immediate_transfers','Immediate transfer'),('delayed_rescues','Delayed rescue'),('final_local','Final local care')]:
 v=np.array([a[k][name] for k in arms]);ax.bar(labels,v,bottom=bottom,label=label)
 for j,x in enumerate(v):ax.text(j,bottom[j]+x/2,f'{x:.2f}',ha='center',va='center',fontsize=10)
 bottom+=v
ax.set_ylabel('Expected episodes per year');ax.set_title('Explicit pathways conserve all 37.5 pilot consultations');ax.legend(loc='upper left',bbox_to_anchor=(1.01,1));save(fig,'01_pathways')
fig,ax=plt.subplots(figsize=(9,5));calls=np.linspace(0,1800,601);h=hub_cost(calls,np.full_like(calls,15),PathwaySpec())
ax.plot(calls,h['economic']/1000,label='Resource value of incremental time');ax.step(calls,h['cash_capacity']/1000,where='post',label='Additional paid capacity, illustrative')
ax.set(xlabel='Annual video consultations',ylabel='Annual hub cost (AUD thousands)',title='Workload—not the number of sites—determines hub costs')
ax.legend();save(fig,'02_hub_workload')
for portfolio,title in [('pilot','Three-site pilot'),('spokes','Illustrative 33-site network')]:
 row=next(x for x in read('v5_v6_bridge.csv') if x['portfolio']==portfolio)
 values=[float(row[k])/1000 for k in ['v5_net_saving','after_hub_only_repair','v6_net_saving']]
 fig,ax=plt.subplots(figsize=(8,5));bars=ax.bar(['v5 historical','Hub trigger repaired','Explicit care pathways'],values)
 ax.bar_label(bars,fmt='%.1f');ax.axhline(0,linewidth=.8);ax.set(ylabel='Annual net resource saving (AUD thousands)',title=f'{title}: why the reference result changes')
 save(fig,'03_bridge_'+portfolio)
 for context in ['reference','prototype_uncertain']:
  ss=r['psa'][portfolio+'_'+context]['summary'];keys=list(ss);labels=['Telephone','Mobile unit','Panda Vision','Fixed PTZ','Tablet/OBSBOT*']
  means=np.array([ss[k]['mean'] for k in keys])/1000;low=np.array([ss[k]['lower'] for k in keys])/1000;high=np.array([ss[k]['upper'] for k in keys])/1000
  fig,ax=plt.subplots(figsize=(9,5));y=np.arange(5);ax.errorbar(means,y,xerr=[means-low,high-means],fmt='o',capsize=4)
  ax.set_yticks(y,labels);ax.invert_yaxis();ax.axvline(0,linestyle='--',linewidth=.8)
  ax.set(xlabel='Mean annual net resource saving and 95% model interval (AUD thousands)',title=f'{title}: '+('reference uncertainty' if context=='reference' else 'uncertain prototype cost and delivery'))
  fig.text(.18,.065,'*Complete unquoted configuration; not a clinical equivalence or procurement claim.',fontsize=8)
  save(fig,'04_psa_'+portfolio+'_'+context)
# Full two-way surface, independent of chart simplification.
rows=[x for x in read('two_way.csv') if x['portfolio']=='pilot' and x['grid']=='effect_local_burden']
xs=sorted({float(x['x_value']) for x in rows});ys=sorted({float(x['y_value']) for x in rows});z=np.empty((len(ys),len(xs)))
for q in rows:z[ys.index(float(q['y_value'])),xs.index(float(q['x_value']))]=float(q['panda_net'])/1000
fig,ax=plt.subplots(figsize=(9,5));im=ax.pcolormesh(xs,ys,z,shading='nearest');c=ax.contour(xs,ys,z,levels=[0]);ax.clabel(c,fmt='Break-even',fontsize=9)
fig.colorbar(im,ax=ax,label='Panda annual resource saving (AUD thousands)');ax.set(xlabel='Transfer odds ratio (lower implies fewer transfers)',ylabel='Local-care resource multiplier',title='Pilot result depends on both clinical effect and hospital-care assumptions');save(fig,'05_hospital_effect_surface')
rows=[x for x in read('budget.csv') if x['portfolio']=='pilot' and x['strategy']=='panda'];fig,ax=plt.subplots(figsize=(9,5))
for inc,label in [('False','Buy new Panda installations'),('True','Retain installed Panda; 2 years remaining')]:
 q=[x for x in rows if x['incumbent']==inc];ax.plot([int(x['year']) for x in q],[float(x['cash_expenditure'])/1000 for x in q],marker='o',label=label)
ax.set(xlabel='Budget year',ylabel='Cash expenditure (AUD thousands, constant prices)',title='Replacement remains a future cost even when initial capital is sunk');ax.legend();save(fig,'06_cash_replacement')
print(f'Created {len(list(FIG.glob("*.png")))} PNG/SVG figures from exact model outputs.')
