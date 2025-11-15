# Comparing AI-Agents for Lesson-Plan Generation

*# A repo-friendly summary with bullets, commands, and quick links.*

**Quick links**
- [What this repo does](#what-this-repo-does)
- [Why it matters](#why-it-matters)
- [Features](#features)
- [Acronyms (quick)](#acronyms-quick)
- [ULPR at a glance (weights → 100)](#ulpr-at-a-glance-weights--100)
- [Scoring](#scoring)
- [Guardrails / Dependencies](#guardrails--dependencies)
- [Indices (short list)](#indices-short-list)
- [Quick start](#quick-start)
- [Evidence base (high-level)](#evidence-base-high-level)

---

## What this repo does
- Evaluates lesson-plan generators (AI agents/LLMs) using a unified rubric (**ULPR**).
- Extracts evidence from lesson text and maps it to **0–4 bands per strand**.
- Outputs reports (**Markdown + JSON**) with strand scores and an overall **0–100**.
- Documents how pedagogy maps to indices used by the evaluator.

## Why it matters
- Most auto-generated lesson plans lack evaluable signals (alignment, **ICAP** engagement, formative use of evidence, retrieval & spacing, **CLT**-aware design).
- **ULPR** gives a research-grounded, replicable way to compare agents/architectures.

## Features
- ✅ **Unified Lesson Plan Rubric (ULPR)** with six strands and weights  
- ✅ **Evidence extraction → banding (0–4) → points (0–100)**  
- ✅ **Markdown and JSON** reports  
- ✅ **Guardrails** (e.g., expertise reversal for CLT) and **dependency caps** (alignment → engagement/formative)

## Acronyms (quick)
- **AI**: Artificial Intelligence  
- **LLM**: Large Language Model  
- **ULPR**: Unified Lesson Plan Rubric  
- **CA**: Constructive Alignment  
- **ICAP**: Interactive–Constructive–Active–Passive (name kept to match manuscript/code)  
- **RP**: Retrieval Practice  
- **DI**: Direct Instruction  
- **CL**: Cognitive Load  
- **SMARTIE**: Specific & Strategic; Measurable; Actionable; Rigorous/Realistic/Results-Focused; Timed; Inclusive; Equity-Oriented  
- **UDL**: Universal Design for Learning

---

## ULPR at a glance (weights → 100)
- **A. Outcomes & Alignment — 25**
- **B. ICAP Engagement — 20**
- **C. Formative Assessment — 15**
- **D. Retrieval Practice — 15**
- **E. Cognitive Load / Examples — 15**
- **F. DI Moves — 10**

## Scoring
- Each index is banded **0–4** with evidence → **points = weight × (band / 4)**.

## Guardrails / Dependencies
- **CLT guardrail:** if `E3 < 2`, any `E1/E2 = 4` → **demote to 3**.  
- **Alignment caps:**  
  - if `A2 ≤ 1` → `B2, C2 ≤ 2`  
  - if `A1 ≤ 1` → `A2 ≤ 2`

---

## Indices (short list)
- **A (Outcomes & Alignment):** A1 SMARTIE outcomes; A2 outcomes↔TLAs↔assessment mapping; A3 structure/timing/flow.  
- **B (ICAP):** B1 time in Constructive+Interactive; B2 generative tasks; B3 all-student routines / structured groupwork.  
- **C (Formative & Retrieval):** C1 retrieval density/effort; C2 formative checks & action; C3 spacing & cumulative coverage.  
- **D (Examples/Scaffolds/Practice):** D1 worked examples; D2 scaffolds & fading; D3 independent practice.  
- **E (Cognitive Load):** E1 intrinsic-load sequencing; E2 extraneous load & modality; E3 expertise adaptation & monitoring.  
- **F (UDL & Accessibility):** F1 multiple means + accessible resources.

---

## Quick start
- Clone this repo.
- *(Optional)* Create a virtualenv and install deps (e.g., `pip install -r requirements.txt`).
- Run the evaluator on a lesson text file:

```bash
python lesson_plan_evaluator.py \
  --lesson "lessons/lesson_plan(GPT-5).txt" \
  --backend ollama --model llama3.1 \
  --md-out "reports_md/report(GPT-5).md" \
  --json-out "reports_json/report(GPT-5).json"
