"""Plot current exact-model tables, never historical artifacts or fitted surrogates."""
from pathlib import Path
import csv
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
ROOT=Path(__file__).resolve().parents[1]


def main(output=None):
    output=Path(output or ROOT/'outputs/v12');figures=output/'figures';figures.mkdir(exist_ok=True)
    def read(name):
        with (output/name).open(newline='') as stream:return list(csv.DictReader(stream))
    def save(fig,name):
        fig.tight_layout();fig.savefig(figures/(name+'.png'),dpi=170);fig.savefig(figures/(name+'.svg'));plt.close(fig)
    rows=[r for r in read('psa_perspectives.csv') if r['scenario']=='reference' and r['strategy']=='panda' and r['perspective']=='health_system']
    labels={'pilot':'Pilot (3)','chhhs':'CHHHS (10)','chhhs_tchhs':'CHHHS + TCHHS (14)','spokes':'Illustrative state (33)'}
    means=[float(r['mean']) for r in rows];lower=[float(r['lower']) for r in rows];upper=[float(r['upper']) for r in rows]
    fig,ax=plt.subplots(figsize=(10,4.8));ax.errorbar(means,range(len(rows)),xerr=[[m-l for m,l in zip(means,lower)],[u-m for m,u in zip(means,upper)]],fmt='o',capsize=5)
    ax.set_yticks(range(len(rows)),[labels[r['portfolio']] for r in rows]);ax.axvline(0,linestyle='--',linewidth=1);ax.xaxis.set_major_formatter(FuncFormatter(lambda v,p:f'${v/1000:,.0f}k'))
    ax.set_xlabel('Annual net resource saving (AUD): mean and 95% prior interval');ax.set_title('Panda Vision versus telephone — conditional, not observed savings');save(fig,'resource_intervals')
    budget=read('mixed_estate_budget.csv');fig,ax=plt.subplots(figsize=(10,4.8))
    for keep,label in [('True','Retain 3; purchase 7'),('False','Purchase all 10')]:
        rs=[r for r in budget if r['portfolio']=='chhhs' and r['strategy']=='panda' and r['retain_known_estate']==keep]
        ax.plot([int(r['year']) for r in rs],[float(r['capital']) for r in rs],marker='o',label=label)
    ax.set_xticks(range(1,8));ax.set_ylim(bottom=0);ax.yaxis.set_major_formatter(FuncFormatter(lambda v,p:f'${v/1000:,.0f}k'));ax.set_xlabel('Budget year');ax.set_ylabel('Capital purchases (AUD; constant prices)');ax.set_title('CHHHS mixed estate: ownership and replacement made explicit');ax.legend();save(fig,'mixed_estate_capital')
    rows=[r for r in read('utility_bridge_scenarios.csv') if float(r['utility_difference'])==.13 and int(r['duration_years_assumed'])==1 and float(r['fraction_consultations_improved_assumed'])==.001]
    fig,ax=plt.subplots(figsize=(10,4.8));ax.bar([f"{float(r['discount_rate']):.0%}" for r in rows],[float(r['qalys_per_1000_consultations']) for r in rows]);ax.set_ylim(bottom=0);ax.set_xlabel('Discount rate');ax.set_ylabel('Illustrative QALYs per 1,000 consultations');ax.set_title('One year of assumed utility gain begins at age 11, not birth');fig.text(.5,.01,'0.13 utility contrast; 1 improved infant per 1,000 consultations. Not a video-effect estimate.',ha='center',fontsize=9);save(fig,'utility_correction')
    print('Created three current PNG/SVG figures from CSV tables.')

if __name__=='__main__':main()
