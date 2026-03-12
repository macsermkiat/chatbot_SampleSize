"""Methodology agent evaluation rubric -- 8 dimensions, 5-level anchored scoring."""

from __future__ import annotations

from evaluation.rubrics.schema import Rubric, RubricDimension, ScoreAnchor


METHODOLOGY_RUBRIC: Rubric = None  # type: ignore[assignment]  # set at module bottom


def build_methodology_rubric() -> Rubric:
    """Construct the full methodology evaluation rubric."""
    return Rubric(
        rubric_id="methodology_v1",
        name="Methodology Agent Evaluation Rubric",
        description=(
            "Evaluates research methodology advice across 8 dimensions: "
            "research question structuring, study design, causal inference, "
            "bias identification, ethical considerations, reporting standards, "
            "explanation quality, and actionability."
        ),
        dimensions=[
            _pico_dimension(),
            _study_design_dimension(),
            _causal_inference_dimension(),
            _bias_identification_dimension(),
            _ethical_considerations_dimension(),
            _reporting_standards_dimension(),
            _explanation_quality_dimension(),
            _actionability_dimension(),
        ],
    )


def _pico_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M1",
        name="Research Question Structuring",
        description=(
            "Does the response translate the clinical question into a clearly "
            "structured, operationalizable research question? Any recognized "
            "framework (PICO, PICOTS, GRADE, FINER, or equivalent) is acceptable."
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "No structuring of the research question. It remains "
                    "vague and unactionable. No attempt to define population, "
                    "intervention/exposure, comparator, or outcome."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "1-2 key elements mentioned but incomplete or imprecise. "
                    "For example, population is vague ('patients with diabetes') "
                    "without age, setting, or severity criteria."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Core elements (population, intervention/exposure, comparator, "
                    "outcome) identified with reasonable specificity. Minor "
                    "imprecisions or missing context (timeframe, setting) that "
                    "would need refinement."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Fully structured question with specific operationalization. "
                    "Population has inclusion/exclusion criteria. Intervention "
                    "and comparator clearly defined. Outcomes include both "
                    "primary and secondary. Context (timeframe, setting) addressed."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Precisely operationalized question with population descriptors "
                    "(demographics, comorbidities, severity), specific "
                    "intervention details (dose, duration, route), explicit "
                    "counterfactual comparator, hard clinical outcomes with "
                    "measurement method, clear timeframe, and defined setting. "
                    "Question is directly translatable to a study protocol."
                ),
            ),
        ],
    )


def _study_design_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M2",
        name="Study Design Appropriateness",
        description=(
            "Is the recommended study design appropriate for answering the "
            "clinical question? Does the response justify the choice?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Wrong study design for the question. For example, recommending "
                    "a cross-sectional study for a causal/temporal question, or "
                    "a case-control for a rare exposure."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Partially appropriate design but missing critical justification. "
                    "Design could work but is not optimal, and the response does not "
                    "explain why this design was chosen over alternatives."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Appropriate design selected with basic justification. "
                    "The match between question type and study design is correct, "
                    "but alternatives are not discussed."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Appropriate design with clear rationale. Alternatives discussed "
                    "with reasons for selection. Considers practical constraints "
                    "(cost, time, ethics, feasibility)."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Optimal design with systematic decision reasoning. Presents "
                    "a hierarchy of designs considered, explains trade-offs "
                    "(internal vs external validity), discusses pragmatic "
                    "considerations, and includes feasibility assessment."
                ),
            ),
        ],
    )


def _causal_inference_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M3",
        name="Causal Inference Rigor",
        description=(
            "Does the response apply appropriate causal reasoning? "
            "This includes confounder identification, distinction between "
            "association and causation, and use of any valid causal framework "
            "(e.g., DAGs, Target Trial Emulation, multivariable adjustment, "
            "propensity scores, instrumental variables)."
        ),
        weight=1.5,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "No mention of causal reasoning. Confuses association with "
                    "causation. No discussion of confounding."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Acknowledges confounding exists but does not address "
                    "systematically. May list potential confounders without "
                    "explaining the causal mechanism."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Identifies key confounders with a plan for adjustment "
                    "(e.g., multivariable regression, stratification, matching). "
                    "Distinguishes association from causation."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Systematic confounding control using any valid framework: "
                    "DAG-based adjustment, propensity scores, Target Trial "
                    "Emulation, or equivalent. Confounders vs mediators "
                    "distinguished. Time zero or index date considerations "
                    "addressed for longitudinal designs."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Rigorous causal framework with explicit variable "
                    "classification (confounder, mediator, collider). "
                    "Sensitivity analysis for unmeasured confounding planned "
                    "(e.g., E-value, quantitative bias analysis). Advanced "
                    "techniques considered where applicable (instrumental "
                    "variables, regression discontinuity, difference-in-"
                    "differences). Assumptions of the chosen method stated."
                ),
            ),
        ],
    )


def _bias_identification_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M4",
        name="Bias Identification",
        description=(
            "Does the response identify relevant biases specific to the study "
            "design, name them correctly, explain their direction, and propose "
            "mitigation strategies?"
        ),
        weight=1.5,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description="No biases mentioned or discussed.",
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Generic bias mention ('there may be bias') without "
                    "specificity or naming of bias types."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "1-2 relevant biases identified by name (e.g., selection bias, "
                    "recall bias) with basic mitigation strategies."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "3+ specific biases named using correct epidemiological "
                    "terminology (immortal time bias, protopathic bias, Neyman "
                    "bias). Direction of bias explained. Mitigation strategies "
                    "are specific and actionable."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Comprehensive bias audit covering selection, information, "
                    "and confounding biases relevant to the design. Specific "
                    "mechanisms explained. Direction and magnitude of bias "
                    "estimated. Quantitative sensitivity analysis suggested "
                    "(e.g., bias analysis, probabilistic bias analysis)."
                ),
            ),
        ],
    )


def _ethical_considerations_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M5",
        name="Ethical Considerations",
        description=(
            "Does the response address ethical aspects of the proposed research, "
            "including Declaration of Helsinki principles, IRB requirements, "
            "and participant protections?"
        ),
        weight=0.75,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description="No ethical discussion whatsoever.",
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Generic ethics statement ('get IRB approval') without "
                    "specific application to the scenario."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Declaration of Helsinki principles referenced with basic "
                    "application. Informed consent and IRB mentioned with "
                    "relevance to the study design."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Specific ethical concerns addressed: clinical equipoise "
                    "for trials, vulnerable population protections, risk-benefit "
                    "analysis, data privacy considerations."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Full ethical governance framework: Helsinki compliance, "
                    "distributive justice (fair risk/benefit distribution), "
                    "data sovereignty and consent for secondary use, "
                    "sustainability considerations, specific IRB pathway "
                    "guidance for the study type."
                ),
            ),
        ],
    )


def _reporting_standards_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M6",
        name="Reporting Standards (EQUATOR)",
        description=(
            "Does the response recommend the correct reporting guideline "
            "from the EQUATOR network for the study design?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description="No reporting guideline mentioned.",
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Incorrect guideline for the study design (e.g., recommending "
                    "CONSORT for an observational study, or PRISMA for a cohort)."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Correct guideline named (e.g., STROBE for cohort, "
                    "CONSORT for RCT, PRISMA for systematic review). "
                    "Reference to EQUATOR network."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Correct guideline with mention of specific checklist items "
                    "relevant to the scenario. Directs user to equator-network.org "
                    "for the full checklist."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Correct guideline with specific checklist items highlighted "
                    "as critical for this study. Awareness of relevant extensions "
                    "or specialized guidelines where applicable. Directs user to "
                    "authoritative sources for the full checklist. Sensitivity "
                    "analyses and flow diagram guidance included."
                ),
            ),
        ],
    )


def _explanation_quality_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M7",
        name="Explanation Quality",
        description=(
            "Is the response clear, well-structured, and appropriately pitched "
            "for the target expertise level? Does it teach concepts effectively?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Incoherent or incomprehensible. Excessive jargon without "
                    "definition. Poor structure with no logical flow."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Partially understandable but assumes advanced knowledge "
                    "inappropriately. Poor organization. Key concepts unexplained."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Clear structure with logical sections. Most concepts "
                    "explained. Appropriate for the stated expertise level. "
                    "Some room for improved clarity."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Excellent clarity. Concepts scaffolded from simple to "
                    "complex. Good use of examples. Well-organized with "
                    "headers and bullet points."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Outstanding pedagogical quality. Uses analogies for complex "
                    "concepts. Layered explanation with progressive detail. "
                    "Perfectly calibrated to expertise level (simple mode: no "
                    "jargon, practical analogies; advanced mode: precise "
                    "terminology with nuance). Concise without sacrificing "
                    "completeness."
                ),
            ),
        ],
    )


def _actionability_dimension() -> RubricDimension:
    return RubricDimension(
        dimension_id="M8",
        name="Actionability",
        description=(
            "Can the user actually implement the advice? Does the response "
            "provide specific, practical next steps?"
        ),
        weight=1.0,
        anchors=[
            ScoreAnchor(
                score=1,
                label="Poor",
                description=(
                    "Abstract theoretical discussion only. The user cannot "
                    "act on any of the advice without significant additional "
                    "research or expert consultation."
                ),
            ),
            ScoreAnchor(
                score=2,
                label="Below Average",
                description=(
                    "Some practical elements but lacks specifics. Does not "
                    "answer who, what, when, or how."
                ),
            ),
            ScoreAnchor(
                score=3,
                label="Adequate",
                description=(
                    "Clear next steps provided. User could begin implementing "
                    "with moderate effort. Includes what data to collect and "
                    "general analysis approach."
                ),
            ),
            ScoreAnchor(
                score=4,
                label="Good",
                description=(
                    "Specific implementable protocol outline with variables, "
                    "data sources, inclusion/exclusion criteria, and timeline. "
                    "User can start writing a protocol."
                ),
            ),
            ScoreAnchor(
                score=5,
                label="Excellent",
                description=(
                    "Complete implementation roadmap: sample frame definition, "
                    "recruitment strategy, data collection instruments, "
                    "statistical analysis plan outline, and feasibility "
                    "considerations (budget, timeline, personnel)."
                ),
            ),
        ],
    )


METHODOLOGY_RUBRIC = build_methodology_rubric()
