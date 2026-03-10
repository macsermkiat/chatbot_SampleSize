"""Check response completeness for required structural elements."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence


@dataclass(frozen=True)
class CompletenessResult:
    """Result of checking response structural completeness."""

    case_id: str
    system_id: str
    pico_elements_found: dict[str, bool]
    pico_completeness: float
    mentions_bias: bool
    bias_count: int
    biases_found: tuple[str, ...]
    mentions_equator: bool
    equator_guideline_found: str
    mentions_ethics: bool
    mentions_assumptions: bool
    has_code_block: bool
    has_references: bool
    total_word_count: int


# Common bias keywords to detect
BIAS_KEYWORDS = [
    "selection bias",
    "information bias",
    "recall bias",
    "attrition bias",
    "detection bias",
    "performance bias",
    "publication bias",
    "immortal time bias",
    "lead time bias",
    "length time bias",
    "confounding by indication",
    "protopathic bias",
    "neyman bias",
    "prevalence-incidence bias",
    "berkson bias",
    "healthy user bias",
    "hawthorne effect",
    "observer bias",
    "measurement bias",
    "survivor bias",
    "survivorship bias",
    "collider bias",
    "reverse causation",
    "misclassification",
]

EQUATOR_GUIDELINES = {
    "CONSORT": r"\bconsort\b",
    "STROBE": r"\bstrobe\b",
    "PRISMA": r"\bprisma\b",
    "STARD": r"\bstard\b",
    "SPIRIT": r"\bspirit\b",
    "CARE": r"\bcare\b(?!\s+(?:of|for|about))",
    "CHEERS": r"\bcheers\b",
    "MOOSE": r"\bmoose\b",
    "STREGA": r"\bstrega\b",
    "TRIPOD": r"\btripod\b",
}

PICO_PATTERNS = {
    "P": [
        r"\bpopulation\b",
        r"\bpatients?\b",
        r"\bparticipants?\b",
        r"\bsubjects?\b",
        r"\binclusion criteria\b",
        r"\beligib",
    ],
    "I": [
        r"\bintervention\b",
        r"\bexposure\b",
        r"\btreatment\b",
        r"\bdrug\b",
        r"\btherapy\b",
    ],
    "C": [
        r"\bcompar(?:ator|ison)\b",
        r"\bcontrol\b",
        r"\bplacebo\b",
        r"\bstandard (?:of )?care\b",
        r"\bcounterfactual\b",
    ],
    "O": [
        r"\boutcome\b",
        r"\bendpoint\b",
        r"\bprimary (?:outcome|endpoint)\b",
        r"\bmeasure\b",
    ],
    "T": [
        r"\btimeframe\b",
        r"\bfollow[- ]up\b",
        r"\bduration\b",
        r"\btime horizon\b",
    ],
    "S": [
        r"\bsetting\b",
        r"\bhospital\b",
        r"\bclinic\b",
        r"\bcommunity\b",
        r"\bprimary care\b",
    ],
}


def check_completeness(
    case_id: str,
    system_id: str,
    response_text: str,
    additional_response_texts: Sequence[str] = (),
) -> CompletenessResult:
    """Check a response for required structural elements.

    For multi-turn conversations, pass all follow-up response texts via
    ``additional_response_texts``.  The completeness check is applied to
    the concatenation of all turns so that information spread across
    multiple responses is counted.
    """
    combined_text = response_text
    if additional_response_texts:
        combined_text = "\n\n".join(
            [response_text, *additional_response_texts]
        )
    text_lower = combined_text.lower()

    # PICO detection
    pico_found = {}
    for element, patterns in PICO_PATTERNS.items():
        pico_found[element] = any(
            re.search(p, text_lower) for p in patterns
        )
    pico_completeness = sum(pico_found.values()) / len(pico_found) if pico_found else 0.0

    # Bias detection
    biases_found = []
    for bias in BIAS_KEYWORDS:
        if bias.lower() in text_lower:
            biases_found.append(bias)

    # EQUATOR guideline detection
    equator_found = ""
    for guideline, pattern in EQUATOR_GUIDELINES.items():
        if re.search(pattern, text_lower):
            equator_found = guideline
            break

    # Ethics mention
    ethics_keywords = [
        "ethics", "ethical", "irb", "institutional review",
        "informed consent", "helsinki", "equipoise",
    ]
    mentions_ethics = any(kw in text_lower for kw in ethics_keywords)

    # Assumptions mention
    assumption_keywords = [
        "assumption", "normality", "homogeneity", "independence",
        "proportional hazards", "linearity",
    ]
    mentions_assumptions = any(kw in text_lower for kw in assumption_keywords)

    # Code block detection
    has_code_block = "```" in combined_text

    # Reference detection
    reference_patterns = [r"doi:", r"pubmed", r"pmid", r"\d{4};\d+", r"et al\."]
    has_references = any(
        re.search(p, text_lower) for p in reference_patterns
    )

    # Word count
    total_words = len(combined_text.split())

    return CompletenessResult(
        case_id=case_id,
        system_id=system_id,
        pico_elements_found=pico_found,
        pico_completeness=pico_completeness,
        mentions_bias=len(biases_found) > 0,
        bias_count=len(biases_found),
        biases_found=tuple(biases_found),
        mentions_equator=bool(equator_found),
        equator_guideline_found=equator_found,
        mentions_ethics=mentions_ethics,
        mentions_assumptions=mentions_assumptions,
        has_code_block=has_code_block,
        has_references=has_references,
        total_word_count=total_words,
    )
