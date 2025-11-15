Comparing AI‑Agents for Planning Innovative Lesson Plans

Short version: This repository evaluates lesson‑plan generators built with Large Language Models (LLMs) using a unified, research‑grounded rubric (ULPR). We provide the rubric, mappings to evidence, and an LLM‑assisted evaluator that turns lesson text into strand‑wise band scores (0–4) and an overall 0–100.

⸻

Abstract

High‑quality lesson planning is costly in time and expertise, and recent AI agents can draft plans in seconds. Yet most generated plans lack the explicit signals needed for systematic evaluation—clear outcome–activity–assessment alignment, observable engagement levels (ICAP), formative use of evidence, durable learning checks via retrieval and spacing, and cognitive‑load–aware design.

We operationalize research‑based pedagogy into a Unified Lesson Plan Rubric (ULPR) and provide an AI‑assisted evaluation pipeline that extracts rubric evidence from lesson‑plan text and maps it to banded scores. The rubric integrates Constructive Alignment (CA), ICAP, Formative Assessment, Test‑Enhanced Learning, Cognitive Load Theory (CLT), and Direct Instruction (DI)/Rosenshine’s principles. We also outline architectural choices for embedding pedagogy into AI agents and discuss next steps for coverage and human calibration.

In a case study, we identified 7 AI agents/chatbots with lesson‑plan generation features and evaluated them using rubric‑aligned metrics (see references in refs.bib). Code, sample inputs, and generated reports live in this repo.

⸻

Contents
	•	Acronyms
	•	Contributions
	•	ULPR rubric at a glance
	•	ULPR metric system and index codes
	•	Evidence base and implementation mapping
	•	Evaluation pipeline
	•	Experiment: sample result
	•	Diagnosis & improvement pointers
	•	Repository layout (suggested)
	•	Getting started
	•	Citing
	•	References

⸻

Acronyms
	•	RAG — Retrieval‑Augmented Generation
	•	KG — Knowledge Graph
	•	AI — Artificial Intelligence
	•	LLM — Large Language Model
	•	ULPR — Unified Lesson Plan Rubric
	•	ICAP — Individual Career and Academic Plan (kept as‑is to match source text)
	•	CA — Constructive Alignment
	•	RP — Retrieval Practice
	•	DI — Direct Instruction
	•	CL — Cognitive Load
	•	SMARTIE — Specific & Strategic; Measurable; Actionable; Rigorous, Realistic & Results‑Focused; Timed; Inclusive; Equity‑Oriented
	•	UDL — Universal Design for Learning

Note: In the pedagogy literature, ICAP often denotes Interactive–Constructive–Active–Passive. The term is left unchanged here to reflect the provided manuscript text and code variables.

⸻

Contributions
	1.	A research‑grounded rubric unifying six strands.
	2.	An LLM‑assisted evaluator that extracts signals and maps them to 0–4 bands.
	3.	A case study illustrating a diagnostic 0/100 outcome and how to act on it.
	4.	Discussion of architectural choices for embedding pedagogy into AI agents.

⸻

ULPR rubric at a glance

The ULPR aggregates six strands with band descriptors (0–4) and strand caps summing to 100 points.

Strand (source)	Max
A. Outcomes & Alignment (Biggs, 1996)	25
B. ICAP Engagement (Chi & Wylie, 2014)	20
C. Formative Assessment (Black & Wiliam, 1998)	15
D. Retrieval Practice (Roediger & Karpicke, 2006)	15
E. Cognitive Load / Examples (Sweller et al., 2019)	15
F. Direct Instruction Moves (Rosenshine, 2012)	10
Total	100


⸻

ULPR metric system and index codes

This section enumerates the concrete indices used by the evaluator (the entries of ULPR_CRITERIA) and links them to their evidentiary sources and scoring weights. Letter prefixes broadly correspond to strands; some codes span or predate the final labels.

Scoring: Each index is banded 0–4 with evidence; points are computed as weight × (band ÷ 4). Strand totals and the overall score follow the caps above.

Code	Name	Wt	Operational intent (abridged)
A. Outcomes & Alignment			
A1	SMARTIE Outcomes	8	Measurable outcomes with success criteria to enable alignment.
A2	Alignment: TLAs ↔ Outcomes ↔ Assessment	9	1:1 mapping at the same cognitive level; criteria‑referenced.
A3	Structure, Timing & Flow	8	Small steps; modeled → guided → independent; realistic time boxes.
B. ICAP Engagement			
B1	ICAP Engagement Mix	6	≥50% time in Constructive+Interactive; thresholds for band 3/4.
B2	Generative Tasks	6	Prompts that elicit explain/justify/compare/predict (Constructive).
B3	Whole‑class Participation/Interactivity	8	All‑student response; structured groupwork; roles and timed turns.
C. Formative Assessment & Retrieval			
C1	Retrieval Density & Effort	6	Count distinct retrievals; reward high‑effort formats (free recall).
C2	Formative Checks & Action	7	Use evidence now to reteach/regroup; actionable feedback.
C3	Spacing & Cumulative Coverage	7	Delayed checks (~2‑day/1‑week); cumulative items.
D. Examples, Scaffolds, Practice			
D1	Models / Worked Examples	6	Provide models, exemplars, and worked steps.
D2	Scaffolds & Fading	5	Scaffold then fade support over time.
D3	Independent Practice	4	Require independent practice with accountability.
E. Cognitive Load (CLT)			
E1	Intrinsic Load Sequencing	3	Simple → complex; isolate‑then‑integrate; goal‑free early tasks.
E2	Extraneous Load & Modality	5	Integrate sources; signaling; redundancy & split‑attention control.
E3	Expertise Adaptation & Load Monitoring	4	Probe prior knowledge; effort/load checks; planned adjustments.
F. UDL & Accessibility			
F1	UDL & Accessibility	5	Multiple means (rep., action, engagement); accessible resources.

Guardrails & dependencies
	•	CLT guardrail: if E3 < 2, any E1 or E2 band of 4 is demoted to 3.
	•	Alignment caps: if A2 ≤ 1 then B2 and C2 ≤ 2; if A1 ≤ 1 then A2 ≤ 2. These enforce theoretical dependencies without rewriting plan content.

⸻

Evidence base and implementation mapping

This section provides brief provenance notes for each source and specifies the indices through which recommendations are operationalized. Full citations are in refs.bib.

Paper 1 — Rosenshine (2012): Principles of Instruction

Core ideas: Daily review; small steps; frequent checks; models/worked examples; guided practice; high success rate; scaffold & fade; independent practice; frequent retrieval; weekly/monthly reviews (I‑do/We‑do/You‑do).
Indices: A3 (8), D1 (6), D2 (5), D3 (4); C1 (6), C3 (7). Higher bands require explicit timings, examples, and artifacts.

Paper 2 — Freeman et al. (2014): Active learning in STEM

Core ideas: Meta‑analysis of 225 studies: active learning improves exams (~½ letter grade) and reduces failure (~55%).
Indices: B1 (6) time‑share thresholds for Constructive+Interactive; B3 (8) all‑student routines & structured groupwork; B2 (6) generative prompts. Lecture‑only designs score poorly even with strong content.

Paper 3 — Roediger & Karpicke (2006): Test‑enhanced learning

Core ideas: Retrieval practice strengthens retention beyond restudy; effects are larger with effortful retrieval and meaningful delays.
Indices: C1 (6) retrieval density/effort; C3 (7) spacing & cumulative coverage; C2 (7) formative use of results now (reteach/regroup).

Paper 4 — Biggs (1996): Constructive Alignment

Core ideas: Align intended outcomes, TLAs, and assessment at the same level (SOLO framing); design TLAs to elicit targeted performances; prefer authentic assessment and criteria‑referenced grading.
Indices: A2 (9) alignment centerpiece; A1 (8) SMARTIE outcomes; Caps in code: if A2 ≤ 1 then B2, C2 ≤ 2; if A1 ≤ 1 then A2 ≤ 2.

Paper 5 — Chi & Wylie (2014): ICAP framework

Core ideas: Passive, Active, Constructive, Interactive with predicted learning gains I > C > A > P; operational coding of behaviors and design implications.
Indices: B1 (6) time in C+I; B2 (6) generative tasks; B3 (8) interactivity with roles, joint products, timed turns, and monitoring cues.

Paper 6 — Black & Wiliam (1998): Formative assessment

Core ideas: Clarify intentions/success criteria; engineer evidence of learning via whole‑class participation; feedback that moves learners forward; activate peers and self‑regulation.
Indices: C2 (7) formative checks and actionable feedback with in‑lesson time to use it; B3 (8) all‑student response routines; A1/A2 ensure intentions/success criteria are visible for formative use.

Paper 7 — Practical session‑planning checklist

Contents: Aims; SMARTIE outcomes; content/sequence/timings; teacher vs. student activities; ABC learning types; strategies; open‑ended questioning; resources; aligned assessment & reflection; UDL principles.
Indices: A1 (8) and A3 (8) mirror front matter; B1–B3 reflect activity variety & questioning; C‑row enforces aligned assessment & reflection; F1 (5) lifts UDL items into bands and evidence notes.

Paper 8 — Sweller et al. (2019): Cognitive load, 20 years later

Core ideas: Working‑memory limits; intrinsic/extraneous/germane load; worked example, split‑attention, modality, redundancy, expertise reversal, element interactivity; implications for measuring/managing load.
Indices: E1 (3) intrinsic sequencing; E2 (5) extraneous load & modality; E3 (4) expertise adaptation & monitoring. Guardrail: if E3 < 2, E1/E2 top bands are reduced (expertise‑reversal logic).

⸻

Evaluation pipeline

The evaluator parses lesson artifacts, extracts signals, and maps them to bands per strand. Signals include: measurable outcome verbs & success criteria (A); activity verbs indicating ICAP level (B); learning intentions, checks‑for‑understanding, and feedback routines (C); retrieval episodes (D); scaffolds like worked examples and fading (E); and lesson flow with review → guided → independent (F).

Command

python lesson_plan_evaluator.py \
  --lesson "lessons/lesson_plan(GPT-5).txt" \
  --backend ollama --model llama3.1 \
  --md-out "reports_md/report(GPT-5).md" \
  --json-out "reports_json/report(GPT-5).json"

Filenames with underscores should be displayed safely in code or using pathlike notation in prose (e.g., lesson_plan_evaluator.py).

Outputs
	•	Markdown report with strand‑wise evidence and banding (in reports_md/)
	•	JSON report with machine‑readable bands & points (in reports_json/)

⸻

Experiment: sample result

We ran the evaluator on lessons/lesson_plan(GPT-5).txt. The tool produced strand‑wise bands and a total score.

Strand	Band (0–4)	Score / Max
A. Outcomes & Alignment	0	0 / 25
B. ICAP Engagement	0	0 / 20
C. Formative Assessment	0	0 / 15
D. Retrieval Practice	0	0 / 15
E. Cognitive Load / Examples	0	0 / 15
F. Direct Instruction Moves	0	0 / 10
Total	—	0 / 100

This diagnostic example is intentionally minimal and highlights how the rubric pinpoints missing evidence.

⸻

Diagnosis & improvement pointers
	•	A (Outcomes & Alignment): Add measurable outcomes and an explicit alignment map (outcomes ↔ TLAs ↔ assessment).
	•	B (ICAP Engagement): Replace passive exposure with generative/interactive tasks.
	•	C (Formative): State intentions/success criteria and plan evidence and feedback within the lesson.
	•	D (Retrieval): Insert spaced, effortful retrieval (e.g., brain‑dumps, short‑answer).
	•	E (CLT): Manage load; include worked examples with fading; segment complexity.
	•	F (DI/Rosenshine): Use review, small steps, guided practice, checks, and independent practice.

⸻

Repository layout (suggested)

.
├── lessons/
│   └── lesson_plan(GPT-5).txt
├── reports_md/
│   └── report(GPT-5).md
├── reports_json/
│   └── report(GPT-5).json
├── lesson_plan_evaluator.py
├── ULPR/
│   └── criteria.py                # ULPR_CRITERIA and weights/bands (example)
├── refs.bib                       # Bibliography (see References)
└── README.md

Folder names reflect the manuscript; adjust as needed to match your actual structure.

⸻

Getting started
	1.	Clone this repository.
	2.	(Optional) Create a virtual environment.
	3.	Install dependencies (e.g., pip install -r requirements.txt if present).
	4.	Run the evaluator using the command shown above, pointing --lesson to your lesson text.

Notes
	•	The --backend/--model flags in the example use ollama and llama3.1; adapt to your environment.
	•	Ensure lesson inputs are plain‑text files with clear sectioning so evidence can be detected reliably.

⸻

Citing

If you use ULPR or the evaluator in academic work, please cite this repository and the original sources in refs.bib.

@misc{ulpr_lesson_plans_2025,
  title        = {Comparing AI-Agents for Planning Innovative Lesson Plans: A Unified Lesson Plan Rubric and LLM-Assisted Evaluator},
  author       = {Anonymous},
  year         = {2025},
  howpublished = {GitHub repository},
  note         = {ULPR rubric and evaluator. See refs.bib for sources}
}


⸻

References

This README summarizes content derived from sources listed in refs.bib, including but not limited to:
	•	Biggs (1996) — Constructive Alignment
	•	Black & Wiliam (1998) — Inside the Black Box
	•	Roediger & Karpicke (2006) — Test‑Enhanced Learning
	•	Rosenshine (2012) — Principles of Instruction
	•	Freeman et al. (2014) — Active Learning in STEM
	•	Chi & Wylie (2014) — ICAP framework
	•	Sweller et al. (2019) — Cognitive Load Theory
	•	Practical session‑planning checklists and institutional guidance

Additional references include the lesson‑plan generator tools surveyed (e.g., EduAide, Khanmigo, Radius, Slidesgo AI, etc.). Keep tool names and links in refs.bib for traceability.

⸻

License

See LICENSE in this repository (choose a license appropriate for your project if not present).

⸻

This README is adapted from the accompanying LaTeX manuscript for repository use. It preserves the rubric, indices, and evaluation details while removing LaTeX‑specific formatting.
