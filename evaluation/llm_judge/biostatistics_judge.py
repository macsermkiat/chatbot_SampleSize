"""Biostatistics-specific judge instructions for enhanced scoring accuracy."""

from __future__ import annotations

# Additional context injected into judge prompts when evaluating biostatistics dimensions.

BIOSTATISTICS_JUDGE_CONTEXT = """\
You are evaluating a biostatistics/sample size response. Apply these \
domain-specific standards:

TEST SELECTION (B1):
- The correct test depends on: data type, number of groups, paired vs \
independent, distribution assumptions
- Decision tree: continuous/categorical -> paired/independent -> normal/non-normal
- Correct test with assumption justification = 4
- Correct test + decision logic + sensitivity alternatives = 5
- Partially correct (e.g., t-test when ANOVA needed) = 2-3

SAMPLE SIZE CALCULATION (B2):
- Required elements: effect size, variance, alpha, power, formula
- Check mathematical correctness of the calculation
- Score 3: correct base calculation
- Score 4: adds dropout adjustment
- Score 5: adds clustering (ICC/DEFF), multiplicity adjustment, sensitivity \
table across effect sizes

CODE CORRECTNESS (B3):
- Does the code execute without errors?
- Does it produce the correct numerical result?
- Correct within 10% of ground truth = acceptable
- Uses appropriate libraries (statsmodels, scipy, pwr in R)
- Handles edge cases (zero variance, missing data)

ASSUMPTION CHECKING (B4):
- Minimum: name the key assumptions
- Good: state how to check each assumption (Shapiro-Wilk, Levene's, etc.)
- Excellent: interpretation guidance + robust alternatives when violated
- Common assumptions: normality, homogeneity of variance, independence, \
proportional hazards

EFFECT SIZE (B5):
- Beyond p-value: report effect size with confidence interval
- Cohen's d conventions (0.2 small, 0.5 medium, 0.8 large) are a start
- Clinical MCID (Minimal Clinically Important Difference) = advanced
- NNT/NNH calculation = score 5

CLINICAL VS STATISTICAL SIGNIFICANCE (B6):
- Clear distinction: statistically significant does not mean clinically meaningful
- MCID discussion + CI interpretation framework = 5
- Conflating the two = 1-2
- Example: "p=0.01 with 0.1% HbA1c difference is statistically significant \
but not clinically meaningful"

EL12 EXPLANATION QUALITY (B7):
- "EL12" = Explain Like I'm 12 (for simple mode)
- Analogies for statistical concepts (coin flipping for p-values, etc.)
- Accurate simplification: must not sacrifice correctness for accessibility
- Advanced mode: precise statistical language, distributional assumptions
- Mismatched register (jargon for novice, or oversimplified for expert) = max 3

CODE QUALITY (B8):
- Readable with comments? Parameterized (not hardcoded values)?
- Uses canonical libraries (statsmodels, scipy.stats, not custom implementations)?
- Output is formatted and labeled?
- Publication-quality = score 5 (could paste into methods section)
"""

DIMENSION_REMINDERS: dict[str, str] = {
    "B1": (
        "Test selection: verify the test matches the data structure. "
        "Two continuous groups -> t-test/Mann-Whitney. "
        "Two categorical -> chi-square/Fisher's. "
        "Survival -> log-rank/Cox. Paired -> paired t/Wilcoxon signed-rank. "
        "Multiple groups -> ANOVA/Kruskal-Wallis."
    ),
    "B2": (
        "Sample size: check formula correctness. "
        "For t-test: n = 2*((z_alpha + z_beta)^2 * sigma^2) / delta^2. "
        "For proportions: different formula. "
        "Dropout adjustment = n / (1-dropout_rate). "
        "Cluster adjustment = n * DEFF where DEFF = 1 + (m-1)*ICC."
    ),
    "B3": (
        "Code correctness: does the code run? Does it produce a number "
        "within 10% of the expected sample size? "
        "Syntax errors = 1. Runs but wrong answer = 2. "
        "Correct answer = 4. Correct + edge cases = 5."
    ),
    "B4": (
        "Assumptions: for t-test check normality + equal variance. "
        "For chi-square check expected cell counts >= 5. "
        "For Cox check proportional hazards. "
        "Naming assumptions = 3. Testing + alternatives = 5."
    ),
    "B5": (
        "Effect size: p-value alone = 1. Cohen's d = 3. "
        "MCID + CI + literature comparison = 5. "
        "NNT for binary outcomes is a strong indicator of score 5."
    ),
    "B6": (
        "Clinical vs statistical: look for explicit statement that a "
        "small p-value does not guarantee clinical importance. "
        "MCID definition + CI interpretation = 5. "
        "No distinction made = 1-2."
    ),
    "B7": (
        "EL12 explanation: in simple mode, score 5 requires accessible "
        "analogies that are still accurate. In advanced mode, precise "
        "statistical language is expected. "
        "Incorrect simplification (e.g., wrong p-value interpretation) = max 2."
    ),
    "B8": (
        "Code quality: weight 0.75. Readable + commented = 3. "
        "Parameterized + canonical libraries + formatted output = 5. "
        "No code provided = 1."
    ),
}


def get_biostatistics_context() -> str:
    """Return the full biostatistics judge context string."""
    return BIOSTATISTICS_JUDGE_CONTEXT


def get_dimension_reminder(dimension_id: str) -> str:
    """Return dimension-specific scoring reminder, if available."""
    return DIMENSION_REMINDERS.get(dimension_id, "")
