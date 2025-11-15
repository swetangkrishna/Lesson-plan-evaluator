#!/usr/bin/env python3
"""
Unified Lesson Plan Evaluator (ULPR)
====================================

Combines and de-duplicates 8 research-grounded rubrics into a single
100-point scoring system, then uses an LLM (open-source friendly) to
rate a lesson plan and produce a structured report.

Backends supported (choose one):
  1) Ollama (default): requires `ollama` running locally.
     Example model: `llama3.1`, `qwen2.5:7b-instruct`, `mistral`.

  2) Hugging Face Transformers (optional, offline/local):
     Set --backend hf and provide --model (e.g., "Qwen/Qwen2.5-7B-Instruct").
     Requires `transformers` + `torch` installed. Uses a simple chat prompt.

Quick start (Ollama):
  1) Install & run Ollama: https://ollama.com
  2) Pull a chat model, e.g.:   `ollama pull llama3.1`
  3) Run:  python ulpr_lesson_plan_evaluator.py \
            --lesson path/to/lesson.md \
            --backend ollama --model llama3.1 \
            --md-out report.md --json-out report.json

Input can be a file path or raw text via --lesson "...".

Output:
  - Markdown report (optional)
  - JSON breakdown (optional)
  - Console summary

© 2025 — Released for your own use. No warranty.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests  # for Ollama HTTP
except Exception:
    requests = None  # only needed for ollama backend

# Optional HF imports will be attempted only if backend=="hf"

# -------------------------
# Unified Rubric Definition
# -------------------------

@dataclasses.dataclass
class Criterion:
    code: str
    name: str
    weight: float  # contributes to /100 total
    description: str
    band_notes: List[str]  # concise notes for 0→4 (index = band)
    sources: List[str]  # traceability to original metrics


# Bands are standardized across criteria
BAND_DEFS = [
    "0 – Not evident / harmful / misaligned.",
    "1 – Minimal: token, ad-hoc, or unclear; unlikely to impact learning.",
    "2 – Adequate/Developing: present with gaps; partial quality or alignment.",
    "3 – Strong: clear, intentional, and consistent design.",
    "4 – Exemplary: comprehensive, explicit, with routines/tools and verification.",
]

# ULPR criteria — deduplicated & mapped back to the provided metrics.
# Weights sum to 100.
ULPR_CRITERIA: List[Criterion] = [
    # A. Outcomes & Alignment (25)
    Criterion(
        code="A1",
        name="SMARTIE Outcomes & Success Criteria",
        weight=8,
        description=(
            "Outcomes use measurable verbs with success criteria; clearly stated aims; student-friendly;"
            " includes inclusivity/equity within outcomes when relevant."
        ),
        band_notes=[
            "Missing/unclear outcomes or criteria.",
            "Vague aims; outcomes mostly non-measurable (e.g., 'understand').",
            "About half the outcomes are measurable; criteria inconsistent.",
            "Most outcomes are SMARTIE; clear criteria; minor gaps only.",
            "All outcomes are SMARTIE with explicit criteria; clearly linked to aims; inclusive language visible.",
        ],
        sources=["M8.1 Aims & SMARTIE", "M1.1 Learning Intentions", "M6.7 Success Criteria"],
    ),
    Criterion(
        code="A2",
        name="Alignment: TLAs ↔ Outcomes ↔ Assessment",
        weight=9,
        description=(
            "Every key ILO has at least one learning activity and one assessment task at the same cognitive level;"
            " activities and assessment mirror the intended performances."
        ),
        band_notes=[
            "No visible alignment; activities/tests don't match outcomes.",
            "Partial links; several orphaned activities or mismatched levels.",
            "Mostly aligned but with gaps in coverage or level.",
            "Strong match on both content and level across the plan.",
            "Transparent mapping; assessments authentically evidence the performances; students see 'what good looks like'.",
        ],
        sources=["M3.2 TLAs", "M3.3 Assessment authenticity", "M5.6 Alignment", "M8.2 Structure"],
    ),
    Criterion(
        code="A3",
        name="Structure, Timing & Flow",
        weight=8,
        description=(
            "Coherent sequence (activate prior knowledge → model → guided → independent), realistic timings with buffers;"
            " small steps are visible; worked examples precede independence where appropriate."
        ),
        band_notes=[
            "Arbitrary order; unrealistic timing; big undifferentiated 'teach' blocks.",
            "Some sequencing but still rushed/optimistic; limited step design.",
            "Mostly coherent; minor issues; steps are present but uneven.",
            "Clear simple→complex flow with time boxes; steps each have explain→example→short practice.",
            "Exemplary pacing and transitions with contingency buffers; consistent stepwise design.",
        ],
        sources=["M8.2 Structure", "M6.2 Small steps", "M6.4 Worked examples"],
    ),

    # B. Engagement & Interaction (20)
    Criterion(
        code="B1",
        name="ICAP Engagement Mix",
        weight=6,
        description=(
            "Share of time in Constructive/Interactive modes vs Passive/Active; aim for ≥50% C+I with some I."
        ),
        band_notes=[
            "≥80% Passive; little/no Active/Constructive/Interactive.",
            "Mostly Passive/Active; <20% Constructive/Interactive.",
            "30–49% Constructive+Interactive; Interactive brief.",
            "50–69% C+I with ≥10% Interactive.",
            "≥70% C+I with ≥30% Interactive and credible plans to realize it.",
        ],
        sources=["M2.D1 ICAP mix", "M5.1 Active time"],
    ),
    Criterion(
        code="B2",
        name="Generative Tasks & Prompts",
        weight=6,
        description=(
            "Prompts/tasks require explain/justify/compare/predict; rubrics expect new ideas/links, not copies."
        ),
        band_notes=[
            "Recall/copy prompts only.",
            "Occasional higher-order prompts; optional or vague.",
            "Some targeted generative prompts in key episodes.",
            "Frequent, well-framed generative prompts across episodes.",
            "Systematic progression (infer→justify→predict) tightly aligned to outcomes; outputs require novelty/justification.",
        ],
        sources=["M2.D2 Prompts", "M2.D3 Output", "M5.2 Task quality"],
    ),
    Criterion(
        code="B3",
        name="Whole-class Participation & Interactivity",
        weight=8,
        description=(
            "All-student response routines (polls, slates, cold-call with support) + structured group work with roles and joint products."
        ),
        band_notes=[
            "Few respond; volunteers only; 'discuss' with no structure.",
            "Some mechanisms (think-pair-share) but many can stay passive; ad-hoc pairs.",
            "Multiple all-student response moments; groups have prompts but weak interdependence.",
            "Every activity requires all to produce/share; clear roles + shared products; teacher monitoring cues.",
            "Full protocol: roles, timed turns, criteria, rotation, public share-outs or peer-instruction cycles.",
        ],
        sources=["M1.3 Questioning", "M2.D4 Interactivity", "M5.3 Participation", "M5.4 Group structure"],
    ),

    # C. Retrieval & Assessment for Learning (20)
    Criterion(
        code="C1",
        name="Retrieval Density & Effort",
        weight=6,
        description=(
            "Distinct retrieval episodes (≥2–3) with high-effort formats (free recall, short-answer, no-notes problems)."
        ),
        band_notes=[
            "No retrieval opportunities.",
            "Brief recognition-only checks.",
            "One substantial retrieval or mix with low effort.",
            "Two retrievals with ≥50% high-effort.",
            "≥3 retrievals with ≥70% high-effort.",
        ],
        sources=["M4.1 Density", "M4.2 Effort"],
    ),
    Criterion(
        code="C2",
        name="Formative Checks & Actionable Feedback",
        weight=7,
        description=(
            "Aligned exit tickets/mini-quizzes/oral checks with immediate use (reteach/regroup/next task) and task-focused feedback time."
        ),
        band_notes=[
            "No checks; feedback absent or grades only.",
            "One informal check; no action/time to use feedback.",
            "Some checks but misaligned or results not used.",
            "At least one aligned check with stated follow-up; clear feedback plan.",
            "≥2 aligned checks + explicit regroup/reteach plan; scheduled time to apply feedback now.",
        ],
        sources=["M1.4 Feedback", "M1.6 Formative checks", "M6.6 CFU", "M5.5 Feedback loops"],
    ),
    Criterion(
        code="C3",
        name="Spacing, Delayed Checks & Cumulative Coverage",
        weight=7,
        description=(
            "In-lesson spacing between retrievals; planned delayed cumulative checks (≈2 days & 1 week); later quizzes include prior content."
        ),
        band_notes=[
            "No spacing; no delayed checks; no cumulative items.",
            "One immediate end check only; minimal revisit of prior content.",
            "Some spacing or one delayed check; limited cumulative items.",
            "Two spaced retrievals or ≥1 delayed ≥48h; 25–49% prior content later.",
            "≥3 spaced retrievals and both 2‑day & 1‑week checks; ≥50% cumulative items later.",
        ],
        sources=["M4.4 Spacing", "M4.5 Delayed checks", "M4.6 Cumulative"],
    ),

    # D. Instructional Design & Scaffolding (15)
    Criterion(
        code="D1",
        name="Models/Worked Examples & Guided Practice",
        weight=6,
        description=(
            "Full worked examples or think‑alouds precede independence; a timed, scaffolded 'we do' phase is present."
        ),
        band_notes=[
            "None; straight to independent work.",
            "Examples or 'guided' mentioned but thin; no timing/prompts.",
            "Clear worked example and specific guided tasks with timing.",
            "As 3 + contrasting/common‑error example and teacher prompts during circulation.",
            "Exemplary sequencing with decision rules (if‑then triggers) for re‑modeling as needed.",
        ],
        sources=["M6.4 Worked examples", "M6.5 Guided practice"],
    ),
    Criterion(
        code="D2",
        name="Scaffolds & Fading (Generative)",
        weight=5,
        description=(
            "Sentence stems, checklists, partial solutions, compare‑contrast tables; explicit plan to fade supports and provoke self‑explanation."
        ),
        band_notes=[
            "No scaffolds.",
            "Scaffolds named but not shown or not tied to tasks.",
            "Specific artifacts attached and when used.",
            "As 3 + explicit fade steps and timing across tasks.",
            "Well‑timed scaffolds that trigger Constructive/Interactive moves with monitored fade‑out.",
        ],
        sources=["M6.8 Scaffolds", "M2.D6 Generative scaffolds"],
    ),
    Criterion(
        code="D3",
        name="Independent Practice & Monitoring",
        weight=4,
        description=(
            "Independent tasks mirror models; circulation/monitoring plan with error interception (mini‑conferences etc.)."
        ),
        band_notes=[
            "Homework/worksheet only; no monitoring.",
            "Tasks listed; monitoring approach unclear.",
            "Mirror‑tasks + circulation plan (who/when/what).",
            "As 3 + error‑interception plan.",
            "Exemplary: targeted monitoring by pattern; data informs next tasks.",
        ],
        sources=["M6.9 Independent practice"],
    ),

    # E. Cognitive Load & Adaptation (12)
    Criterion(
        code="E1",
        name="Intrinsic Load Sequencing",
        weight=3,
        description=(
            "Simple→complex progression; isolate hard elements before integration; optional goal‑free early tasks."
        ),
        band_notes=[
            "Jumps into complexity; no scaffolding.",
            "Mentions 'start simple' but tasks still complex.",
            "Some segmentation; major topics still overloaded.",
            "Clear simple→complex; isolate then integrate.",
            "As 3 + goal‑free early tasks/self‑paced segments with staged complexity.",
        ],
        sources=["M7.1 Intrinsic load"],
    ),
    Criterion(
        code="E2",
        name="Extraneous Load Minimization & Modality",
        weight=5,
        description=(
            "Integrated materials (no split‑attention); signaling; concise on‑screen text; narration aligned with visuals; brief processing pauses."
        ),
        band_notes=[
            "Pervasive split‑attention; read‑aloud slides; long unbroken content.",
            "Occasional integration; mostly fragmented.",
            "Some integrated visuals; reduced duplication; not consistent.",
            "Consistent integration; redundant text removed; timing and pauses planned.",
            "As 4 + learner pace control on transient content; captions are succinct cues.",
        ],
        sources=["M7.2 Extraneous", "M7.4 Modality"],
    ),
    Criterion(
        code="E3",
        name="Expertise Adaptation & Load Monitoring",
        weight=4,
        description=(
            "Early probe; novices get more guidance; supports fade; quick effort/load checks (e.g., 1–9) trigger specific adjustments."
        ),
        band_notes=[
            "Same tasks/support for all; no checks.",
            "Vague differentiation; generic exit ticket only.",
            "Some leveled tasks or brief effort checks; actions unclear.",
            "Planned probe + defined if‑then tweaks (raise/lower challenge).",
            "As 4 + revision notes to update materials post‑lesson based on patterns.",
        ],
        sources=["M7.5 Expertise", "M7.6 Load monitoring"],
    ),

    # F. Inclusivity, Culture & Reflection (8)
    Criterion(
        code="F1",
        name="UDL & Accessibility",
        weight=5,
        description=(
            "Multiple means of representation/action/engagement; clear instructions; proactive accommodations (captions/alt text/contrast)."
        ),
        band_notes=[
            "No inclusivity/accessibility provisions.",
            "Minimal one‑size‑fits‑all instructions; token UDL.",
            "At least one UDL area addressed; limited choice.",
            "Two+ UDL areas with choice; instructions clear for all.",
            "Two+ options in two+ UDL areas + proactive accommodations.",
        ],
        sources=["M8.7 UDL"],
    ),
    Criterion(
        code="F2",
        name="Culture of Success & Reflection",
        weight=3,
        description=(
            "Error‑friendly norms; progress tracking; structured reflection linked to ILOs informs next steps."
        ),
        band_notes=[
            "Ranking/competition focus; no reflection.",
            "Positive language but ad‑hoc; optional reflection prompts only.",
            "Some tracking or brief reflection; limited link to ILOs.",
            "Norms/tools normalize errors + reflection linked to ILOs and decisions.",
            "Evidence that reflection generates conceptual change; informs future design/assessment.",
        ],
        sources=["M1.8 Culture", "M3.4 Reflection"],
    ),
]

# -------------------------
# LLM Prompt & Backends
# -------------------------

SYSTEM_PROMPT = (
    "You are an expert rater of lesson plans. Score using the Unified Lesson Plan Rubric (ULPR) with bands 0–4. "
    "Use only evidence visible in the plan. If evidence is missing or vague, choose the lower band. "
    "Return ONLY a single valid JSON object (no prose, no markdown). "
    "You MUST include ALL criterion codes exactly once: A1, A2, A3, B1, B2, B3, C1, C2, C3, D1, D2, D3, E1, E2, E3, F1, F2."
)

SCHEMA_SPEC = {
    "type": "object",
    "properties": {
        "criteria": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "band": {"type": "integer", "minimum": 0, "maximum": 4},
                    "evidence": {"type": "string"},
                    "notes": {"type": "string"},
                },
                "required": ["band", "evidence"],
            },
        },
        "global_notes": {"type": "string"},
    },
    "required": ["criteria"],
}


def build_user_prompt(lesson_text: str) -> str:
    def crit_block(c: Criterion) -> str:
        notes = "\n".join([f"  {i}: {c.band_notes[i]}" for i in range(5)])
        return (
            f"{c.code} — {c.name} (weight {c.weight})\n"
            f"What to look for: {c.description}\n"
            f"Bands:\n{notes}\n"
        )

    rubric_text = "\n".join(crit_block(c) for c in ULPR_CRITERIA)

    schema_text = json.dumps(SCHEMA_SPEC, indent=2)

    required_codes = [c.code for c in ULPR_CRITERIA]
    skeleton = {
        "criteria": {code: {"band": 0, "evidence": "", "notes": ""} for code in required_codes},
        "global_notes": "",
    }
    skeleton_text = json.dumps(skeleton, indent=2)

    prompt = f"""
Score the following lesson plan using the Unified Lesson Plan Rubric (ULPR) with bands 0–4.
For each criterion code (A1..F2), choose ONE band (0–4) and provide 1–3 sentences of evidence quoted or paraphrased from the plan.
If a claim (e.g., 'interactive' or 'alignment') is asserted but not operationalized with routines/tools/timing, score lower.

Ties go LOWER if the plan does not include explicit artifacts (items, prompts, rubrics, timings, roles, etc.).

Return ONLY valid JSON and include ALL codes. Use exactly this object structure (ALL keys must exist):
{skeleton_text}

Also adhere to this JSON schema:
{schema_text}

Rubric (condensed):
{rubric_text}

Lesson Plan:
""".strip()
    return prompt + "\n\n" + lesson_text.strip()


# -------------------------
# Backends
# -------------------------

class LLMBackend:
    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class OllamaBackend(LLMBackend):
    def __init__(self, model: str = "llama3.1", url: str = "http://localhost:11434/api/chat"):
        if requests is None:
            raise RuntimeError("requests is required for Ollama backend. Install with `pip install requests`. ")
        self.model = model
        self.url = url

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_ctx": 8192},
        }
        r = requests.post(self.url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        # Ollama may return either {"message": {"content": "..."}} or aggregate messages
        if isinstance(data, dict) and "message" in data and isinstance(data["message"], dict):
            return data["message"].get("content", "")
        # Fallback: try to read first 'content' found
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict) and "content" in v:
                    return v["content"]
        return json.dumps({"error": "Unexpected Ollama response", "raw": data})


class HFBackend(LLMBackend):
    def __init__(self, model: str = "Qwen/Qwen2.5-7B-Instruct", device: Optional[str] = None):
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
            import torch
        except Exception as e:
            raise RuntimeError(
                "Hugging Face backend requires transformers+torch installed."
            ) from e
        from transformers import AutoModelForCausalLM, AutoTokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model)
        self.model = AutoModelForCausalLM.from_pretrained(model, device_map="auto")
        self.device = device

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        # Simple chat-style prompt
        prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>"
        inputs = self.tokenizer([prompt], return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=2048,
            do_sample=True,
            temperature=0.2,
            top_p=0.9,
        )
        text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Return assistant slice (naive)
        parts = text.split("<|assistant|>")
        return parts[-1].strip()


# -------------------------
# Scoring & Post-processing
# -------------------------

def extract_json(text: str) -> Dict[str, Any]:
    """Extract the first JSON object from text."""
    # Direct try
    try:
        return json.loads(text)
    except Exception:
        pass
    # Fallback: find outermost braces
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        snippet = text[start : end + 1]
        try:
            return json.loads(snippet)
        except Exception:
            # Attempt common fixes
            snippet = re.sub(r"\\n", "\n", snippet)
            snippet = re.sub(r"\\'", '"', snippet)
            return json.loads(snippet)
    raise ValueError("Could not parse JSON from model output")


@dataclasses.dataclass
class RatedCriterion:
    code: str
    name: str
    weight: float
    band: int
    points: float
    evidence: str
    notes: str


def clamp_band(x: Any) -> int:
    try:
        xi = int(x)
    except Exception:
        return 0
    return max(0, min(4, xi))


def apply_caps(ratings: Dict[str, RatedCriterion]) -> List[str]:
    """Apply cross-criterion caps and adjustments. Return list of cap notes."""
    notes: List[str] = []

    # Constructive Alignment influences: if A2 (alignment) is 0–1 → cap B2 (generative), C2 (formative) at ≤2
    if ratings.get("A2") and ratings["A2"].band <= 1:
        for k in ["B2", "C2"]:
            if k in ratings and ratings[k].band > 2:
                old = ratings[k].band
                ratings[k].band = 2
                ratings[k].points = ratings[k].weight * ratings[k].band / 4.0
                notes.append(f"Cap applied: {k} reduced from {old} to 2 due to weak alignment (A2={ratings['A2'].band}).")

    # If outcomes not measurable (A1<=1) → cap A2 at ≤2 if higher
    if ratings.get("A1") and ratings["A1"].band <= 1 and "A2" in ratings and ratings["A2"].band > 2:
        old = ratings["A2"].band
        ratings["A2"].band = 2
        ratings["A2"].points = ratings["A2"].weight * ratings["A2"].band / 4.0
        notes.append(f"Cap applied: A2 reduced from {old} to 2 because outcomes (A1) are not measurable enough.")

    # CLT fast rule: to award E1 or E2 at band 4, E3 must be ≥2. If not, drop 4→3.
    if ratings.get("E3") and ratings["E3"].band < 2:
        for k in ["E1", "E2"]:
            if k in ratings and ratings[k].band == 4:
                ratings[k].band = 3
                ratings[k].points = ratings[k].weight * ratings[k].band / 4.0
                notes.append(f"CLT guardrail: {k} 4→3 since load monitoring (E3) < 2.")

    # If no delayed checks/cumulative (C3<=1) make it harder to get C2=4 → demote C2 4→3.
    if ratings.get("C3") and ratings["C3"].band <= 1 and ratings.get("C2") and ratings["C2"].band == 4:
        ratings["C2"].band = 3
        ratings["C2"].points = ratings["C2"].weight * ratings["C2"].band / 4.0
        notes.append("Retrieval maturity guardrail: C2 4→3 because spacing/delays/cumulative (C3) are weak.")

    return notes


def rate_from_model(raw: Dict[str, Any]) -> Tuple[Dict[str, RatedCriterion], List[str]]:
    """Convert model JSON into rated criteria; apply caps; return ratings and cap notes."""
    criteria_map = {c.code: c for c in ULPR_CRITERIA}
    got = raw.get("criteria", {}) if isinstance(raw, dict) else {}

    ratings: Dict[str, RatedCriterion] = {}
    missing_codes: List[str] = []

    for c in ULPR_CRITERIA:
        entry = got.get(c.code, {}) if isinstance(got, dict) else {}
        band = clamp_band(entry.get("band", 0))
        evidence = str(entry.get("evidence", ""))[:1200]
        notes = str(entry.get("notes", ""))[:1200]
        points = c.weight * band / 4.0
        ratings[c.code] = RatedCriterion(
            code=c.code,
            name=c.name,
            weight=c.weight,
            band=band,
            points=points,
            evidence=evidence,
            notes=notes,
        )
        if c.code not in got:
            missing_codes.append(c.code)

    cap_notes = apply_caps(ratings)
    return ratings, cap_notes


def totals(ratings: Dict[str, RatedCriterion]) -> Tuple[float, Dict[str, float]]:
    total = 0.0
    by_section = {"A": 0.0, "B": 0.0, "C": 0.0, "D": 0.0, "E": 0.0, "F": 0.0}
    for rc in ratings.values():
        total += rc.points
        by_section[rc.code[0]] += rc.points
    return total, by_section


def format_markdown_report(
    ratings: Dict[str, RatedCriterion],
    cap_notes: List[str],
    model_json: Dict[str, Any],
    lesson_excerpt: str,
) -> str:
    total, by_section = totals(ratings)

    header = f"# Unified Lesson Plan Report (ULPR)\n\nTotal: **{round(total)} / 100**\n\n"

    sec_titles = {
        "A": "Outcomes & Alignment",
        "B": "Engagement & Interaction",
        "C": "Retrieval & Assessment for Learning",
        "D": "Instructional Design & Scaffolding",
        "E": "Cognitive Load & Adaptation",
        "F": "Inclusivity, Culture & Reflection",
    }

    lines = [header]

    # Section summaries
    for sec in "ABCDEF":
        lines.append(f"## {sec}. {sec_titles[sec]} — {round(by_section[sec])} pts\n")
        for code in sorted([k for k in ratings if k.startswith(sec)]):
            r = ratings[code]
            lines.append(
                f"**{r.code} {r.name}** — band {r.band} → {r.points:.1f}/{r.weight}\n\n"
                f"*Evidence:* {r.evidence}\n\n"
                + (f"*Notes:* {r.notes}\n\n" if r.notes else "")
            )

    if cap_notes:
        lines.append("---\n\n### Caps & Guardrails Applied\n")
        for n in cap_notes:
            lines.append(f"- {n}")
        lines.append("\n")

    if model_json.get("global_notes"):
        lines.append("---\n\n### Rater Global Notes\n" + model_json["global_notes"] + "\n")

    # Optional: embed a small excerpt of the plan for context
    excerpt = (lesson_excerpt or "").strip()
    if excerpt:
        excerpt_short = excerpt[:1200] + ("…" if len(excerpt) > 1200 else "")
        lines.append("---\n\n### Lesson Plan (excerpt)\n\n" + "" + excerpt_short + "\n")

    return "\n".join(lines)


# -------------------------
# CLI
# -------------------------

def read_lesson_text(arg: str) -> str:
    if os.path.exists(arg) and os.path.isfile(arg):
        with open(arg, "r", encoding="utf-8") as f:
            return f.read()
    return arg  # treat as raw text


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Unified Lesson Plan Evaluator (ULPR)")
    p.add_argument("--lesson", required=True, help="Path to lesson plan text/markdown OR raw text")
    p.add_argument("--backend", choices=["ollama", "hf"], default="ollama")
    p.add_argument("--model", default="llama3.1", help="Model name (e.g., ollama: llama3.1; HF: Qwen/Qwen2.5-7B-Instruct)")
    p.add_argument("--md-out", default=None, help="Write Markdown report to this path")
    p.add_argument("--json-out", default=None, help="Write raw model JSON to this path")
    p.add_argument("--ollama-url", default="http://localhost:11434/api/chat", help="Ollama chat endpoint")
    args = p.parse_args(argv)

    lesson_text = read_lesson_text(args.lesson)

    # Build prompts
    user_prompt = build_user_prompt(lesson_text)

    if args.backend == "ollama":
        backend = OllamaBackend(model=args.model, url=args.ollama_url)
    else:
        backend = HFBackend(model=args.model)

    print("→ Querying model…", file=sys.stderr)
    raw_text = backend.generate(SYSTEM_PROMPT, user_prompt)

    try:
        model_json = extract_json(raw_text)
    except Exception as e:
        print("Model output was not valid JSON. Raw output:\n", raw_text, file=sys.stderr)
        raise

    ratings, cap_notes = rate_from_model(model_json)
    report_md = format_markdown_report(ratings, cap_notes, model_json, lesson_excerpt=lesson_text[:3000])

    total, _ = totals(ratings)
    print(f"\nULPR Total: {round(total)} / 100\n")

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(model_json, f, ensure_ascii=False, indent=2)
        print(f"Saved JSON → {args.json_out}")

    if args.md_out:
        with open(args.md_out, "w", encoding="utf-8") as f:
            f.write(report_md)
        print(f"Saved Markdown report → {args.md_out}")

    # Console preview
    print("\n=== Report Preview ===\n")
    print(report_md[:3000] + ("\n…\n" if len(report_md) > 3000 else ""))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
