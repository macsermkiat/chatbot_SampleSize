"""Biostatistics agent evaluation rubric -- 8 dimensions, 5-level anchored scoring."""

from __future__ import annotations

from evaluation.rubrics.schema import Rubric, RubricDimension, ScoreAnchor


BIOSTATISTICS_RUBRIC: Rubric = None  # type: ignore[assignment]  # set at module bottom


def build_biostatistics_rubric() -> Rubric:
    """Construct the full biostatistics evaluation rubric."""
    return Rubric(
        rubric_id="biostatistics_v1",
        name="Biostatistics Agent Evaluation Rubric",
        description=(
            "Evaluates biostatistical advice across 8 dimensions: "
            "test selection, sample size calculation, code correctness, "
            "assumption checking, effect size interpretation, clinical vs "
            "statistical significance, explanation quality, and code quality."
        ),
        dimensions=[
            _test_selection_dimension(),
            _sample_size_dimension(),
            _code_correctness_dimension(),
            _assumption_checking_dimension(),
            _effect_size_dimension(),
            _clinical_significance_dimension(),
            _explanation_quality_dimension(),
            _code_quality_dimension(),
        ],
    )


def _test_selection_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B1",
        name="Statistical Test Selection Correctness",
        description=(
            "Is the recommended statistical test appropriate for the data "
            "structure, variable types, and research question?"
        ),
        weight=1.5,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Completely wrong test for the scenario. For example, "
                    "recommending an independent t-test for time-to-event data, "
                    "or chi-square for continuous outcomes."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Partially appropriate test family but wrong variant. "
                    "For example, paired t-test when groups are independent, "
                    "or parametric test when data is clearly non-normal "
                    "without mentioning alternatives."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Correct test for the data structure. Assumptions mentioned "
                    "but not thoroughly checked. No discussion of alternatives "
                    "if assumptions are violated."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Correct test with assumptions explicitly stated. "
                    "Alternative tests recommended if assumptions are violated. "
                    "Decision logic explained (why this test over others)."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Optimal test with full decision reasoning: variable types "
                    "identified, distribution assessed, dependency structure "
                    "analyzed. Primary and sensitivity test recommendations "
                    "with clear justification. Acknowledges valid alternatives "
                    "and explains why the chosen test is preferred."
                ),
            ),
        ],
    )


def _sample_size_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B2",
        name="Sample Size / Power Calculation Correctness",
        description=(
            "Are the sample size or power calculations correct? Are the "
            "input parameters appropriate? Are adjustments applied?"
        ),
        weight=1.5,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Completely wrong formula or parameters. Order of magnitude "
                    "error in result. Or states a sample size without any "
                    "calculation or justification."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Correct formula family but wrong parameters (e.g., using "
                    "one-sided test when two-sided is appropriate) or missing "
                    "critical adjustments (dropout, multiple comparisons)."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Correct base calculation with standard defaults "
                    "(alpha=0.05, power=0.80). Result within acceptable range. "
                    "Minor issues with parameter justification."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Correct calculation with appropriate adjustments: dropout "
                    "rate inflation, design effect for clustering, continuity "
                    "correction. Parameters justified from literature or "
                    "clinical practice."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Correct calculation with all parameters well-justified "
                    "(from pilot data, literature, or clinical reasoning). "
                    "Appropriate adjustments (dropout, clustering, multiplicity). "
                    "Either a sensitivity analysis across plausible effect sizes "
                    "OR a single well-justified effect size with rationale. "
                    "Clinically meaningful interpretation of the required "
                    "sample size in terms of feasibility."
                ),
            ),
        ],
    )


def _code_correctness_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B3",
        name="Code Correctness",
        description=(
            "Does the generated code execute successfully and produce "
            "correct numerical results?"
        ),
        weight=1.5,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "No code provided, or code has syntax errors and cannot "
                    "execute. Missing imports, undefined variables, or "
                    "fundamental logic errors."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Code executes but produces incorrect results. Wrong "
                    "function calls, incorrect parameter mapping, or "
                    "mathematical errors in the calculation."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Code executes and produces approximately correct results "
                    "(within 10% of ground truth). Uses appropriate library "
                    "functions but may have minor parameter issues."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Code executes, produces correct results (within 5% of "
                    "ground truth), uses canonical library functions "
                    "(e.g., statsmodels.stats.power). Handles standard cases."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Code executes with exact correct results. Uses optimal "
                    "methods (closed-form where possible). Handles edge cases "
                    "(very small effect sizes, extreme alpha). Includes "
                    "parameter validation and informative error messages."
                ),
            ),
        ],
    )


def _assumption_checking_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B4",
        name="Assumption Checking",
        description=(
            "Does the response identify and address the statistical "
            "assumptions required by the recommended test or calculation?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description="No assumptions mentioned or discussed.",
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Assumptions listed generically ('data should be normal') "
                    "but not checked, verified, or specific to the scenario."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Key assumptions stated with guidance on how to check "
                    "them (e.g., Shapiro-Wilk for normality, Levene's for "
                    "homogeneity of variance). Relevant to the chosen test."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Assumptions stated, checking procedures described with "
                    "specific tests, interpretation of results explained, "
                    "and alternative methods given if assumptions are violated."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Comprehensive assumption framework: each assumption "
                    "named, specific diagnostic test recommended, "
                    "interpretation thresholds given, robust alternatives "
                    "specified, and discussion of how assumption violations "
                    "affect the validity of results."
                ),
            ),
        ],
    )


def _effect_size_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B5",
        name="Effect Size Interpretation",
        description=(
            "Does the response discuss effect sizes meaningfully, "
            "beyond just p-values?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "No effect size discussed. Only p-values or significance "
                    "statements. No attempt to quantify the magnitude of effect."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Effect size mentioned but not interpreted clinically. "
                    "May state 'medium effect size' without explaining what "
                    "that means in the clinical context."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Effect size calculated or recommended with Cohen's "
                    "conventions (small/medium/large). Basic interpretation "
                    "of what the effect size means."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Effect size with clinical context: Minimum Clinically "
                    "Important Difference (MCID) discussed, confidence "
                    "interval for effect size recommended."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Effect size framework: MCID defined for the outcome, "
                    "NNT/NNH calculated where applicable, CI interpretation, "
                    "comparison to prior literature effect sizes, discussion "
                    "of clinical vs statistical significance implications."
                ),
            ),
        ],
    )


def _clinical_significance_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B6",
        name="Clinical vs Statistical Significance",
        description=(
            "Does the response clearly distinguish between statistical "
            "significance and clinical importance?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Conflates statistical and clinical significance. "
                    "Treats p < 0.05 as proof of clinical importance."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Mentions the distinction exists but does not "
                    "operationalize it for the current scenario."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Clear distinction between statistical and clinical "
                    "significance with a concrete example from the scenario. "
                    "Explains why a statistically significant result may not "
                    "be clinically meaningful."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Distinction with MCID definition, practical importance "
                    "discussion, and implications for sample size (larger "
                    "samples detect smaller, potentially trivial effects)."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Comprehensive framework: MCID threshold defined, "
                    "equivalence/non-inferiority margins discussed where "
                    "applicable, CI-based interpretation ('absence of "
                    "evidence is not evidence of absence'), and guidance "
                    "on interpreting non-significant results."
                ),
            ),
        ],
    )


def _explanation_quality_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B7",
        name="Explanation Quality",
        description=(
            "Is the statistical explanation clear and accessible? "
            "In simple mode, does it use plain language? In advanced mode, "
            "does it use precise terminology? Are p-values and CIs "
            "explained correctly?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Incomprehensible jargon. No attempt to explain concepts. "
                    "May contain incorrect definitions (e.g., 'p-value is "
                    "the probability the null hypothesis is true')."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Partially understandable but inconsistent tone. "
                    "Uses jargon in simple mode or oversimplifies in "
                    "advanced mode. Some concepts poorly explained."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Clear for the target audience. Key concepts explained. "
                    "p-value and CI definitions are technically correct. "
                    "Appropriate complexity for the expertise level."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Strong pedagogical quality. Concepts build logically. "
                    "p-value correctly framed as 'probability of data this "
                    "extreme assuming no effect'. Good examples and analogies."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Outstanding pedagogical quality. In simple mode: uses "
                    "everyday analogies, no jargon, concise bullet points. "
                    "In advanced mode: precise terminology with nuance. All "
                    "statistical concepts accurately explained. Layered "
                    "explanation that the reader can follow progressively."
                ),
            ),
        ],
    )


def _code_quality_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="B8",
        name="Code Quality",
        description=(
            "Is the generated code well-structured, readable, reproducible, "
            "and following best practices?"
        ),
        weight=0.75,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "No code provided, or completely unreadable spaghetti "
                    "code. No comments, no structure."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Code runs but uses deprecated APIs, has no comments, "
                    "poor variable names (x, y, a, b), or hardcoded "
                    "magic numbers."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Readable code with some comments. Uses current APIs "
                    "and libraries. Variable names are descriptive. "
                    "Basic structure with sections."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Well-structured code with clear sections (imports, "
                    "parameters, calculation, output). Good variable names. "
                    "Proper imports. Formatted output (Markdown tables or "
                    "labeled print statements)."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Publication-quality reproducible script. Parameters "
                    "defined as named variables at top. Uses canonical "
                    "libraries (statsmodels, scipy). Well-commented with "
                    "section headers. Output is formatted, labeled, and "
                    "ready to include in a report."
                ),
            ),
        ],
    )


BIOSTATISTICS_RUBRIC = build_biostatistics_rubric()
