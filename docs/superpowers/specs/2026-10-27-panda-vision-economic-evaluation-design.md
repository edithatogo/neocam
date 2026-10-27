# Panda Vision economic evaluation design

## Intent
Build a decision-useful, model-based economic evaluation of the existing three-site Panda Vision pilot for CHHHS, Queensland and national investment decisions. The evaluation must use existing information and current estimates, not wait for prospective data.

## Goals
- Compare video-supported neonatal consultation with telephone-supported consultation; consultation occurs in both arms.
- Represent two main benefit mechanisms: avoided transfer and improved care before or during transfer.
- Include an exploratory survival-with-major-morbidity pathway rather than assuming every survival gain is cost-saving.
- Estimate organisational, health-system and societal consequences.
- Test all material assumptions through scenarios and probabilistic sensitivity analysis.
- Produce one source-controlled model, CHHHS briefing note and CHHHS presentation.

## Non-goals
- Claim local causal effectiveness from 4-5 Atherton episodes.
- Treat NWAU revenue as a marginal cash saving.
- Claim a current Queensland neonatal transport-mode split where public reporting does not provide one.
- Build a discrete-event simulation or import large HEOR frameworks.

## Constraints and rulings
- Current Panda Vision installation: $10,000 per site, flagged for invoice verification.
- Existing sites: Atherton, Mareeba and Innisfail.
- Activity: 10-15 video consultations per site per year; midpoint 12.5.
- Public QAS reporting establishes RSQ workload but does not disaggregate current neonatal road/rotary/fixed-wing transport.
- Base transport mix uses a Queensland neonatal retrieval study (25 road, 9 rotary, 11 fixed-wing outbound legs) with broad alternative mixes.
- The tablet option is a replacement for the current ad hoc setup. No exact off-the-shelf medically integrated tablet-mounted PTZ package has been verified; OBSBOT Tail Air is the closest current architecture but requires BTS/eHealth/QH Portal validation.

## Approaches considered
1. Simple break-even spreadsheet: transparent but misses correlated uncertainty and clinical pathways.
2. Decision tree plus scenario and PSA: selected; proportionate, publishable and easy to validate.
3. DES/ABM using careops-sim: rejected for v1 because event-level operational queues are not the principal decision uncertainty.

## Model architecture
Annual cohort decision tree, with 30-45 consultations across three sites. Usual-care transfer probability and video effect are uncertain. Transfer cost is a weighted combination of road, rotary and fixed-wing asset costs plus the incremental receiving-hospital resource difference. Programme costs include annualised equipment, readiness checks, support and incremental video workflow time. Clinical consequences are reported separately; an optional net-monetary-benefit extension includes death, survival without major morbidity and survival with major morbidity.

## Outputs
- Editable Excel workbook with input provenance, deterministic scenarios, PSA, IHACPA benchmarks, equipment options, clinical extension and evidence register.
- CHHHS briefing note on the supplied template.
- CHHHS PowerPoint using supplied visual assets and palette.
- Conductor context, track status and Git history.
