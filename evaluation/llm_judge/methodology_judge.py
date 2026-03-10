"""Methodology-specific judge instructions for enhanced scoring accuracy."""

from __future__ import annotations

# Additional context injected into judge prompts when evaluating methodology dimensions.
# These supplement the base JUDGE_SYSTEM_PROMPT with domain-specific guidance.

METHODOLOGY_JUDGE_CONTEXT = """\
You are evaluating a medical research methodology response. Apply these \
domain-specific standards:

CAUSAL INFERENCE (M3):
- Target Trial Emulation (TTE) is the gold standard for observational studies
- DAGs (Directed Acyclic Graphs) should identify confounders vs colliders vs mediators
- Look for: time zero definition, eligibility criteria alignment, treatment strategies
- Penalize conflation of association and causation
- Grace periods and immortal time bias handling are advanced concepts (score 5)

BIAS IDENTIFICATION (M4):
- Minimum expected: selection bias, information bias
- Good: immortal time bias, protopathic bias, confounding by indication
- Excellent: mechanism explanation, direction of bias, quantitative sensitivity analysis
- Look for bias-specific mitigation strategies, not just generic "be careful"

EQUATOR GUIDELINES (M6):
- Match guideline to study design: CONSORT=RCT, STROBE=observational, PRISMA=SR, \
STARD=diagnostic, SPIRIT=protocol
- Penalize wrong guideline for the study type
- Score 5 requires specific checklist items, not just naming the guideline

STUDY DESIGN (M2):
- Hierarchy: RCT > prospective cohort > retrospective cohort > case-control > cross-sectional
- But the BEST design depends on the question (RCT isn't always feasible or ethical)
- Look for feasibility discussion alongside design choice
- Pragmatic vs explanatory trial distinction is advanced

ETHICS (M5):
- Minimum: mention of IRB/ethics committee
- Good: equipoise discussion, informed consent specifics
- Excellent: justice considerations, data sovereignty, vulnerable populations, \
Declaration of Helsinki application

EXPERTISE CALIBRATION:
- "simple" mode: Analogies, plain language, avoid excessive jargon. \
Score higher if complex concepts are made accessible.
- "advanced" mode: Precise terminology expected. Penalize if oversimplified \
for an advanced audience.
"""

# Dimension-specific scoring reminders that get appended to evaluation prompts
DIMENSION_REMINDERS: dict[str, str] = {
    "M1": (
        "PICO/PICOTS scoring: P must specify inclusion/exclusion criteria, "
        "I must be operationalized (dose, duration, route), "
        "C must name specific comparator, O must define measurement method, "
        "T and S are bonus for score 5."
    ),
    "M2": (
        "Study design: consider whether the chosen design matches the research "
        "question type (therapy, prognosis, diagnosis, etiology). "
        "Penalize if design is theoretically correct but practically infeasible."
    ),
    "M3": (
        "Causal inference: DAG reasoning should identify specific confounders, "
        "not just state 'there may be confounders.' TTE framework with time zero, "
        "eligibility, treatment strategy alignment = score 5."
    ),
    "M4": (
        "Bias: count distinct, relevant biases. Generic bias statements = 3. "
        "Mechanism + direction + mitigation for each = 5. "
        "Wrong bias identification should reduce score."
    ),
    "M5": (
        "Ethics: IRB mention alone = 2. Helsinki + equipoise + consent = 3-4. "
        "Justice, data sovereignty, vulnerable populations = 5. "
        "This dimension has weight 0.75 (less critical for overall score)."
    ),
    "M6": (
        "EQUATOR: wrong guideline for study type = 1. "
        "Correct guideline named = 3. Specific items from checklist = 4-5. "
        "Check: CONSORT for RCT, STROBE for observational, PRISMA for SR."
    ),
    "M7": (
        "Explanation quality: match to expertise_mode. "
        "Simple mode: use analogies, avoid jargon, build from basics. "
        "Advanced mode: precise terminology, cite literature conventions. "
        "Mismatched register = max score 3."
    ),
    "M8": (
        "Actionability: can a resident take this advice and start a protocol? "
        "Vague: 'consider using a questionnaire' = 2. "
        "Specific: 'use PHQ-9, administered at baseline and 6 weeks, "
        "by trained RA' = 5."
    ),
}


def get_methodology_context() -> str:
    """Return the full methodology judge context string."""
    return METHODOLOGY_JUDGE_CONTEXT


def get_dimension_reminder(dimension_id: str) -> str:
    """Return dimension-specific scoring reminder, if available."""
    return DIMENSION_REMINDERS.get(dimension_id, "")
