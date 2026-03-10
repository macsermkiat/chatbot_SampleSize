"""Generate publication-quality reports from evaluation results."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from evaluation.analysis.comparison import ComparisonReport, PairedComparison
from evaluation.analysis.descriptive import SystemSummary
from evaluation.llm_judge.calibration import CalibrationReport, ConsistencyMetrics


@dataclass(frozen=True)
class ReportConfig:
    """Configuration for report generation."""

    output_dir: str = "evaluation/output/reports"
    include_latex: bool = True
    include_markdown: bool = True
    decimal_places: int = 2


def generate_full_report(
    chatbot_summary: SystemSummary,
    gpt5_summary: SystemSummary,
    comparison: ComparisonReport,
    consistency_metrics: list[ConsistencyMetrics],
    calibration: CalibrationReport | None,
    config: ReportConfig | None = None,
) -> str:
    """Generate the full Markdown report.

    Returns the complete report as a string.
    """
    cfg = config or ReportConfig()
    dp = cfg.decimal_places

    sections = [
        _header(),
        _executive_summary(chatbot_summary, gpt5_summary, comparison, dp),
        _methodology_section(),
        _descriptive_table(chatbot_summary, gpt5_summary, dp),
        _comparison_table(comparison, dp),
        _judge_quality_section(consistency_metrics, calibration, dp),
        _key_findings(comparison, dp),
        _limitations(),
    ]

    report = "\n\n".join(sections)

    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "evaluation_report.md").write_text(report)

    if cfg.include_latex:
        latex = _generate_latex_tables(
            chatbot_summary, gpt5_summary, comparison, dp
        )
        (out_dir / "tables.tex").write_text(latex)

    return report


def _header() -> str:
    return """\
# Evaluation Report: Medical Research Chatbot vs GPT-5

**Study Design:** Blinded paired comparison with LLM-as-judge evaluation
**Methodology:** Wilcoxon signed-rank test with Bonferroni correction
**Judge:** Claude (Anthropic) to avoid OpenAI self-preference bias"""


def _executive_summary(
    chatbot: SystemSummary,
    gpt5: SystemSummary,
    comparison: ComparisonReport,
    dp: int,
) -> str:
    oc = comparison.overall_comparison
    favors_text = {
        "chatbot": "the specialized chatbot",
        "gpt5": "GPT-5",
        "tie": "neither system",
    }

    return f"""\
## Executive Summary

| Metric | Chatbot | GPT-5 |
|--------|---------|-------|
| Cases Evaluated | {chatbot.n_cases} | {gpt5.n_cases} |
| Mean Overall Quality | {chatbot.mean_overall_quality:.{dp}f} | {gpt5.mean_overall_quality:.{dp}f} |
| Mean Composite Score | {chatbot.mean_composite:.{dp}f} | {gpt5.mean_composite:.{dp}f} |

**Overall comparison:** {favors_text.get(oc.favors, "inconclusive")} \
(p={oc.p_value:.4f}, r={oc.effect_size_r:.{dp}f} [{oc.effect_size_label}])

**Significant dimensions** (Bonferroni-adjusted): \
{comparison.n_significant_adjusted}/{comparison.total_dimensions}"""


def _methodology_section() -> str:
    return """\
## Methodology

### Study Design
- 50 standardized clinical research scenarios (20 methodology, 20 biostatistics, 10 edge cases)
- Each scenario sent to both systems under identical conditions
- GPT-5 tested without system prompt or tools (vanilla baseline)
- Responses blinded and randomly labeled "System A" / "System B"

### Evaluation
- 16 rubric dimensions (8 methodology + 8 biostatistics), each scored 1-5
- LLM judge (Claude) scored each response 3 times for consistency
- Automated checks: statistical test correctness, code execution, PICO completeness

### Statistical Analysis
- Wilcoxon signed-rank test for paired ordinal comparisons
- Bonferroni correction for multiple comparisons (alpha/17)
- Effect size: rank-biserial correlation (r = Z/sqrt(N))
- McNemar's test for binary outcomes (code correctness, test selection)"""


def _descriptive_table(
    chatbot: SystemSummary,
    gpt5: SystemSummary,
    dp: int,
) -> str:
    lines = [
        "## Descriptive Statistics",
        "",
        "| Dimension | Chatbot Mean (SD) | GPT-5 Mean (SD) | Chatbot Median | GPT-5 Median |",
        "|-----------|-------------------|-----------------|----------------|--------------|",
    ]

    chatbot_dims = {d.dimension_id: d for d in chatbot.dimension_summaries}
    gpt5_dims = {d.dimension_id: d for d in gpt5.dimension_summaries}

    all_dims = sorted(set(chatbot_dims.keys()) | set(gpt5_dims.keys()))

    for dim_id in all_dims:
        cd = chatbot_dims.get(dim_id)
        gd = gpt5_dims.get(dim_id)
        c_mean = f"{cd.mean:.{dp}f} ({cd.sd:.{dp}f})" if cd else "N/A"
        g_mean = f"{gd.mean:.{dp}f} ({gd.sd:.{dp}f})" if gd else "N/A"
        c_med = f"{cd.median:.1f}" if cd else "N/A"
        g_med = f"{gd.median:.1f}" if gd else "N/A"
        lines.append(f"| {dim_id} | {c_mean} | {g_mean} | {c_med} | {g_med} |")

    return "\n".join(lines)


def _comparison_table(comparison: ComparisonReport, dp: int) -> str:
    lines = [
        "## Paired Comparisons (Wilcoxon Signed-Rank)",
        "",
        f"**Alpha:** {comparison.alpha} | "
        f"**Bonferroni-adjusted alpha:** {comparison.bonferroni_alpha:.4f}",
        "",
        "| Dimension | N | Diff | W | p-value | p-adj | r | Effect | Favors | Sig |",
        "|-----------|---|------|---|---------|-------|---|--------|--------|-----|",
    ]

    all_comps = [*comparison.dimension_comparisons, comparison.overall_comparison]
    for c in all_comps:
        sig_marker = "***" if c.significant_adjusted else ("*" if c.significant_raw else "")
        lines.append(
            f"| {c.dimension_id} | {c.n_pairs} | "
            f"{c.mean_difference:+.{dp}f} | "
            f"{c.wilcoxon_statistic:.1f} | "
            f"{_format_p(c.p_value)} | "
            f"{_format_p(c.p_value_adjusted)} | "
            f"{c.effect_size_r:.{dp}f} | "
            f"{c.effect_size_label} | "
            f"{c.favors} | {sig_marker} |"
        )

    lines.append("")
    lines.append("*p < 0.05, ***p < Bonferroni-adjusted alpha")

    return "\n".join(lines)


def _judge_quality_section(
    consistency: list[ConsistencyMetrics],
    calibration: CalibrationReport | None,
    dp: int,
) -> str:
    lines = ["## LLM Judge Quality Metrics", ""]

    # Consistency table
    lines.append("### Self-Consistency (3 runs per case)")
    lines.append("")
    lines.append("| Dimension | N Comparisons | Exact Agreement | Within-1 Agreement |")
    lines.append("|-----------|---------------|-----------------|-------------------|")

    for m in consistency:
        lines.append(
            f"| {m.dimension_id} | {m.total_comparisons} | "
            f"{m.exact_agreement_rate:.{dp}f} | {m.within_one_rate:.{dp}f} |"
        )

    if consistency:
        avg_exact = sum(m.exact_agreement_rate for m in consistency) / len(consistency)
        avg_within = sum(m.within_one_rate for m in consistency) / len(consistency)
        lines.append(f"| **Average** | | **{avg_exact:.{dp}f}** | **{avg_within:.{dp}f}** |")

    # Calibration results
    if calibration:
        lines.append("")
        lines.append("### Gold Standard Calibration")
        lines.append(f"- Cases evaluated: {calibration.total_cases}")
        lines.append(f"- Exact match rate: {calibration.exact_match_rate:.{dp}f}")
        lines.append(f"- Within-1 match rate: {calibration.within_one_rate:.{dp}f}")
        status = "PASSED" if calibration.passed else "FAILED"
        lines.append(f"- Calibration status: **{status}**")

    return "\n".join(lines)


def _key_findings(comparison: ComparisonReport, dp: int) -> str:
    lines = ["## Key Findings", ""]

    # Dimensions where chatbot significantly outperforms
    chatbot_wins = [
        c for c in comparison.dimension_comparisons
        if c.significant_adjusted and c.favors == "chatbot"
    ]
    gpt5_wins = [
        c for c in comparison.dimension_comparisons
        if c.significant_adjusted and c.favors == "gpt5"
    ]

    if chatbot_wins:
        lines.append("### Chatbot Advantages (statistically significant after correction)")
        for c in chatbot_wins:
            lines.append(
                f"- **{c.dimension_id}**: +{c.mean_difference:.{dp}f} points "
                f"(p={_format_p(c.p_value_adjusted)}, r={c.effect_size_r:.{dp}f})"
            )
        lines.append("")

    if gpt5_wins:
        lines.append("### GPT-5 Advantages (statistically significant after correction)")
        for c in gpt5_wins:
            lines.append(
                f"- **{c.dimension_id}**: {c.mean_difference:.{dp}f} points "
                f"(p={_format_p(c.p_value_adjusted)}, r={c.effect_size_r:.{dp}f})"
            )
        lines.append("")

    if not chatbot_wins and not gpt5_wins:
        lines.append(
            "No statistically significant differences after Bonferroni correction."
        )

    return "\n".join(lines)


def _limitations() -> str:
    return """\
## Limitations

1. **LLM-as-judge**: Potential biases in automated evaluation; human validation recommended
2. **Synthetic scenarios**: Test cases may not capture full clinical complexity
3. **Single comparison model**: Results specific to GPT-5; other models may differ
4. **Temperature variability**: Judge consistency may vary across dimensions
5. **No real user testing**: Evaluation does not measure actual clinical workflow impact"""


def _format_p(p: float) -> str:
    """Format p-value for display."""
    if p < 0.001:
        return "<0.001"
    if p < 0.01:
        return f"{p:.3f}"
    return f"{p:.4f}"


def _generate_latex_tables(
    chatbot: SystemSummary,
    gpt5: SystemSummary,
    comparison: ComparisonReport,
    dp: int,
) -> str:
    """Generate LaTeX table fragments for publication."""
    lines = [
        "% Descriptive Statistics Table",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Descriptive statistics by evaluation dimension}",
        "\\label{tab:descriptive}",
        "\\begin{tabular}{lcccc}",
        "\\toprule",
        "Dimension & Chatbot M (SD) & GPT-5 M (SD) & Chatbot Mdn & GPT-5 Mdn \\\\",
        "\\midrule",
    ]

    chatbot_dims = {d.dimension_id: d for d in chatbot.dimension_summaries}
    gpt5_dims = {d.dimension_id: d for d in gpt5.dimension_summaries}

    for dim_id in sorted(set(chatbot_dims.keys()) | set(gpt5_dims.keys())):
        cd = chatbot_dims.get(dim_id)
        gd = gpt5_dims.get(dim_id)
        c_str = f"{cd.mean:.{dp}f} ({cd.sd:.{dp}f})" if cd else "--"
        g_str = f"{gd.mean:.{dp}f} ({gd.sd:.{dp}f})" if gd else "--"
        c_med = f"{cd.median:.1f}" if cd else "--"
        g_med = f"{gd.median:.1f}" if gd else "--"
        lines.append(f"{dim_id} & {c_str} & {g_str} & {c_med} & {g_med} \\\\")

    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "% Comparison Table",
        "\\begin{table}[htbp]",
        "\\centering",
        "\\caption{Paired comparisons (Wilcoxon signed-rank test)}",
        "\\label{tab:comparison}",
        "\\begin{tabular}{lcccccl}",
        "\\toprule",
        "Dimension & N & $\\Delta$ & W & p & p\\textsubscript{adj} & r \\\\",
        "\\midrule",
    ])

    all_comps = [*comparison.dimension_comparisons, comparison.overall_comparison]
    for c in all_comps:
        sig = "$^{***}$" if c.significant_adjusted else (
            "$^{*}$" if c.significant_raw else ""
        )
        lines.append(
            f"{c.dimension_id} & {c.n_pairs} & "
            f"{c.mean_difference:+.{dp}f} & "
            f"{c.wilcoxon_statistic:.1f} & "
            f"{_format_p(c.p_value)} & "
            f"{_format_p(c.p_value_adjusted)} & "
            f"{c.effect_size_r:.{dp}f}{sig} \\\\"
        )

    lines.extend([
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
    ])

    return "\n".join(lines)
