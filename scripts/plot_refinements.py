"""Plot inspectable refinement CSVs; no colours or clinical rankings are imposed."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main(output: Path) -> None:
    """Produce three separate figures with explicit scenario and cost qualifications."""
    output = Path(output)
    figures = output/'figures'
    figures.mkdir(parents=True, exist_ok=True)
    def rows(name):
        with (output/name).open(encoding='utf-8', newline='') as stream:
            return list(csv.DictReader(stream))
    psa = rows('policy_psa.csv')
    def save(fig, name, note):
        fig.text(.02, .015, note, fontsize=9, wrap=True)
        fig.tight_layout(rect=(0,.075,1,1))
        for suffix in ('png','svg'):
            fig.savefig(figures/f'{name}.{suffix}', dpi=180)
        plt.close(fig)
    fig, ax = plt.subplots(figsize=(9,5))
    for basis, label in [('contacts','Forecast fixed as contacts'),('episodes','Forecast fixed as episodes')]:
        data = [r for r in psa if r['portfolio']=='chhhs' and r['effect_mode']=='attenuated'
                and r['perspective']=='health_system' and r['policy']=='retain_pilot_expand_obsbot'
                and r['activity_basis']==basis]
        data.sort(key=lambda r:float(r['contacts_per_episode']))
        ax.plot([float(r['contacts_per_episode']) for r in data], [float(r['mean']) for r in data], marker='o',label=label)
    ax.axhline(0,linewidth=.7,linestyle=':')
    ax.set(title='CHHHS: interpretation of repeat contacts', xlabel='Assumed contacts per clinical episode',
           ylabel='Expected annual net resource saving (AUD)')
    ax.legend()
    save(fig,'contact_denominator','Conditional Panda retention + kit expansion; researcher priors, not observed savings. No per-contact efficacy gain.')
    data = [r for r in psa if r['portfolio']=='chhhs_tchhs' and r['activity_id']=='contacts_1'
            and r['effect_mode']=='attenuated' and r['perspective']=='health_system']
    labels={'telephone':'Telephone everywhere','retain_pilot_only':'Retain three pilot systems',
        'retain_pilot_expand_panda':'Retain + new Panda (conditional)', 'retain_pilot_expand_obsbot':'Retain + new kit (conditional)',
        'retain_pilot_expand_mobile':'Retain + mobile (conditional)', 'retain_pilot_expand_fixed':'Retain + fixed (conditional)'}
    data.sort(key=lambda r:float(r['mean']))
    fig, ax = plt.subplots(figsize=(10,5.5))
    means=[float(r['mean']) for r in data]
    ax.barh([labels[r['policy']] for r in data],means)
    ax.axvline(0,linewidth=.7,linestyle=':')
    ax.set(title='CHHHS + TCHHS: conditional deployment costs',xlabel='Expected annual net resource saving (AUD)')
    save(fig,'regional_policy_costs','Equal video effects/reliability assumed; cost ranking is not clinical suitability or procurement approval. PSA intervals are in CSV.')
    budget=rows('policy_budget.csv')
    fig,ax=plt.subplots(figsize=(9,5))
    for policy in ('retain_pilot_only','retain_pilot_expand_panda','retain_pilot_expand_obsbot'):
        data=[r for r in budget if r['portfolio']=='chhhs' and r['activity_id']=='contacts_1' and r['policy']==policy]
        data.sort(key=lambda r:int(r['year']))
        ax.plot([int(r['year']) for r in data],[float(r['capital']) for r in data],marker='o',label=labels[policy])
    ax.set(title='CHHHS: purchases and replacements',xlabel='Budget year',ylabel='Equipment cash expenditure (constant AUD)')
    ax.legend()
    save(fig,'estate_purchases','Two remaining years for three pilot installations and five-year replacement life are explicit assumptions; excludes running costs.')
    metadata=json.loads((output/'results.json').read_text())
    text='# Neocam: episode/contact and mixed-deployment refinements\n\n'
    text+='This is a conditional decision-model supplement, not observed clinical or financial outcomes. The exact model uses existing evidence and disclosed analyst scenarios; it is not fitted to the Atherton pilot cases.\n\n'
    text+='## Expected annual health-system resource result\n\n'
    text+='Default one-contact-per-episode scenario, attenuated clinical-effect structure, retaining the three known pilot installations. Expansion options are hypothetical site-suitability scenarios. Equal video effects and reliability are assumed across configurations.\n\n'
    text+='| Network | Policy | Expected net resource saving (AUD/year) | 95% researcher-prior interval | Probability of resource saving |\n|---|---|---:|---|---:|\n'
    for row in psa:
        if row['activity_id']=='contacts_1' and row['effect_mode']=='attenuated' and row['perspective']=='health_system' and row['policy']!='telephone':
            text+=f"| {row['portfolio']} | {labels[row['policy']]} | {float(row['mean']):,.0f} | {float(row['lower']):,.0f} to {float(row['upper']):,.0f} | {float(row['probability_resource_saving']):.1%} |\n"
    text+='\nNet saving is against telephone. Negative values mean added resources, not proof of poor clinical value. The family extension is bounded; arbitrary policy-specific provider/Commonwealth/state allocations are not inferred. The six-perspective primary reference is retained separately.\n\n'
    text+='## Repeat-contact interpretation\n\nFor a fixed forecast of contacts, repeated contacts reduce distinct clinical episodes; for a fixed forecast of episodes, repeated contacts increase workload. The ratio is not observed locally. Repeated contacts do not independently amplify clinical success or video reliability. An episode is not necessarily a unique infant across separate illnesses.\n\n'
    text+='![Contact-denominator comparison](figures/contact_denominator.png)\n\n'
    text+='## Decision sets and equipment\n\nTelephone everywhere and retention at the three reported pilot sites form the reported-operation set. Reported operation is not regulatory certification. New Panda, kit, mobile and fixed installations are conditional alternatives requiring site-specific capability and governance checks. Duplicate assignment policies are removed before probability-best calculations.\n\n'
    text+='![Conditional policy comparison](figures/regional_policy_costs.png)\n\n'
    text+='Hub workload is summed across technologies before applying shared paid-capacity blocks. Purchase and replacement schedules use the same owned estate as the economic calculation. Retention does not make future replacement free.\n\n![Equipment purchases](figures/estate_purchases.png)\n\n'
    text+='## Validation and evidence\n\n'
    text+=f"{metadata['counts']['paired_policy_scenarios']} paired policy/scenario evaluations each use {metadata['draws']:,} draws; the maximum cohort residual is {metadata['max_cohort_residual']:.3g}. These are overlapping model comparisons, not independent clinical studies. All external reviewer records are pending. Automatic arithmetic checks cannot certify clinical appropriateness; additional appropriate transfers may be beneficial.\n\n"
    text+='Input and calculation-source identity: `resolved_inputs.json`. Eligibility and assignments: `eligibility.csv`, `policy_assignments.csv`. PSA and exact rankings: `policy_psa.csv`, `policy_rankings.csv`. Absolute prior-predictive outputs: `policy_predictive.csv`. Seven-year cash schedules: `policy_budget.csv`. Review requests: `review_packet.json`. Original literature, estimates, rights and gaps remain in the repository evidence/source registers; this supplement adds no empirical effect or price claim.\n'
    (output/'refinements_report.md').write_text(text,encoding='utf-8')
    print('Created three refinement figures and the results-linked Markdown supplement.')


if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'outputs/v13-refinements')
    main(parser.parse_args().output)
