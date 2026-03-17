export interface BlogPost {
  readonly slug: string;
  readonly title: string;
  readonly description: string;
  readonly date: string;
  readonly readingTime: string;
  readonly category: string;
  readonly content: string;
}

export const BLOG_POSTS: readonly BlogPost[] = [
  {
    slug: "sample-size-pitfalls-researchers-overlook",
    title: "5 Sample Size Pitfalls That Trip Up Even Experienced Researchers",
    description:
      "Power analysis is deceptively simple in theory. In practice, subtle mistakes in effect size estimation, dropout assumptions, and multiplicity adjustments can invalidate your entire study before enrollment begins.",
    date: "2026-03-15",
    readingTime: "6 min read",
    category: "Biostatistics",
    content: `
Sample size calculation sits at the foundation of every clinical study. Get it wrong, and you either waste resources on an overpowered trial or -- worse -- publish an underpowered study that misses a real effect. Despite decades of methodological guidance, the same mistakes keep appearing in grant applications and protocols.

Here are five pitfalls we see repeatedly, and how to avoid them.

## 1. Using a "Convenient" Effect Size

The most common error is choosing an effect size because it produces a feasible sample size, rather than because it reflects a clinically meaningful difference. A researcher aiming for n=50 per group might back-calculate an effect size of d=0.8, then justify it post hoc.

**The fix:** Start from the Minimal Clinically Important Difference (MCID) for your outcome measure. If no MCID exists, use pilot data or systematic reviews of similar interventions. If the required sample size is infeasible, that is valuable information -- it means you need a different design, not a different effect size.

## 2. Ignoring Dropout and Non-Compliance

A power calculation that assumes 100% retention is fiction. Longitudinal studies routinely lose 15-30% of participants, and intention-to-treat analysis with imputed data does not recover the lost statistical power.

**The fix:** Inflate your sample size by the expected attrition rate. If you expect 20% dropout, divide your calculated n by 0.80. Better yet, model dropout as informative rather than random, and consider how differential dropout between arms could bias your results.

## 3. Forgetting Multiplicity Adjustments

Testing three co-primary endpoints without adjusting alpha inflates your family-wise error rate to roughly 14% instead of the intended 5%. Reviewers and regulatory bodies will catch this, but often only after the study is complete.

**The fix:** Decide your multiplicity strategy before calculating sample size. Bonferroni is conservative but straightforward. Hierarchical testing preserves alpha without inflating sample size if you can rank your endpoints by clinical importance. The choice of adjustment method directly affects the required n -- build it into your power calculation from the start.

## 4. Misspecifying the Statistical Test

Using a t-test power calculation when your analysis plan calls for a mixed-effects model, or calculating power for a log-rank test when you plan to use Cox regression with covariates, leads to sample sizes that are either too small or wastefully large.

**The fix:** Your power calculation should mirror your planned primary analysis as closely as possible. If you plan to adjust for baseline covariates in an ANCOVA, use an ANCOVA-based power calculation -- the variance reduction from covariates typically lowers the required n by 20-30%. Simulation-based power analysis is invaluable when closed-form solutions do not match your analysis plan.

## 5. Treating Sample Size as a One-Time Calculation

Assumptions change. Interim data may reveal that your variance estimate was wrong, your control group event rate was off, or your dropout rate is higher than expected. A fixed sample size calculated once at the protocol stage cannot adapt to these realities.

**The fix:** Consider adaptive designs that allow sample size re-estimation at a pre-specified interim analysis. Group sequential designs, in particular, can let you stop early for efficacy or futility while maintaining the overall type I error rate. Even without a formal adaptive design, planning a blinded sample size re-estimation based on pooled variance can save a study from being underpowered.

## The Broader Pattern

These pitfalls share a common root: treating sample size calculation as a bureaucratic checkbox rather than a modeling exercise. Power analysis is a prediction about how your study will behave under specific assumptions. The quality of those assumptions determines whether your study succeeds or fails.

Tools like G*Power and PASS handle the arithmetic, but they cannot tell you whether your inputs are reasonable. That is where domain expertise -- and increasingly, AI-assisted methodology review -- becomes essential. An AI system that understands both the statistical framework and the clinical context can flag unrealistic assumptions before they become expensive mistakes.

At ProtoCol, our biostatistics phase walks researchers through each assumption, challenges questionable inputs, and generates the code to verify calculations independently. The goal is not to replace statistical thinking, but to make sure it happens rigorously every time.
    `,
  },
  {
    slug: "research-question-to-protocol-three-phases",
    title: "From Research Question to Study Protocol: Why Three Phases Matter",
    description:
      "Most research planning tools solve one piece of the puzzle. A systematic three-phase approach -- gap analysis, methodology design, biostatistical planning -- produces stronger protocols and catches problems early.",
    date: "2026-03-10",
    readingTime: "5 min read",
    category: "Research Methodology",
    content: `
Research planning is not a single activity. It is a sequence of decisions, each building on the last, where a mistake in an early phase compounds through everything that follows. Yet most researchers approach it as a collection of disconnected tasks: search the literature here, sketch a study design there, run a power calculation somewhere else.

This fragmentation leads to protocols that do not hold together -- a research gap that does not quite match the study design, or a statistical plan that cannot answer the research question as framed. The three-phase approach addresses this by treating research planning as a pipeline where each phase's output becomes the next phase's input.

## Phase 1: Research Gap Analysis

Before designing a study, you need to know precisely what is and is not known. This sounds obvious, but "I could not find any studies on X" is not the same as a systematic gap analysis.

A rigorous gap analysis involves structured literature search with multiple query strategies, classification of the type of gap (evidence, methodology, population, context, or theoretical), and a framework like PICO or PICOTS to define the question precisely.

The output of this phase is not just a list of papers. It is a clear statement of what evidence exists, where it falls short, and why a new study is justified. This framing directly shapes the next phase.

**What goes wrong without it:** Researchers design studies that duplicate existing evidence, address a gap that has already been filled by recent publications, or frame their question so broadly that no single study could answer it.

## Phase 2: Study Methodology Design

With a well-defined gap, the methodology phase asks: what study design would generate the evidence needed to fill this gap?

This involves more than choosing between "RCT" and "cohort study." Rigorous methodology design includes selecting the appropriate study type and justifying why alternatives are inferior, constructing a causal model (often a DAG) to identify confounders and mediators, planning for bias through tools like the Cochrane Risk of Bias framework, and selecting the right reporting guideline (CONSORT, STROBE, PRISMA, etc.) from the EQUATOR network.

One particularly powerful technique gaining traction is Target Trial Emulation, where observational studies are designed to mirror the structure of an ideal randomized trial. This forces researchers to make explicit decisions about eligibility criteria, treatment strategies, and outcome definitions that might otherwise remain vague.

**What goes wrong without it:** Studies with unmeasured confounding that invalidates the results, designs that cannot answer the research question as stated, or protocols that do not meet the reporting standards expected by target journals.

## Phase 3: Biostatistical Planning

The statistical plan is where the methodology becomes concrete and testable. This phase translates the study design into specific hypotheses, determines the appropriate statistical tests, calculates the required sample size, and produces analysis code.

Good biostatistical planning is iterative. The initial power calculation might reveal that the study is infeasible as designed, sending you back to Phase 2 to consider a different design or a more focused population. The choice of statistical test might depend on distributional assumptions that need to be verified with pilot data.

This phase also produces artifacts that reviewers and ethics boards require: the statistical analysis plan (SAP), sample size justification with all assumptions stated, and often R or STATA code that demonstrates the planned analyses.

**What goes wrong without it:** Underpowered studies, inappropriate statistical tests, analysis plans that do not match the study design, and the all-too-common post hoc rationalization of unexpected results.

## Why the Phases Must Connect

The three-phase structure is not just organizational convenience. Each transition is a quality gate.

The gap analysis constrains the methodology: you cannot design a study to fill a gap you have not rigorously defined. The methodology constrains the statistics: your power calculation must match your planned analysis, which must match your study design, which must address the identified gap.

When these phases are disconnected -- different tools, different consultants, different months -- the connections weaken. Assumptions made in Phase 1 get lost by Phase 3. The result is a protocol that looks complete on paper but contains internal contradictions that reviewers will find.

## The Case for AI-Assisted Planning

AI cannot replace the domain expertise that drives research planning. But it can do something that human consultants struggle with: maintain perfect consistency across all three phases while checking each decision against established methodological frameworks.

When a researcher tells an AI system that they are studying a rare disease with an expected prevalence of 0.1%, the system can immediately flag that a standard RCT sample size calculation will produce infeasible numbers and suggest alternative designs. When the gap analysis identifies a population subgroup, the methodology phase can automatically consider that subgroup in the design, and the statistics phase can plan the appropriate subgroup analyses.

This is not about replacing methodological thinking. It is about providing a structured environment where that thinking happens more rigorously, more consistently, and earlier in the process -- when changes are cheap rather than expensive.
    `,
  },
] as const;

export function getPostBySlug(slug: string): BlogPost | undefined {
  return BLOG_POSTS.find((post) => post.slug === slug);
}
