# Panda Vision Economic Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a reproducible decision model, PSA, CHHHS memo and CHHHS presentation for Panda Vision.

**Architecture:** A Python annual-cohort decision model supplies reviewed outputs to an artifact_tool workbook and two template-based executive artifacts. All assumptions are classified and source-linked.

**Tech Stack:** Python, NumPy, artifact_tool, python-docx, PptxGenJS, Git, Conductor.

**Spec:** `docs/superpowers/specs/2026-10-27-panda-vision-economic-evaluation-design.md`

## Global Constraints
- Consultation occurs in both arms.
- 3 sites; 10-15 consultations per site-year.
- $10,000 per installation remains verification-required.
- PSA must allow no benefit and possible increased transfer.
- NWAU is a resource benchmark, not automatic cash saving.

## Review Focus
- Transfer-effect distribution crossing the null.
- Transport shares summing to one.
- Annualised versus sunk capital treatment.
- Survival-with-morbidity costs not omitted.
- No claim that the tablet architecture is clinically or ICT approved.

---

### Task 1: Decision model and tests
Create `src/panda_model.py` and `tests/test_model.py`; test deterministic costs, transfer probability transformation, transport mix, scenario outputs and PSA reproducibility.

### Task 2: Workbook
Create `scripts/build_workbook.py` and export `outputs/Panda_Vision_economic_model_v1.xlsx` with inputs, formulas, scenarios, PSA, IHACPA, equipment, clinical extension and sources.

### Task 3: CHHHS briefing note
Create `scripts/build_memo.py`, populate the supplied template and render/verify the document.

### Task 4: CHHHS presentation
Create `scripts/build_slides.js`, use supplied CHHHS backgrounds, native charts and overlap/out-of-bounds checks, then render/verify the deck.

### Task 5: Verification and conductor status
Run tests, scan workbook formula errors, render documents and slides, update track status and package the source-controlled project.
