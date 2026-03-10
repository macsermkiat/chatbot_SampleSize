"""Check if the recommended statistical test matches ground truth."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Synonym map: canonical test name -> list of acceptable variations
TEST_SYNONYMS: dict[str, list[str]] = {
    "independent two-sample t-test": [
        "independent t-test",
        "student's t-test",
        "unpaired t-test",
        "two-sample t-test",
        "independent samples t-test",
        "two-group t-test",
    ],
    "paired t-test": [
        "dependent t-test",
        "matched-pairs t-test",
        "repeated measures t-test",
        "paired samples t-test",
    ],
    "Mann-Whitney U test": [
        "wilcoxon rank-sum",
        "mann-whitney",
        "mann whitney",
        "rank-sum test",
        "wilcoxon rank sum",
    ],
    "Wilcoxon signed-rank test": [
        "wilcoxon signed-rank",
        "wilcoxon signed rank",
        "signed-rank test",
    ],
    "chi-square test": [
        "chi-square",
        "chi-squared",
        "pearson chi-square",
        "chi square",
        "χ²",
        "x2 test",
    ],
    "Fisher's exact test": [
        "fisher exact",
        "fisher's exact",
        "exact test",
    ],
    "one-way ANOVA": [
        "one-way anova",
        "anova",
        "analysis of variance",
        "f-test",
    ],
    "Kruskal-Wallis test": [
        "kruskal-wallis",
        "kruskal wallis",
        "non-parametric anova",
        "h test",
    ],
    "Friedman test": [
        "friedman",
        "friedman's anova",
        "friedman test",
        "non-parametric repeated measures",
    ],
    "Pearson correlation": [
        "pearson correlation",
        "pearson's r",
        "linear correlation",
        "pearson coefficient",
    ],
    "Spearman rank correlation": [
        "spearman",
        "spearman's rho",
        "rank correlation",
        "spearman correlation",
    ],
    "logistic regression": [
        "logistic regression",
        "multivariable logistic",
        "multiple logistic",
        "binary logistic",
    ],
    "linear regression": [
        "linear regression",
        "multiple regression",
        "multiple linear regression",
        "ols regression",
    ],
    "Cox proportional hazards": [
        "cox regression",
        "cox ph",
        "cox proportional hazards",
        "cox model",
        "proportional hazards",
    ],
    "log-rank test": [
        "log-rank",
        "log rank",
        "logrank",
        "kaplan-meier with log-rank",
    ],
    "mixed-effects model": [
        "mixed model",
        "mixed effects",
        "hierarchical linear model",
        "hlm",
        "multilevel model",
        "random effects model",
    ],
    "repeated measures ANOVA": [
        "repeated measures anova",
        "rm-anova",
        "within-subjects anova",
    ],
    "Fine-Gray model": [
        "fine-gray",
        "fine gray",
        "subdistribution hazard",
        "competing risks regression",
        "cumulative incidence",
    ],
    "GEE": [
        "generalized estimating equations",
        "gee",
        "marginal model",
    ],
    "TOST": [
        "tost",
        "two one-sided tests",
        "bioequivalence test",
        "equivalence test",
        "non-inferiority test",
    ],
    "Dunnett's test": [
        "dunnett",
        "dunnett's",
        "many-to-one comparison",
    ],
}


@dataclass(frozen=True)
class TestCheckResult:
    """Result of checking statistical test selection."""

    case_id: str
    system_id: str
    expected_test: str
    detected_test: str
    is_correct: bool
    matched_synonym: str
    confidence: float


def check_statistical_test(
    case_id: str,
    system_id: str,
    response_text: str,
    expected_test: str,
    accepted_synonyms: list[str] | None = None,
) -> TestCheckResult:
    """Check if the response recommends the correct statistical test.

    Args:
        case_id: Test case identifier.
        system_id: System that produced the response.
        response_text: The full response text to search.
        expected_test: The canonical correct test name.
        accepted_synonyms: Additional accepted names beyond the built-in map.
    """
    text_lower = response_text.lower()

    # Build list of acceptable terms
    acceptable = [expected_test.lower()]

    # Add built-in synonyms
    for canonical, synonyms in TEST_SYNONYMS.items():
        if expected_test.lower() in [canonical.lower()] + [
            s.lower() for s in synonyms
        ]:
            acceptable.extend([canonical.lower()] + [s.lower() for s in synonyms])

    # Add user-provided synonyms
    if accepted_synonyms:
        acceptable.extend(s.lower() for s in accepted_synonyms)

    # Deduplicate
    acceptable = list(set(acceptable))

    # Search for matches
    best_match = ""
    best_confidence = 0.0
    for term in acceptable:
        # Use word boundary matching for accuracy
        pattern = re.escape(term)
        matches = re.findall(pattern, text_lower)
        if matches:
            # Higher confidence for longer, more specific matches
            confidence = min(1.0, len(term) / 20.0 + 0.5)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = term

    return TestCheckResult(
        case_id=case_id,
        system_id=system_id,
        expected_test=expected_test,
        detected_test=best_match,
        is_correct=bool(best_match),
        matched_synonym=best_match,
        confidence=best_confidence,
    )
