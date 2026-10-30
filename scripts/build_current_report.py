"""Portable, data-driven current reports; no ChatGPT-host helper paths."""
from __future__ import annotations
import argparse
import csv
import html
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[1]
LABELS={'pilot':'Pilot: 3 sites','chhhs':'CHHHS: 10 locations','chhhs_tchhs':'CHHHS + TCHHS: 14','spokes':'Illustrative Queensland: 33'}


def read_rows(output: Path, name: str) -> list[dict]:
    with (output/name).open(encoding='utf-8',newline='') as stream:
        return list(csv.DictReader(stream))


def money(value: str | float) -> str:
    value=float(value)
    return ('-$' if value<0 else '$')+f'{abs(value):,.0f}'


def build(output: Path, *, office: bool=False) -> None:
    """Use current CSV/JSON for every exported figure, table and narrative number."""
    inputs=json.loads((output/'resolved_inputs.json').read_text())
    metadata=json.loads((output/'results.json').read_text())
    rows=[r for r in read_rows(output,'psa_perspectives.csv') if r['scenario']=='reference' and r['strategy']=='panda' and r['perspective']=='health_system']
    budgets=[r for r in read_rows(output,'mixed_estate_budget.csv') if r['strategy']=='panda' and r['retain_known_estate']=='True' and r['year']=='1']
    utility=next(r for r in read_rows(output,'utility_bridge_scenarios.csv') if float(r['utility_difference'])==.13 and int(r['duration_years_assumed'])==1 and float(r['discount_rate'])==.05 and float(r['fraction_consultations_improved_assumed'])==.001)
    lines=['# Neocam: current decision-model release v12','',
      'Existing evidence and explicit assumptions; no new patient data, local effect fitting or independent clinical validation.',
      '', '## Annual Panda Vision resource results versus telephone', '',
      '| Network | Mean net saving | 95% researcher-prior interval | P(resource saving) |',
      '|---|---:|---|---:|']
    for r in rows:
        lines.append(f"| {LABELS[r['portfolio']]} | {money(r['mean'])} | {money(r['lower'])} to {money(r['upper'])} | {float(r['probability_positive']):.1%} |")
    lines+=['','## Mixed equipment estate','',
      'The same ownership record informs economic retention and cash purchases. Only Atherton, Mareeba and Innisfail are recorded as existing Panda installations. Two remaining years is a scenario assumption, not an observed service-life measurement.',
      '', '| Network | New installations in year 1 | Year-1 capital |','|---|---:|---:|']
    for r in budgets:lines.append(f"| {LABELS[r['portfolio']]} | {r['new_installations']} | {money(r['capital'])} |")
    lines+=['','## Corrected secondary utility scenario','',
      f"With the stated illustrative 0.13 contrast, one improved infant per 1,000 consultations, one year of benefit beginning at age 11 and 5% discounting, the result is **{float(utility['qalys_per_1000_consultations']):.6f} QALYs per 1,000 consultations**. This is not a video-effect estimate and is not included in the reference cost results.",
      '', '## Investment and publication plan','',
      'Compare telephone, mobile teleconference, Panda Vision, ceiling/wall PTZ and a complete tablet/OBSBOT configuration. Keep new purchases, retention and shared infrastructure distinct. The prototype is not an approved clinical installation.',
      '', 'Use the explicit immediate-transfer, delayed-rescue and final-local-care paths; do not equate fewer transfers with better care. Report whole-system resource costs, bounded societal/family effects, CHHHS exposure and conditional state/Commonwealth allocations without counting transfers twice.',
      '', 'Run declared configuration through the exact model, retain shared uncertainty across sites and alternatives, and report null/sceptical effects, clinical plausibility and prior-predictive consequences alongside expected savings. Repeat-contact workload and mixed deployment policies remain specified follow-on analyses, not fitted local estimates.',
      '', 'Before submission: complete four critical full texts, independent neonatal/retrieval and economic review, current local funding/price verification, and permissions for corporate or licensed source materials. Simulated roles are author review only.',
      '', '## Reproducibility and boundaries','',
      f"Configuration SHA-256: `{inputs['configuration_sha256']}`. {metadata['counts']['paired_psa_structures']} paired structures × {metadata['draws']:,} draws. Generated reports and their input hashes are bound by release_manifest.json.",
      '', 'Historical v7 Office artifacts are retained as historical, not the current release. The current memo, report, presentation, CSV tables and figures are generated together here. There is no newly certified recalculating Excel workbook.',
      '', 'Source model: src/pathways_v6.py and regional/perspective adapters. Provenance: sources/registry.csv (where supplied), evidence registers, and resolved_inputs.json. IHACPA episode prices are prototypes, not patient-level DRG grouping or marginal cash tariffs. QEP/local QWAU and clinical effects remain uncertain.',
      '', 'Software acceptance is separate from these numerical outputs. Missing lock, unavailable tools, Gitleaks, hosted CI, complete source migration and independent review remain unresolved until actually verified.', '']
    (output/'current_report.md').write_text('\n'.join(lines),encoding='utf-8')
    table='<table><tr><th>Network</th><th>Mean annual net saving</th><th>95% prior interval</th><th>P(saving)</th></tr>'
    for r in rows:
        table+='<tr>'+''.join('<td>'+html.escape(x)+'</td>' for x in [LABELS[r['portfolio']],money(r['mean']),money(r['lower'])+' to '+money(r['upper']),f"{float(r['probability_positive']):.1%}"])+'</tr>'
    table+='</table>'
    figures=''.join(f'<figure><img src="figures/{name}.svg" alt="{title}"><figcaption>{title}</figcaption></figure>' for name,title in [('resource_intervals','Conditional annual resource results; prior uncertainty, not observed savings'),('mixed_estate_capital','Same ownership assumptions used in economic and budget accounts'),('utility_correction','Age-11 scenario, not an estimated clinical effect')])
    (output/'current_report.html').write_text('<!doctype html><meta charset="utf-8"><title>Neocam current release</title><style>body{font:16px Arial;max-width:1000px;margin:40px auto;padding:20px}td,th{padding:12px;text-align:left;border-bottom:1px solid #bbb}img{width:100%;max-width:900px}pre{white-space:pre-wrap}</style><h1>Neocam: current model release</h1><p>Conditional economic analysis. Not independent clinical validation.</p>'+table+figures+'<pre>'+html.escape('\n'.join(lines[8:]))+'</pre>',encoding='utf-8')
    if office:
        build_office(output,rows,budgets,inputs)


def build_office(output,rows,budgets,inputs):
    """Optional reporting group; corporate assets remain private and repository-relative."""
    from docx import Document
    from docx.shared import Pt, Inches
    from pptx import Presentation
    from pptx.util import Inches as PInches, Pt as PPt
    from pptx.dml.color import RGBColor
    doc=Document(ROOT/'assets/Briefing_note.docx')
    regional=next((r for r in budgets if r['portfolio']=='chhhs'),None)
    estate_note=(f"Year-1 CHHHS new purchases: {regional['new_installations']} installations, {money(regional['capital'])}. " if regional else '')
    estate_note+=f"Configured Panda benchmark: {money(inputs['parameters']['equipment_cost'])} per installation; verify invoices."
    doc.paragraphs[0].text='30 October 2026 | Evaluation plan v12 | Discussion draft'
    doc.paragraphs[1].text='Neocam: consistent investment decisions from existing evidence'
    doc.tables[0].cell(1,0).text='Estimate the value of neonatal video support compared with telephone consultation using existing evidence and transparent assumptions. Align decisions, actual model inputs, equipment ownership, budget schedules and current reporting. No new recruitment or structured elicitation is required for this preliminary evaluation.'
    doc.tables[1].cell(0,1).text='Prepared for Dr Dylan Mordaunt, Chief Medical Officer'
    doc.tables[1].cell(1,1).text='Neonatal, retrieval, virtual-care and finance partners'
    doc.tables[2].cell(1,0).text=(
      '1. Decisions. Compare telephone, mobile teleconference, Panda Vision, ceiling/wall PTZ and a complete tablet/OBSBOT kit. Separate new investment, retention and shared infrastructure. The kit is a conceptual comparator, not approved clinical equipment.\n\n'
      '2. Populations. Use pilot (3 sites), CHHHS hospital/emergency network (10), CHHHS + TCHHS (14) and illustrative Queensland (33). Historical births and missingness remain explicit; these are not certified deployment inventories.\n\n'
      '3. Model. Retain immediate transfer, delayed rescue and final local care; failed video falls back to telephone. Consultation exists in both arms. Keep incremental specialist time, paid capacity and hospital resource prototypes separate.\n\n'
      '4. Configuration and ownership. One validated configuration supplies the executed parameters and pathway assumptions. One ownership table feeds retained capital and replacement budgets. '+estate_note+' Remaining life is a budget assumption.\n\n'
      '5. Perspectives and uncertainty. Reconcile health-system, bounded societal, provider, patient/family and conditional state/Commonwealth views. Report paired probabilistic structures, clinical plausibility, null/sceptical effects, and value of perspective. Funding and subsidies do not create social resources.\n\n'
      '6. Health outcomes. Do not infer mortality or QALY gains from transport changes. The illustrative utility scenarios begin at the source age of 11 and are not included in primary results. Additional survival with morbidity is not excluded.\n\n'
      '7. Evidence and decisions. Replace assumptions when ordinary invoices or routine records are available; complete critical full texts and independent clinical/economic review before publication. Assess safe care and equity alongside cost, not transfer reduction alone.')
    for i,text in [(1,'Include family travel/time and disclose omitted caregiver, education, disability-service and environmental consequences.'),(2,'Simulated review is author self-review. Obtain independent clinical/economic review before claiming validation.'),(3,'Use current records where available; uncertain effect estimates remain explicit, not locally fitted.')]:doc.tables[3].cell(i,1).text=text
    concerns=['Annual cash purchases, opportunity costs and funding allocations are separate. No expenditure approval is implied.',
      'Incremental hub workload depends on video time, not an arbitrary count of sites. Repeated contacts per infant remain an open workload assumption.',
      'Current outputs are regenerated and hash-bound. Historical tables and slides are not silently presented as the current analysis.',
      'No patient-level records added. Corporate templates/source excerpts must remain private pending redistribution permission.',
      'A passing ordinary test suite is not full assurance. Lock, Gitleaks, requested tools and hosted CI require actual execution.',
      'Rural access, clinical appropriateness and disability-inclusive consequences remain relevant even where the service is not cost-saving.']
    for i,text in enumerate(concerns,1):doc.tables[4].cell(i,1).text=text
    doc.tables[5].cell(1,0).text='Our care: appropriate neonatal support. Our people: explicit workload and usable systems. Equity: remote access. Sustainability: coherent investment and perspective accounting.'
    doc.tables[6].cell(1,0).text='Current CSV tables, plots, report and presentation share one resolved-input snapshot and release manifest. Source registers remain incomplete where originals/full texts were unavailable. This is not a validated cost-utility or procurement recommendation.'
    for table in list(doc.tables)[7:]:table._element.getparent().remove(table._element)
    for node in doc._element.xpath('.//w:t'):
        if node.text and '<select document type>' in node.text:node.text='MEMORANDUM'
        elif node.text and 'Choose an item' in node.text:node.text=''
    for table in doc.tables:
        for row in table.rows:
            row.height=None
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.space_after=Pt(3);para.paragraph_format.line_spacing=1
                    for run in para.runs:run.font.name='Arial';run.font.size=Pt(9)
    for p in doc.paragraphs:
        for run in p.runs:run.font.name='Arial';run.font.size=Pt(9)
    for run in doc.paragraphs[1].runs:run.font.size=Pt(15);run.bold=True
    doc.save(output/'Neocam_current_plan.docx')
    # A minimal portable deck uses the supplied template theme and background assets.
    deck=Presentation(ROOT/'assets/chhhs-powerpoint-template.pptx')
    for sid in list(deck.slides._sldIdLst):
        deck.part.drop_rel(sid.rId);deck.slides._sldIdLst.remove(sid)
    def slide(title,body=None,image=None):
        s=deck.slides.add_slide(deck.slide_layouts[6])
        s.shapes.add_picture(str(ROOT/'assets/chhhs-content-background.png'),0,0,width=deck.slide_width,height=deck.slide_height)
        box=s.shapes.add_textbox(PInches(.55),PInches(.32),deck.slide_width-PInches(1.1),PInches(.8))
        p=box.text_frame.paragraphs[0];p.text=title;p.font.size=PPt(25);p.font.bold=True;p.font.color.rgb=RGBColor.from_string('15535C')
        if image:s.shapes.add_picture(str(image),PInches(1.1),PInches(1.35),width=deck.slide_width-PInches(2.2),height=deck.slide_height-PInches(2.05))
        if body:
            box=s.shapes.add_textbox(PInches(.8),PInches(1.5),deck.slide_width-PInches(1.6),deck.slide_height-PInches(2.2))
            box.text_frame.word_wrap=True
            for i,text in enumerate(body):
                p=box.text_frame.paragraphs[0] if i==0 else box.text_frame.add_paragraph();p.text=text;p.font.size=PPt(20);p.space_after=PPt(16)
    slide('Neocam | decision-model consistency release',[
      'Existing evidence; five configurations; four regional portfolios.',
      'Declared inputs now reach the calculations. One equipment estate aligns retention and cash budgets.',
      'Current outputs are regenerated together. Uncertain clinical effects and incomplete validation remain explicit.'])
    slide('Conditional annual resource results',image=output/'figures/resource_intervals.png')
    slide('One estate, coherent purchases and replacements',image=output/'figures/mixed_estate_capital.png')
    slide('Corrected secondary health scenario',image=output/'figures/utility_correction.png')
    slide('Interpret the results at the right level',[
      'Health-system resource value is not the same as CHHHS cash savings or Commonwealth/state funding.',
      'Video may improve care without reducing transfers. No causal survival or QALY benefit is credited in the reference analysis.',
      'Prototype equivalence, local eligibility, marginal retrieval costs and funding responses remain assumptions.'])
    slide('Work to finish before publication',[
      'Complete original-source and critical full-text verification; independent clinical/economic review.',
      'Resolve the real environment lock; execute required security and quality tools, including Gitleaks.',
      'Finish private repository/history transfer and reproduce from a fresh clone. No public release is authorised.'])
    deck.save(output/'Neocam_current_presentation.pptx')
    executable=shutil.which('soffice')
    if executable:
        with tempfile.TemporaryDirectory(prefix='neocam-office-') as temp:
            command=[executable,'-env:UserInstallation='+Path(temp).as_uri(),'--headless','--convert-to','pdf','--outdir',str(output),str(output/'Neocam_current_plan.docx')]
            subprocess.run(command,check=True,capture_output=True,text=True,timeout=90)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'outputs/v12');p.add_argument('--office',action='store_true')
    a=p.parse_args();build(a.output.resolve(),office=a.office)
