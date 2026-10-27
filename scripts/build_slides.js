const pptxgen = require('pptxgenjs');
const fs = require('fs');
const path = require('path');
const { warnIfSlideHasOverlaps, warnIfSlideElementsOutOfBounds } = require('/home/oai/skills/slides/pptxgenjs_helpers');

const data = JSON.parse(fs.readFileSync('outputs/model_results.json','utf8'));
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Cairns and Hinterland Hospital and Health Service';
pptx.subject = 'Panda Vision neonatal telehealth economic evaluation';
pptx.title = 'Panda Vision: model-based economic evaluation';
pptx.company = 'Cairns and Hinterland Hospital and Health Service';
pptx.lang = 'en-AU';
pptx.theme = { headFontFace: 'Arial', bodyFontFace: 'Arial', lang: 'en-AU' };
pptx.defineSlideMaster({
  title:'CHHHS_CONTENT',
  background:{color:'FFFFFF'},
  objects:[{image:{path:'assets/chhhs-content-background.png',x:0,y:0,w:13.333,h:7.5}}],
  slideNumber:{x:12.35,y:7.10,w:0.45,h:0.18,color:'777777',fontFace:'Arial',fontSize:8,align:'right'}
});
pptx.defineSlideMaster({
  title:'CHHHS_TITLE',
  background:{color:'2F8993'},
  objects:[{image:{path:'assets/chhhs-title-background.png',x:0,y:0,w:13.333,h:7.5}}]
});

const C={teal:'2F8993',dark:'15535C',cyan:'44B1BE',green:'70B16D',gold:'F7BA66',grey:'595958',pale:'DDEEF0',light:'F4F8F8',red:'B85450',white:'FFFFFF',black:'222222'};
const addTitle=(s,t,sub)=>{s.addText(t,{x:0.62,y:0.38,w:12.0,h:0.42,fontFace:'Arial',fontSize:27,bold:true,color:C.white,margin:0,fit:'shrink'}); if(sub)s.addText(sub,{x:0.64,y:0.88,w:11.8,h:0.25,fontFace:'Arial',fontSize:11,color:'E4F2F3',margin:0,fit:'shrink'});};
const addFooter=(s,txt)=>s.addText(txt,{x:0.65,y:7.05,w:11.3,h:0.17,fontFace:'Arial',fontSize:8,color:'707070',margin:0,fit:'shrink'});
const addSection=(s,txt,x,y,w)=>s.addText(txt,{x,y,w,h:0.28,fontFace:'Arial',fontSize:12,bold:true,color:C.dark,margin:0,fit:'shrink'});
const addMetric=(s,x,y,w,h,label,value,note,fill=C.light)=>{
  s.addText([{text:value,options:{bold:true,fontSize:25,color:C.dark,breakLine:true}},{text:label,options:{bold:true,fontSize:11,color:C.grey,breakLine:true}},{text:note||'',options:{fontSize:9,color:'666666'}}],{x,y,w,h,fill:{color:fill},line:{color:'D1E4E6',width:1},margin:0.14,breakLine:false,fit:'shrink'});
};
const addBullet=(s,text,x,y,w,h,level=0)=>s.addText(text,{x,y,w,h,fontFace:'Arial',fontSize:15,color:C.black,bullet:{indent:16+level*12},margin:0.02,breakLine:false,fit:'shrink'});

// 1 title
{
 const s=pptx.addSlide('CHHHS_TITLE');
 s.addText('Panda Vision',{x:0.72,y:2.10,w:6.4,h:0.68,fontFace:'Arial',fontSize:36,bold:true,color:C.white,margin:0,fit:'shrink'});
 s.addText('Model-based economic evaluation',{x:0.72,y:2.85,w:8.4,h:0.50,fontFace:'Arial',fontSize:25,color:C.white,margin:0,fit:'shrink'});
 s.addText('Existing rural neonatal telehealth pilot | Atherton, Mareeba and Innisfail',{x:0.72,y:3.55,w:9.4,h:0.34,fontFace:'Arial',fontSize:15,color:'E9F5F6',margin:0,fit:'shrink'});
 s.addText('Decision briefing | 27 October 2026',{x:0.72,y:5.45,w:5.4,h:0.26,fontFace:'Arial',fontSize:12,color:'E9F5F6',margin:0});
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 2 pilot boundary
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'The decision is whether video adds enough value to justify the system','Consultation occurs in both pathways; the model does not credit avoided specialist consultations.');
 addMetric(s,0.70,1.55,2.35,1.42,'current hospitals','3','Atherton · Mareeba · Innisfail',C.pale);
 addMetric(s,3.30,1.55,2.35,1.42,'consultations/site/year','10–15','30–45 across the network',C.light);
 addMetric(s,5.90,1.55,2.35,1.42,'Atherton episodes to date','4–5','local pilot experience',C.pale);
 addMetric(s,8.50,1.55,2.35,1.42,'installed cost/site','$10k','invoice/component verification required',C.light);
 addSection(s,'Benefit mechanisms',0.75,3.45,3.0);
 addBullet(s,'Avoid a transfer that is not clinically required',0.90,3.85,5.2,0.42);
 addBullet(s,'Improve procedures and stabilisation before a transfer',0.90,4.38,5.2,0.42);
 addBullet(s,'Improve assessment, clinician confidence and family communication',0.90,4.91,5.2,0.48);
 addSection(s,'What the model must not assume',6.65,3.45,3.5);
 addBullet(s,'That the 4–5 episodes establish effectiveness',6.80,3.85,5.5,0.42);
 addBullet(s,'That NWAU funding equals marginal cash saved',6.80,4.38,5.5,0.42);
 addBullet(s,'That every additional survivor reduces expenditure',6.80,4.91,5.5,0.42);
 addFooter(s,'Local facts: CHHHS ELC Operational paper, 21 October 2026; activity estimates confirmed after discussion with Dr Nicholas Cairns.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 3 model structure
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'One annual cohort, two consultation modes, several consequences','The decision tree keeps transfer, stabilisation and longer-term outcomes distinct.');
 // arrows first
 const arrows=[[2.75,2.42,1.05,0],[6.15,2.42,0.95,0],[9.35,2.42,0.85,0],[6.15,4.20,0.95,0],[9.35,4.20,0.85,0]];
 arrows.forEach(a=>s.addShape(pptx.ShapeType.line,{x:a[0],y:a[1],w:a[2],h:a[3],line:{color:C.teal,width:2,beginArrowType:'none',endArrowType:'triangle'}}));
 const node=(x,y,w,h,head,body,fill)=>s.addText([{text:head,options:{bold:true,fontSize:16,color:C.dark,breakLine:true}},{text:body,options:{fontSize:11,color:C.black}}],{x,y,w,h,fill:{color:fill},line:{color:'A7D0D4',width:1.2},margin:0.14,fit:'shrink',valign:'mid'});
 node(0.72,1.68,2.05,1.48,'Eligible episode','Neonate requires specialist advice after birth in a rural facility',C.light);
 node(3.80,1.68,2.35,1.48,'Telephone support','Usual specialist consultation and retrieval pathway',C.pale);
 node(7.10,1.68,2.25,1.48,'Transfer decision','Transfer / remain local',C.light);
 node(10.20,1.68,2.35,1.48,'Resource result','Transport, local care and receiving-hospital use',C.pale);
 node(3.80,3.46,2.35,1.48,'Video support','Same consultation plus specialist visual assessment and PTZ control',C.pale);
 node(7.10,3.46,2.25,1.48,'Clinical process','Earlier procedure, stabilisation, communication',C.light);
 node(10.20,3.46,2.35,1.48,'Outcome extension','Death; survival without / with major morbidity',C.pale);
 s.addText('Primary analysis',{x:6.95,y:5.45,w:1.55,h:0.26,fontSize:12,bold:true,color:C.dark,margin:0});
 s.addText('Cost-consequence + budget impact',{x:8.75,y:5.42,w:3.2,h:0.30,fontSize:13,color:C.black,margin:0});
 s.addText('Exploratory only',{x:6.95,y:5.90,w:1.55,h:0.26,fontSize:12,bold:true,color:C.dark,margin:0});
 s.addText('QALYs and lifetime costs, including survival with major morbidity',{x:8.75,y:5.84,w:3.45,h:0.55,fontSize:13,color:C.black,margin:0,fit:'shrink'});
 addFooter(s,'Primary comparison: video-supported consultation versus telephone-supported consultation. RCT not assumed feasible.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true,ignoreLines:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 4 retrieval and IHACPA
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'Retrieval cost is the largest economic lever—and the least certain local input','Current public QAS reporting gives RSQ volume, not a neonatal road/rotary/fixed-wing split.');
 s.addChart(pptx.ChartType.doughnut,[{name:'Mode share',labels:['Road','Rotary','Fixed wing'],values:[25,9,11]}],{x:0.75,y:1.45,w:4.35,h:3.45,showLegend:true,legendPos:'b',showTitle:false,showPercent:true,holeSize:55,chartColors:[C.teal,C.gold,C.green],showValue:false});
 addMetric(s,5.45,1.55,2.10,1.22,'road marginal cost','$4k','range $2k–$8k');
 addMetric(s,7.82,1.55,2.10,1.22,'rotary marginal cost','$25k','range $15k–$45k');
 addMetric(s,10.19,1.55,2.10,1.22,'fixed-wing marginal cost','$18k','range $10k–$30k');
 addMetric(s,5.45,3.08,2.10,1.22,'downstream difference','$4k','range $0–$12k');
 addMetric(s,7.82,3.08,2.10,1.22,'weighted transfer cost',`$${Math.round(data.weighted_transfer_cost/1000)}k`,'base-case estimate');
 addMetric(s,10.19,3.08,2.10,1.22,'NEP26','$7,418','per NWAU');
 s.addText('Use actual DRG/NWAU for consulted babies where available. NEP is a standardised resource benchmark—not an automatic cash saving. Rural block funding under the NEC must be described separately.',{x:5.45,y:4.72,w:6.85,h:1.20,fontSize:15,color:C.black,margin:0.02,fit:'shrink'});
 s.addText('Mode prior',{x:1.72,y:5.18,w:1.2,h:0.25,fontSize:11,bold:true,color:C.dark,align:'center',margin:0});
 s.addText('25 road · 9 rotary · 11 fixed-wing outbound legs',{x:0.82,y:5.53,w:4.1,h:0.52,fontSize:12,color:C.grey,align:'center',margin:0,fit:'shrink'});
 addFooter(s,'Sources: QAS performance data Apr–Jun 2026; NeoSTRESS Queensland neonatal retrieval study; IHACPA NEP Determination 2026–27.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 5 scenarios
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'The base model breaks even at about a 2 percentage-point absolute transfer reduction','All bars are conditional scenarios—not observed CHHHS results.');
 const labels=data.scenarios.map(d=>d.name), values=data.scenarios.map(d=>Math.round(d.net/1000));
 s.addChart(pptx.ChartType.bar,[{name:'Net saving ($000)',labels,values}],{x:0.78,y:1.40,w:7.25,h:4.85,catAxisLabelFontSize:12,valAxisLabelFontSize:11,valAxisTitle:'Annual net saving ($000)',showLegend:false,showTitle:false,chartColors:[C.teal],showValue:true,showCatName:false,showValAxisTitle:true,valAxisMinVal:-20,valAxisMaxVal:180,valGridLine:{color:'D8E3E4',width:1}});
 addMetric(s,8.45,1.55,3.55,1.18,'annual economic programme cost',`$${Math.round(data.programme.total_economic).toLocaleString()}`,'capital annualised over five years');
 addMetric(s,8.45,3.02,3.55,1.18,'annual cash continuation cost',`$${Math.round(data.programme.cash_continuation).toLocaleString()}`,'if installed capital is sunk');
 const be=data.programme.total_economic/(data.programme.consultations*data.weighted_transfer_cost);
 addMetric(s,8.45,4.49,3.55,1.18,'break-even absolute effect',`${(be*100).toFixed(1)} pp`,'about 0.76 avoided transfers/year');
 addFooter(s,'Base: 37.5 consultations/year; weighted marginal transfer + downstream cost ≈ $15.6k; equipment $10k/site.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 6 PSA
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'Probabilistic analysis suggests likely savings—but the interval includes material loss','20,000 simulations jointly vary activity, transfer effect, transport mix/cost and programme cost.');
 const hist=data.psa.histogram;
 s.addShape(pptx.ShapeType.rect,{x:0.72,y:1.38,w:7.65,h:4.95,fill:{color:'FFFFFF'},line:{color:'D7E6E8',width:1}});
 s.addChart(pptx.ChartType.line,[{name:'Simulations',labels:hist.map(d=>Math.round(d.midpoint/1000)),values:hist.map(d=>d.count)}],{x:0.84,y:1.52,w:7.35,h:4.55,catAxisLabelFontSize:9,valAxisLabelFontSize:10,showLegend:false,showTitle:false,chartColors:[C.teal],showValue:false,valGridLine:{color:'D8E3E4',width:1},catAxisTitle:'Annual health-system net saving ($000)',showCatAxisTitle:true,lineSize:3,showMarker:true,markerSize:4});
 const p=data.psa.summary.probability_cost_saving, med=data.psa.summary.median_net_saving, lo=data.psa.summary.net_saving_p025, hi=data.psa.summary.net_saving_p975;
 addMetric(s,8.72,1.50,3.20,1.18,'probability cost-saving',`${(p*100).toFixed(0)}%`,'conditional on model structure');
 addMetric(s,8.72,2.98,3.20,1.18,'median annual net',`$${Math.round(med/1000)}k`,'health-system perspective');
 addMetric(s,8.72,4.46,3.20,1.18,'95% interval',`−$${Math.round(Math.abs(lo)/1000)}k to $${Math.round(hi/1000)}k`,'effect distribution crosses zero');
 addFooter(s,'PSA is decision uncertainty, not a confidence interval around a local trial. Parameter distributions are editable in the workbook.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 7 equipment
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'A tablet-integrated build is feasible as an architecture—not yet a verified product','No exact off-the-shelf medically integrated tablet-mounted PTZ package was identified.');
 const cols=[0.72,3.78,6.84,9.90];
 const heads=['Current Panda Vision','Tablet + Tiny 2 Lite','Tablet + Tail Air','Commercial cart'];
 const vals=['$10k/site','~$4.5k concept','~$7.5k concept','$45k comparator'];
 const bodies=[
  '4K PTZ\nBuilt-in telehealth touchscreen\nPurpose-built Resuscitaire mount\nDocumented local compliance',
  'USB-C wired webcam\nTablet dock and powered hub\nFar-end control unverified\nLowest hardware cost',
  '4K motorised PTZ\nTablet app control\nWi-Fi/NDI, USB-C, PoE\nClosest current architecture',
  'Integrated clinical platform\nProduct-dependent PTZ\nBulky and costly\nNot neonatal-specific'
 ];
 for(let i=0;i<4;i++){
  s.addText([{text:heads[i],options:{bold:true,fontSize:16,color:C.dark,breakLine:true}},{text:vals[i],options:{bold:true,fontSize:21,color:i===0?C.teal:C.grey,breakLine:true}},{text:bodies[i],options:{fontSize:12,color:C.black}}],{x:cols[i],y:1.50,w:2.55,h:3.42,fill:{color:i%2===0?C.light:C.pale},line:{color:'B8D9DC',width:1},margin:0.16,fit:'shrink'});
 }
 s.addText('Prototype before procurement',{x:0.80,y:5.34,w:3.2,h:0.30,fontSize:17,bold:true,color:C.dark,margin:0});
 s.addText('Validate mounting, power, cleaning, QH Portal interoperability, far-end PTZ control, cyber/privacy, biomedical acceptance and clinician usability. OBSBOT Tail Air is a consumer/prosumer component, not a clinical approval.',{x:4.05,y:5.19,w:8.05,h:0.92,fontSize:14,color:C.black,margin:0.02,fit:'shrink'});
 addFooter(s,'Official OBSBOT specifications confirm Tail Air tablet control, 4K PTZ, Wi-Fi/NDI, USB-C and PoE. Installed concept costs are assumptions.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}
// 8 recommendation
{
 const s=pptx.addSlide('CHHHS_CONTENT'); addTitle(s,'Proceed with the evaluation now; use later data collection only to resolve decision uncertainty','The initial product is an investment model, not a prospective trial.');
 const y=[1.45,2.55,3.65,4.75];
 const n=['1','2','3','4'];
 const heads=['Validate local facts','Complete the model','Review with decision-makers','Decide whether more evidence is worth collecting'];
 const bodies=[
  'Invoices/components; 4–5 Atherton episode review; actual mode and destination; DRG/NWAU; local staff time.',
  'Three perspectives; 1/3/5-year budget impact; deterministic scenarios; 20,000-draw PSA; clinical extension kept separate.',
  'CHHHS, Townsville neonatology/ANTS-NQ, RSQ/QAS, virtual care, finance, BTS/eHealth and consumer/First Peoples partners.',
  'Use EVPI/EVPPI/EVSI only after the investment decision and influential uncertainties are clear.'
 ];
 for(let i=0;i<4;i++){
  s.addText(n[i],{x:0.80,y:y[i],w:0.55,h:0.55,fontSize:22,bold:true,color:C.white,fill:{color:C.teal},shape:pptx.ShapeType.ellipse,align:'center',valign:'mid',margin:0});
  s.addText(heads[i],{x:1.65,y:y[i]-0.02,w:3.85,h:0.34,fontSize:17,bold:true,color:C.dark,margin:0,fit:'shrink'});
  s.addText(bodies[i],{x:5.95,y:y[i]-0.05,w:6.15,h:0.72,fontSize:13,color:C.black,margin:0.02,fit:'shrink'});
 }
 s.addText('Recommended decision',{x:0.80,y:6.10,w:2.4,h:0.28,fontSize:12,bold:true,color:C.dark,margin:0});
 s.addText('Continue the pilot, complete the model-based evaluation, and prototype a tablet-integrated replacement without assuming equivalence or approval.',{x:3.20,y:6.02,w:8.90,h:0.55,fontSize:16,bold:true,color:C.black,margin:0.02,fit:'shrink'});
 addFooter(s,'Artifacts: editable economic model, CHHHS briefing note, CHHHS decision presentation and source-controlled Conductor track.');
 warnIfSlideHasOverlaps(s,pptx,{muteContainment:true}); warnIfSlideElementsOutOfBounds(s,pptx);
}

// final inspection pass
for (const s of pptx._slides) { warnIfSlideHasOverlaps(s,pptx,{muteContainment:true,ignoreLines:true}); warnIfSlideElementsOutOfBounds(s,pptx); }
pptx.writeFile({ fileName:'outputs/Panda_Vision_economic_evaluation_CHHHS.pptx' });
