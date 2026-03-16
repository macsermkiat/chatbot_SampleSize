"""Generate natural language prompts from validation benchmark parameters.

Each benchmark has structured parameters (test_type, alpha, power, etc.).
This module converts them into the kind of question a researcher would ask.
"""

from __future__ import annotations

from typing import Any


def generate_prompt(benchmark_id: str, params: dict[str, Any]) -> str:
    """Convert benchmark parameters into a natural language research question.

    Returns a prompt suitable for sending to the chatbot's biostatistics agent.
    """
    test_type = params.get("test_type", "")
    generator = _GENERATORS.get(test_type)
    if generator is None:
        return _generic_prompt(benchmark_id, params)
    return generator(params)


def _two_sample_t(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"
    ratio = p.get("allocation_ratio", 1.0)

    if "effect_size_d" in p:
        effect = f"Cohen's d = {p['effect_size_d']}"
    elif "mean_difference" in p and "sd" in p:
        effect = f"mean difference of {p['mean_difference']} with SD = {p['sd']}"
    else:
        effect = "the specified effect size"

    if "sd_group1" in p:
        effect += f" (Group 1 SD = {p['sd_group1']}, Group 2 SD = {p['sd_group2']})"

    alloc = ""
    if ratio != 1.0:
        alloc = f" Use a {ratio:.0f}:1 allocation ratio (treatment:control)."

    return (
        f"I need to calculate the sample size for a two-sample t-test. "
        f"Parameters: {effect}, alpha = {p['alpha']}, power = {p['power']}, "
        f"{sides} test.{alloc} "
        f"How many participants do I need per group?"
    )


def _one_sample_t(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"

    if "mean_h0" in p:
        effect = (
            f"null hypothesis mean = {p['mean_h0']}, "
            f"expected mean = {p['mean_h1']}, SD = {p['sd']}"
        )
    elif "effect_size_d" in p:
        effect = f"Cohen's d = {p['effect_size_d']}"
    else:
        effect = f"mean difference = {p.get('mean_difference', '?')}, SD = {p.get('sd', '?')}"

    return (
        f"I need a sample size for a one-sample t-test. "
        f"Parameters: {effect}, alpha = {p['alpha']}, power = {p['power']}, "
        f"{sides} test. How many participants?"
    )


def _paired_t(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"
    return (
        f"Calculate sample size for a paired t-test. "
        f"Expected mean difference = {p['mean_difference']}, "
        f"SD of differences = {p['sd_difference']}, "
        f"alpha = {p['alpha']}, power = {p['power']}, {sides} test. "
        f"How many pairs do I need?"
    )


def _two_proportions(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"
    return (
        f"I need the sample size to compare two proportions: "
        f"group 1 = {p['p1']*100:.0f}% vs group 2 = {p['p2']*100:.0f}%. "
        f"Alpha = {p['alpha']}, power = {p['power']}, {sides} test. "
        f"How many per group?"
    )


def _single_proportion(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"
    return (
        f"Calculate sample size for a single proportion test. "
        f"Null proportion = {p['p0']*100:.0f}%, expected = {p['p1']*100:.0f}%, "
        f"alpha = {p['alpha']}, power = {p['power']}, {sides} test. "
        f"How many participants?"
    )


def _anova(p: dict[str, Any]) -> str:
    return (
        f"I need the sample size for a one-way ANOVA with {p['num_groups']} groups. "
        f"Cohen's f = {p['effect_size_f']}, alpha = {p['alpha']}, power = {p['power']}. "
        f"How many per group?"
    )


def _survival(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"
    extra = ""
    if "median_control_months" in p:
        extra = f" Median survival in control = {p['median_control_months']} months."
    if "accrual_months" in p:
        extra += f" Accrual = {p['accrual_months']} months, follow-up = {p['followup_months']} months."
    return (
        f"Calculate the number of events needed for a survival analysis (log-rank test). "
        f"Hazard ratio = {p['hazard_ratio']}, alpha = {p['alpha']}, "
        f"power = {p['power']}, {sides} test.{extra} "
        f"How many events are required?"
    )


def _correlation(p: dict[str, Any]) -> str:
    sides = "two-sided" if p.get("sides", 2) == 2 else "one-sided"
    return (
        f"What sample size do I need to detect a correlation of r = {p['expected_r']}? "
        f"Alpha = {p['alpha']}, power = {p['power']}, {sides} test."
    )


def _non_inferiority_means(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for a non-inferiority trial comparing two means. "
        f"Non-inferiority margin = {p['non_inferiority_margin']}, SD = {p['sd']}, "
        f"true difference = {p['true_difference']}, "
        f"one-sided alpha = {p['alpha']}, power = {p['power']}. "
        f"How many per group?"
    )


def _non_inferiority_proportions(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for a non-inferiority trial comparing two proportions. "
        f"Reference rate = {p['p_reference']*100:.0f}%, test rate = {p['p_test']*100:.0f}%, "
        f"non-inferiority margin = {p['non_inferiority_margin']}, "
        f"one-sided alpha = {p['alpha']}, power = {p['power']}. "
        f"How many per group?"
    )


def _equivalence_proportions(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for an equivalence trial (TOST) comparing two proportions. "
        f"Both proportions = {p['p1']*100:.0f}%, equivalence margin = {p['equivalence_margin']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. How many per group?"
    )


def _equivalence_means(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for an equivalence trial (TOST) comparing two means. "
        f"Equivalence margin = +/-{p['equivalence_margin']}, SD = {p['sd']}, "
        f"true difference = {p['true_difference']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. How many per group?"
    )


def _logistic_regression(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for logistic regression. "
        f"Odds ratio = {p['odds_ratio']}, baseline probability = {p['baseline_probability']}, "
        f"R-squared of other predictors = {p.get('r_squared_other', 0)}, "
        f"alpha = {p['alpha']}, power = {p['power']}. "
        f"What total sample size is needed?"
    )


def _mcnemar(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for McNemar's test (paired proportions). "
        f"Discordant proportion A->B = {p['p_discordant_12']}, "
        f"B->A = {p['p_discordant_21']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. "
        f"What total sample size?"
    )


def _cluster_proportions(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for a cluster-randomized trial comparing proportions. "
        f"p1 = {p['p1']*100:.0f}%, p2 = {p['p2']*100:.0f}%, "
        f"ICC = {p['icc']}, cluster size = {p['cluster_size']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. "
        f"How many individuals per arm and how many clusters?"
    )


def _repeated_measures(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for repeated measures ANOVA. "
        f"{p['num_measurements']} time points, effect size f = {p['effect_size_f']}, "
        f"correlation among measures = {p['correlation']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. "
        f"What total sample size?"
    )


def _crossover(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for a 2x2 crossover design. "
        f"Treatment difference = {p['mean_difference']}, "
        f"within-subject SD = {p['sd_within']}, "
        f"correlation between periods = {p['correlation']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. "
        f"How many subjects total?"
    )


def _chi_square(p: dict[str, Any]) -> str:
    return (
        f"Calculate sample size for a chi-square test of independence. "
        f"Effect size w = {p['effect_size_w']}, df = {p['df']}, "
        f"alpha = {p['alpha']}, power = {p['power']}. "
        f"What total sample size?"
    )


def _generic_prompt(benchmark_id: str, params: dict[str, Any]) -> str:
    """Fallback prompt for unknown test types."""
    param_str = ", ".join(f"{k} = {v}" for k, v in params.items())
    return (
        f"Calculate the sample size for this scenario ({benchmark_id}). "
        f"Parameters: {param_str}. "
        f"Please provide the required sample size."
    )


_GENERATORS: dict[str, Any] = {
    "two_sample_t_test": _two_sample_t,
    "one_sample_t_test": _one_sample_t,
    "paired_t_test": _paired_t,
    "two_proportions": _two_proportions,
    "single_proportion": _single_proportion,
    "one_way_anova": _anova,
    "survival_log_rank": _survival,
    "correlation": _correlation,
    "non_inferiority_means": _non_inferiority_means,
    "non_inferiority_proportions": _non_inferiority_proportions,
    "equivalence_proportions": _equivalence_proportions,
    "equivalence_means": _equivalence_means,
    "logistic_regression": _logistic_regression,
    "mcnemar": _mcnemar,
    "cluster_randomized_proportions": _cluster_proportions,
    "repeated_measures_anova": _repeated_measures,
    "crossover_2x2": _crossover,
    "chi_square_independence": _chi_square,
}
