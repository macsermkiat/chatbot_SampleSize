"""Extract computed sample sizes from chatbot response text and code output.

Looks for numerical values in common patterns like "N = 91",
"n per group = 91", "sample size: 91", and markdown tables.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExtractedN:
    """Extracted sample size value from a response."""

    value: int
    source: str  # "response_text", "code_output", "execution_result"
    match_text: str  # The actual text that was matched


def extract_sample_size(
    response_text: str,
    code_output: str,
    execution_result: str,
    expected_keys: dict[str, Any],
) -> ExtractedN | None:
    """Extract the primary sample size from chatbot outputs.

    Checks execution_result first (most reliable), then code_output,
    then response_text. Returns the best match or None.

    Args:
        response_text: The natural language response from the chatbot.
        code_output: Any generated code.
        execution_result: Stdout from code execution.
        expected_keys: The benchmark's expected dict, used to determine
            which N to look for (n_per_group, total_n, total_events, etc.).
    """
    # Determine which key to extract based on what the benchmark expects
    primary_key = _get_primary_key(expected_keys)

    # 1. Try execution result first (most reliable -- direct code output)
    if execution_result:
        n = _extract_from_text(execution_result, primary_key)
        if n is not None:
            return ExtractedN(value=n, source="execution_result", match_text=execution_result[:200])

    # 2. Try code output (sometimes the script prints the value)
    if code_output:
        n = _extract_from_text(code_output, primary_key)
        if n is not None:
            return ExtractedN(value=n, source="code_output", match_text=code_output[:200])

    # 3. Try response text (natural language, least reliable)
    if response_text:
        n = _extract_from_text(response_text, primary_key)
        if n is not None:
            return ExtractedN(value=n, source="response_text", match_text=response_text[:200])

    return None


def _get_primary_key(expected: dict[str, Any]) -> str:
    """Determine which sample size metric to extract."""
    if "total_events" in expected:
        return "events"
    if "n_per_group_individual" in expected:
        return "n_individual"
    if "n_per_group" in expected:
        return "n_per_group"
    if "n_control" in expected:
        return "n_control"
    return "total_n"


def _extract_from_text(text: str, primary_key: str) -> int | None:
    """Extract the most relevant integer from text using pattern matching."""
    # Normalize whitespace
    text = " ".join(text.split())

    # Choose patterns based on what we're looking for
    if primary_key == "events":
        patterns = _EVENT_PATTERNS + _GENERAL_N_PATTERNS
    elif primary_key == "n_per_group":
        patterns = _PER_GROUP_PATTERNS + _GENERAL_N_PATTERNS
    elif primary_key == "n_individual":
        patterns = _INDIVIDUAL_PATTERNS + _PER_GROUP_PATTERNS + _GENERAL_N_PATTERNS
    elif primary_key == "n_control":
        patterns = _CONTROL_PATTERNS + _PER_GROUP_PATTERNS + _GENERAL_N_PATTERNS
    else:
        patterns = _TOTAL_N_PATTERNS + _PER_GROUP_PATTERNS + _GENERAL_N_PATTERNS

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = int(match.group(1).replace(",", ""))
                if 2 <= val <= 100000:  # sanity bounds
                    return val
            except (ValueError, IndexError):
                continue

    # Last resort: look in markdown table cells for standalone integers
    table_n = _extract_from_table(text, primary_key)
    if table_n is not None:
        return table_n

    return None


def _extract_from_table(text: str, primary_key: str) -> int | None:
    """Extract N from markdown table rows."""
    # Match rows like "| N per group | 91 |" or "| Total N | 182 |"
    if primary_key == "events":
        row_patterns = [
            r"\|\s*(?:total\s+)?events?\s*\|\s*(\d[\d,]*)\s*\|",
            r"\|\s*(?:required\s+)?events?\s*\|\s*(\d[\d,]*)\s*\|",
        ]
    elif primary_key in ("n_per_group", "n_individual"):
        row_patterns = [
            r"\|\s*[Nn]\s+per\s+group\s*\|\s*(\d[\d,]*)\s*\|",
            r"\|\s*(?:sample\s+size\s+)?per\s+(?:group|arm)\s*\|\s*(\d[\d,]*)\s*\|",
            r"\|\s*[Nn]\s*\|\s*(\d[\d,]*)\s*\|",
        ]
    else:
        row_patterns = [
            r"\|\s*[Tt]otal\s+[NnSs]\w*\s*\|\s*(\d[\d,]*)\s*\|",
            r"\|\s*[Nn]\s*\|\s*(\d[\d,]*)\s*\|",
            r"\|\s*[Ss]ample\s+[Ss]ize\s*\|\s*(\d[\d,]*)\s*\|",
        ]

    for pattern in row_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                val = int(match.group(1).replace(",", ""))
                if 2 <= val <= 100000:
                    return val
            except (ValueError, IndexError):
                continue
    return None


# Pattern groups ordered by specificity (most specific first)

_EVENT_PATTERNS = [
    r"(?:total\s+)?(?:number\s+of\s+)?events?\s*(?:needed|required)?\s*(?:=|:|\bis\b)\s*(\d[\d,]*)",
    r"(\d[\d,]*)\s*(?:total\s+)?events?\s*(?:are\s+)?(?:needed|required)?",
    r"(?:approximately|about|roughly|need)\s+(\d[\d,]*)\s*events?",
    r"[Dd]\s*=\s*(\d[\d,]*)",
]

_PER_GROUP_PATTERNS = [
    r"[Nn]\s*(?:per|each)\s*(?:group|arm)\s*(?:=|:|\bis\b)\s*(\d[\d,]*)",
    r"(\d[\d,]*)\s*(?:per|each|in\s+each)\s*(?:group|arm)",
    r"(?:need|require)\s*(\d[\d,]*)\s*(?:per|each|in\s+each)\s*(?:group|arm)",
    r"[Nn]\s*=\s*(\d[\d,]*)\s*per",
]

_TOTAL_N_PATTERNS = [
    r"[Tt]otal\s*(?:[Nn]|sample\s*size)\s*(?:=|:|\bis\b)\s*(\d[\d,]*)",
    r"(\d[\d,]*)\s*(?:total|overall)\s*(?:participants?|subjects?|patients?|sample)",
    r"(?:total\s+of\s+)(\d[\d,]*)\s*(?:participants?|subjects?|patients?)",
]

_CONTROL_PATTERNS = [
    r"(?:control|smaller)\s*(?:group)?\s*(?:=|:|\bis\b)\s*(\d[\d,]*)",
    r"[Nn]_?(?:control|1)\s*=\s*(\d[\d,]*)",
]

_INDIVIDUAL_PATTERNS = [
    r"(?:individual|subject)\s*(?:level)?\s*(?:per\s*(?:group|arm))?\s*(?:=|:|\bis\b)\s*(\d[\d,]*)",
    r"(\d[\d,]*)\s*individuals?\s*per\s*(?:group|arm)",
]

_GENERAL_N_PATTERNS = [
    r"[Nn]\s*=\s*(\d[\d,]*)",
    r"(?:sample\s*size)\s*(?:=|:|\bis\b)\s*(\d[\d,]*)",
    r"(?:need|require)\s*(?:approximately\s+)?(\d[\d,]*)\s*(?:participants?|subjects?|patients?|pairs?)",
    r"(\d[\d,]*)\s*(?:participants?|subjects?|patients?)\s*(?:per\s*group|total|are\s*needed)",
]
