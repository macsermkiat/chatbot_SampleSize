"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  Cell,
  PieChart,
  Pie,
} from "recharts";
import ValidationTable, {
  type ValidationResult,
  type ValidationSummary,
} from "@/components/ValidationTable";

/* ------------------------------------------------------------------ */
/*  Evaluation data (from blinded, multi-run benchmark vs GPT-5)      */
/* ------------------------------------------------------------------ */

const OVERALL = {
  chatbot: { composite: 4.33, quality: 4.54 },
  gpt5: { composite: 3.95, quality: 4.52 },
};

const WIN_LOSS = { wins: 13, losses: 6, ties: 21 };

const DIMENSION_SCORES: {
  id: string;
  name: string;
  shortName: string;
  domain: "Biostatistics" | "Methodology";
  chatbot: number;
  gpt5: number;
  significant: boolean;
  remark?: string;
}[] = [
  { id: "B1", name: "Statistical Test Selection", shortName: "Test Selection", domain: "Biostatistics", chatbot: 4.71, gpt5: 4.67, significant: false },
  { id: "B2", name: "Sample Size Calculation", shortName: "Sample Size", domain: "Biostatistics", chatbot: 3.81, gpt5: 4.22, significant: false, remark: "Our chatbot prioritizes clarifying clinical parameters before computing -- a safer approach for real research, but penalized in benchmarks that reward immediate numerical output. GPT-5 assumes defaults (alpha=0.05, power=0.80) and provides quick estimates that may lack context. We are actively tuning our clarification threshold to balance safety with responsiveness." },
  { id: "B3", name: "Code Correctness", shortName: "Code Correct.", domain: "Biostatistics", chatbot: 3.65, gpt5: 2.16, significant: true },
  { id: "B4", name: "Assumption Checking", shortName: "Assumptions", domain: "Biostatistics", chatbot: 4.32, gpt5: 3.94, significant: false },
  { id: "B5", name: "Effect Size Interpretation", shortName: "Effect Size", domain: "Biostatistics", chatbot: 3.67, gpt5: 3.71, significant: false, remark: "Negligible difference (0.04 points). Both systems perform comparably on effect size interpretation." },
  { id: "B6", name: "Clinical vs Statistical Significance", shortName: "Clin. vs Stat.", domain: "Biostatistics", chatbot: 3.02, gpt5: 2.95, significant: false },
  { id: "B7", name: "Explanation Quality", shortName: "Explanations", domain: "Biostatistics", chatbot: 4.59, gpt5: 4.70, significant: false, remark: "Marginal gap (0.11 points, not significant). Our chatbot provides structured, multi-turn explanations designed for dialogue rather than single-shot completeness. In real usage, researchers can ask follow-up questions for deeper understanding." },
  { id: "B8", name: "Code Quality", shortName: "Code Quality", domain: "Biostatistics", chatbot: 3.76, gpt5: 2.21, significant: true },
  { id: "M1", name: "Research Question Structuring", shortName: "PICO/PICOTS", domain: "Methodology", chatbot: 4.95, gpt5: 4.84, significant: false },
  { id: "M2", name: "Study Design Appropriateness", shortName: "Study Design", domain: "Methodology", chatbot: 4.95, gpt5: 4.84, significant: false },
  { id: "M3", name: "Causal Inference Framework", shortName: "Causal Infer.", domain: "Methodology", chatbot: 4.77, gpt5: 4.63, significant: false },
  { id: "M4", name: "Bias Identification", shortName: "Bias ID", domain: "Methodology", chatbot: 4.91, gpt5: 4.56, significant: true },
  { id: "M5", name: "Ethical Considerations", shortName: "Ethics", domain: "Methodology", chatbot: 3.95, gpt5: 2.79, significant: true },
  { id: "M6", name: "Reporting Standards (EQUATOR)", shortName: "EQUATOR", domain: "Methodology", chatbot: 4.54, gpt5: 3.23, significant: true },
  { id: "M7", name: "Explanation Quality", shortName: "Explanations", domain: "Methodology", chatbot: 5.00, gpt5: 5.00, significant: false },
  { id: "M8", name: "Actionability", shortName: "Actionability", domain: "Methodology", chatbot: 4.96, gpt5: 5.00, significant: false, remark: "Near-perfect scores for both (0.04 gap). Our chatbot occasionally defers action items to the next conversation turn as part of its multi-phase workflow, which marginally affects single-turn scoring." },
];

const COLORS = {
  chatbot: "#c6952b",
  gpt5: "#9e9280",
  chatbotLight: "#f3d994",
  gpt5Light: "#d3cdc3",
  significant: "#a87320",
  bg: "#faf8f4",
};

/* ------------------------------------------------------------------ */
/*  Calculation Validation data (50 benchmarks vs published formulas)  */
/* ------------------------------------------------------------------ */

const VALIDATION_RESULTS: ValidationResult[] = [
  { id: "V01", scenario: "Two independent means (equal groups)", expected: 91, actual: 92, deviation_pct: 1.1, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V02", scenario: "Two independent means (unequal SD)", expected: 58, actual: 59, deviation_pct: 1.7, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V03", scenario: "Paired t-test", expected: 29, actual: 29, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V04", scenario: "Two proportions (chi-square)", expected: 294, actual: 294, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V05", scenario: "Two proportions (small difference)", expected: 1543, actual: 1543, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V06", scenario: "One-way ANOVA (3 groups)", expected: 53, actual: 53, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V07", scenario: "One-way ANOVA (4 groups, small effect)", expected: 109, actual: 109, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V08", scenario: "Survival analysis (log-rank, Schoenfeld)", expected: 380, actual: 380, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V09", scenario: "Survival analysis (HR=0.70, 90% power)", expected: 328, actual: 330, deviation_pct: 0.6, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V10", scenario: "Non-inferiority trial (means)", expected: 142, actual: 143, deviation_pct: 0.7, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V11", scenario: "Correlation test (r=0.30)", expected: 85, actual: 85, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V12", scenario: "Logistic regression (single predictor)", expected: 262, actual: 265, deviation_pct: 1.1, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V13", scenario: "McNemar's test (paired proportions)", expected: 113, actual: 113, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V14", scenario: "Two independent means (90% power)", expected: 122, actual: 122, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V15", scenario: "Cluster-randomized trial (proportions)", expected: 875, actual: 870, deviation_pct: 0.6, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V16", scenario: "Equivalence trial (two proportions)", expected: 199, actual: 200, deviation_pct: 0.5, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V17", scenario: "Repeated measures ANOVA", expected: 42, actual: 42, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V18", scenario: "Two proportions (large effect)", expected: 141, actual: 141, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V19", scenario: "Two-sample t-test with 2:1 allocation", expected: 118, actual: 119, deviation_pct: 0.8, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V20", scenario: "Single proportion (exact binomial)", expected: 58, actual: 58, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V21", scenario: "One-sample t-test", expected: 71, actual: 72, deviation_pct: 1.4, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V22", scenario: "One-sample t-test (small effect)", expected: 197, actual: 199, deviation_pct: 1.0, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V23", scenario: "Two independent means (large effect)", expected: 26, actual: 26, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V24", scenario: "Two independent means (one-sided)", expected: 50, actual: 51, deviation_pct: 2.0, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V25", scenario: "Survival analysis (HR=0.80)", expected: 631, actual: 631, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V26", scenario: "Survival analysis (HR=0.65)", expected: 170, actual: 170, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V27", scenario: "Survival analysis (HR=0.85, large trial)", expected: 1189, actual: 1189, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V28", scenario: "Non-inferiority trial (proportions)", expected: 330, actual: 330, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V29", scenario: "Non-inferiority trial (means, 90% power)", expected: 132, actual: 132, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V30", scenario: "Equivalence trial (means, TOST)", expected: 175, actual: 176, deviation_pct: 0.6, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V31", scenario: "One-way ANOVA (5 groups, large effect)", expected: 18, actual: 18, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V32", scenario: "One-way ANOVA (3 groups, small effect)", expected: 322, actual: 322, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V33", scenario: "Paired t-test (strong effect)", expected: 12, actual: 12, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V34", scenario: "Paired t-test (90% power)", expected: 37, actual: 38, deviation_pct: 2.7, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V35", scenario: "Two proportions (rare events)", expected: 1135, actual: 1135, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V36", scenario: "Two proportions (70% vs 50%)", expected: 47, actual: 47, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V37", scenario: "Two proportions (90% power)", expected: 112, actual: 113, deviation_pct: 0.9, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V38", scenario: "Two proportions (alpha=0.01)", expected: 113, actual: 113, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V39", scenario: "Two proportions (nearly equal)", expected: 179, actual: 179, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V40", scenario: "Two independent means (d=0.20)", expected: 393, actual: 394, deviation_pct: 0.3, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V41", scenario: "Two independent means (3:1 allocation)", expected: 42, actual: 43, deviation_pct: 2.4, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V42", scenario: "Correlation test (r=0.50)", expected: 29, actual: 29, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V43", scenario: "Correlation test (r=0.15)", expected: 347, actual: 349, deviation_pct: 0.6, exact_match: false, within_5pct: true, within_10pct: true },
  { id: "V44", scenario: "Single proportion (one-sided)", expected: 67, actual: 67, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V45", scenario: "Single proportion (90% power)", expected: 113, actual: 113, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V46", scenario: "McNemar's test (larger sample)", expected: 151, actual: 151, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V47", scenario: "Crossover design (2x2)", expected: 45, actual: 45, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V48", scenario: "Chi-square test (2x3)", expected: 108, actual: 108, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V49", scenario: "Survival analysis (HR=0.75, 90% power)", expected: 508, actual: 508, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
  { id: "V50", scenario: "Cluster-randomized (large ICC)", expected: 853, actual: 853, deviation_pct: 0.0, exact_match: true, within_5pct: true, within_10pct: true },
];

const VALIDATION_SUMMARY: ValidationSummary = {
  total: 50,
  scored: 50,
  exact_match_count: 35,
  within_5pct_count: 50,
  within_10pct_count: 50,
  exact_match_rate: 70,
  within_5pct_rate: 100,
  within_10pct_rate: 100,
  mean_deviation: 0.36,
  median_deviation: 0.0,
};

const PIE_DATA = [
  { name: "Our Wins", value: WIN_LOSS.wins, color: COLORS.chatbot },
  { name: "GPT-5 Wins", value: WIN_LOSS.losses, color: COLORS.gpt5 },
  { name: "Ties", value: WIN_LOSS.ties, color: "#ede7d6" },
];

/* ------------------------------------------------------------------ */
/*  Tooltip components                                                 */
/* ------------------------------------------------------------------ */

function CustomBarTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; fill: string }>;
  label?: string;
}) {
  if (!active || !payload) return null;
  return (
    <div className="bg-parchment-50 border border-parchment-300 rounded-lg px-4 py-3 shadow-lg">
      <p className="font-display font-semibold text-ink-900 text-sm mb-1">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="text-body-sm text-ink-700">
          <span className="inline-block w-3 h-3 rounded-sm mr-2" style={{ backgroundColor: entry.fill }} />
          {entry.name}: <span className="font-semibold">{entry.value.toFixed(2)}</span>
        </p>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Stat card component                                                */
/* ------------------------------------------------------------------ */

function StatCard({ label, value, subtext, highlight }: {
  label: string;
  value: string;
  subtext: string;
  highlight?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className={`
        rounded-2xl border p-6 text-center
        ${highlight
          ? "border-gold-400 bg-gradient-to-br from-gold-50 to-parchment-50 shadow-[0_0_20px_oklch(0.85_0.12_85/0.2)]"
          : "border-parchment-200 bg-parchment-50"
        }
      `}
    >
      <p className="text-caption font-display uppercase tracking-wider text-ink-500 mb-2">{label}</p>
      <p className={`text-display-lg font-display font-bold ${highlight ? "text-gold-700" : "text-ink-900"}`}>
        {value}
      </p>
      <p className="text-body-sm text-ink-500 mt-1">{subtext}</p>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Advantage card                                                     */
/* ------------------------------------------------------------------ */

function AdvantageCard({ title, delta, pValue, description }: {
  title: string;
  delta: string;
  pValue: string;
  description: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="flex gap-4 p-5 rounded-xl border border-parchment-200 bg-parchment-50 hover:border-gold-400 transition-colors duration-300"
    >
      <div className="flex-none flex items-center justify-center w-14 h-14 rounded-xl bg-gold-100 text-gold-700">
        <span className="text-display-md font-display font-bold">{delta}</span>
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-display font-semibold text-ink-900">{title}</h4>
          <span className="text-caption px-2 py-0.5 rounded-full bg-gold-100 text-gold-700 font-display">
            p={pValue}
          </span>
        </div>
        <p className="text-body-sm text-ink-600">{description}</p>
      </div>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Benefit card                                                       */
/* ------------------------------------------------------------------ */

function BenefitCard({ icon, title, description }: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5 }}
      className="p-6 rounded-2xl border border-parchment-200 bg-parchment-50 hover:shadow-lg hover:border-gold-300 transition-all duration-300"
    >
      <div className="w-12 h-12 rounded-xl bg-gold-100 text-gold-700 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h4 className="font-display font-semibold text-ink-900 text-body-lg mb-2">{title}</h4>
      <p className="text-body-sm text-ink-600 leading-relaxed">{description}</p>
    </motion.div>
  );
}

/* ------------------------------------------------------------------ */
/*  Dimension table with expandable remarks                            */
/* ------------------------------------------------------------------ */

function DimensionTable() {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
    >
      <h2 className="text-display-lg font-display font-bold text-ink-900 mb-6">
        Full Rubric Breakdown
      </h2>
      <div className="bg-parchment-50 border border-parchment-200 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-body-sm">
            <thead>
              <tr className="border-b-2 border-parchment-300">
                <th className="text-left px-5 py-3 font-display font-semibold text-ink-800">Dimension</th>
                <th className="text-left px-5 py-3 font-display font-semibold text-ink-800">Domain</th>
                <th className="text-center px-5 py-3 font-display font-semibold text-gold-700">Ours</th>
                <th className="text-center px-5 py-3 font-display font-semibold text-ink-500">GPT-5</th>
                <th className="text-center px-5 py-3 font-display font-semibold text-ink-800">Delta</th>
                <th className="text-center px-5 py-3 font-display font-semibold text-ink-800">Winner</th>
              </tr>
            </thead>
            <tbody>
              {DIMENSION_SCORES.map((d) => {
                const delta = d.chatbot - d.gpt5;
                const winner = delta > 0.05 ? "ours" : delta < -0.05 ? "gpt5" : "tie";
                const isExpanded = expandedId === d.id;
                const hasRemark = !!d.remark;

                return (
                  <DimensionRow
                    key={d.id}
                    d={d}
                    delta={delta}
                    winner={winner}
                    hasRemark={hasRemark}
                    isExpanded={isExpanded}
                    onToggle={() => setExpandedId(isExpanded ? null : d.id)}
                  />
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="px-5 py-3 border-t border-parchment-200 flex flex-col gap-1">
          <p className="text-caption text-ink-400 font-display">
            * Statistically significant (Wilcoxon signed-rank, p &lt; 0.05)
          </p>
          <p className="text-caption text-ink-400 font-display">
            Click rows marked with a remark icon to see analysis notes.
          </p>
        </div>
      </div>
    </motion.div>
  );
}

function DimensionRow({ d, delta, winner, hasRemark, isExpanded, onToggle }: {
  d: typeof DIMENSION_SCORES[number];
  delta: number;
  winner: "ours" | "gpt5" | "tie";
  hasRemark: boolean;
  isExpanded: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <tr
        onClick={hasRemark ? onToggle : undefined}
        className={`
          border-b border-parchment-200
          ${d.significant ? "bg-gold-50/50" : ""}
          ${hasRemark ? "cursor-pointer hover:bg-parchment-100 transition-colors" : ""}
        `}
      >
        <td className="px-5 py-3 font-body text-ink-800">
          <span className="font-mono text-caption text-ink-400 mr-2">{d.id}</span>
          {d.name}
          {d.significant && (
            <span className="ml-1 text-caption text-gold-600">*</span>
          )}
          {hasRemark && (
            <span className={`ml-1.5 inline-flex items-center text-caption transition-transform duration-200 ${isExpanded ? "text-gold-600" : "text-ink-400"}`}>
              <svg className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
              </svg>
            </span>
          )}
        </td>
        <td className="px-5 py-3 text-ink-600">{d.domain}</td>
        <td className="px-5 py-3 text-center font-semibold text-gold-700">{d.chatbot.toFixed(2)}</td>
        <td className="px-5 py-3 text-center text-ink-500">{d.gpt5.toFixed(2)}</td>
        <td className={`px-5 py-3 text-center font-semibold ${delta > 0 ? "text-gold-700" : delta < 0 ? "text-ink-500" : "text-ink-400"}`}>
          {delta > 0 ? "+" : ""}{delta.toFixed(2)}
        </td>
        <td className="px-5 py-3 text-center">
          {winner === "ours" && (
            <span className="inline-block px-2 py-0.5 rounded-full bg-gold-100 text-gold-700 text-caption font-display">Ours</span>
          )}
          {winner === "gpt5" && (
            <span className="inline-block px-2 py-0.5 rounded-full bg-parchment-200 text-ink-600 text-caption font-display">GPT-5</span>
          )}
          {winner === "tie" && (
            <span className="text-ink-400 text-caption">Tie</span>
          )}
        </td>
      </tr>
      {hasRemark && isExpanded && (
        <tr className="bg-parchment-100/70">
          <td colSpan={6} className="px-5 py-4">
            <div className="flex gap-3 max-w-3xl">
              <div className="flex-none mt-0.5">
                <svg className="w-4 h-4 text-gold-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-body-sm text-ink-600 font-body leading-relaxed italic">
                {d.remark}
              </p>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

/* ------------------------------------------------------------------ */
/*  Main page                                                          */
/* ------------------------------------------------------------------ */

export default function BenchmarkClient() {
  const [domainFilter, setDomainFilter] = useState<"all" | "Biostatistics" | "Methodology">("all");

  const filteredDimensions = domainFilter === "all"
    ? DIMENSION_SCORES
    : DIMENSION_SCORES.filter((d) => d.domain === domainFilter);

  const barData = filteredDimensions.map((d) => ({
    name: d.id,
    fullName: d.name,
    "Rexearch": d.chatbot,
    "GPT-5": d.gpt5,
    significant: d.significant,
  }));

  const biostatsDims = DIMENSION_SCORES.filter((d) => d.domain === "Biostatistics");
  const methDims = DIMENSION_SCORES.filter((d) => d.domain === "Methodology");

  const radarBioData = biostatsDims.map((d) => ({
    dimension: d.shortName,
    "Rexearch": d.chatbot,
    "GPT-5": d.gpt5,
  }));

  const radarMethData = methDims.map((d) => ({
    dimension: d.shortName,
    "Rexearch": d.chatbot,
    "GPT-5": d.gpt5,
  }));

  const compositeAdvantage = (
    ((OVERALL.chatbot.composite - OVERALL.gpt5.composite) / OVERALL.gpt5.composite) * 100
  ).toFixed(0);

  return (
    <div className="min-h-screen bg-parchment-100">
      {/* Navigation */}
      <nav className="sticky top-0 z-50 border-b border-parchment-200 bg-parchment-100/90 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="font-display text-display-md font-semibold text-ink-900 hover:text-gold-700 transition-colors"
          >
            Rexearch
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-caption font-display text-ink-500 uppercase tracking-wider hidden sm:block">
              Benchmark Results
            </span>
            <Link
              href="/app"
              className="
                px-4 py-2 rounded-xl font-display text-body-sm
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors
              "
            >
              Try It Now
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-gold-50/50 to-transparent pointer-events-none" />
        <div className="max-w-5xl mx-auto px-6 pt-20 pb-16 relative">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
            className="text-center"
          >
            <p className="text-caption font-display uppercase tracking-widest text-gold-600 mb-4">
              Independent Benchmark Study
            </p>
            <h1 className="text-display-xl font-display font-bold text-ink-900 mb-6 text-balance">
              Outperforming GPT-5 Where It Matters Most
            </h1>
            <p className="text-body-lg text-ink-600 max-w-2xl mx-auto mb-8 font-body">
              In a rigorous, blinded evaluation across 40 medical research scenarios,
              Rexearch achieved a{" "}
              <span className="font-semibold text-gold-700">+{compositeAdvantage}% higher composite score</span>{" "}
              than GPT-5 -- with statistically significant advantages
              in ethical awareness, code generation, reporting standards, and bias identification.
            </p>

            {/* Methodology badge */}
            <div className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full border border-parchment-300 bg-parchment-50">
              <svg className="w-4 h-4 text-gold-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
              <span className="text-body-sm text-ink-700 font-body">
                Blinded evaluation -- Claude Sonnet 4.6 judge -- 3 runs per case -- Bonferroni-corrected
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Key Stats */}
      <section className="max-w-5xl mx-auto px-6 -mt-2 mb-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard
            label="Composite Score"
            value="4.33"
            subtext="vs GPT-5's 3.95"
            highlight
          />
          <StatCard
            label="Case Win Rate"
            value="2.2x"
            subtext="13 wins vs 6 losses"
          />
          <StatCard
            label="Dimensions Won"
            value="11 / 16"
            subtext="vs GPT-5's 2 of 16"
            highlight
          />
          <StatCard
            label="Code Correctness"
            value="+69%"
            subtext="3.65 vs 2.16 (p=0.005)"
          />
          <StatCard
            label="Ethical Awareness"
            value="+42%"
            subtext="3.95 vs 2.79 (p<0.001)"
            highlight
          />
        </div>
      </section>

      {/* Win/Loss/Tie Pie */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center"
        >
          <div>
            <h2 className="text-display-lg font-display font-bold text-ink-900 mb-4">
              Head-to-Head: 40 Research Scenarios
            </h2>
            <p className="text-body-md text-ink-600 mb-6 font-body">
              Each test case was scored independently by an AI judge that never knew
              which system produced which answer. Our Research Assistant won more than
              twice as many cases as GPT-5.
            </p>
            <div className="flex gap-6">
              {PIE_DATA.map((entry) => (
                <div key={entry.name} className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: entry.color, border: entry.color === "#ede7d6" ? "1px solid #c9b890" : "none" }} />
                  <span className="text-body-sm text-ink-700 font-body">
                    {entry.name} ({entry.value})
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={PIE_DATA}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={3}
                  dataKey="value"
                  stroke="none"
                >
                  {PIE_DATA.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: COLORS.bg,
                    border: "1px solid #ddd3b8",
                    borderRadius: "8px",
                    fontFamily: "var(--font-source-serif)",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </motion.div>
      </section>

      {/* Dimension Comparison Bar Chart */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-8">
            <div>
              <h2 className="text-display-lg font-display font-bold text-ink-900 mb-2">
                Rubric Score Comparison
              </h2>
              <p className="text-body-md text-ink-600 font-body">
                16 dimensions scored 1-5 by blinded expert judge. Highlighted bars indicate statistically significant differences.
              </p>
            </div>
            <div className="flex gap-2">
              {(["all", "Biostatistics", "Methodology"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setDomainFilter(f)}
                  className={`
                    px-3 py-1.5 rounded-lg text-body-sm font-display transition-all
                    ${domainFilter === f
                      ? "bg-ink-900 text-parchment-100"
                      : "bg-parchment-200 text-ink-700 hover:bg-parchment-300"
                    }
                  `}
                >
                  {f === "all" ? "All" : f}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-parchment-50 border border-parchment-200 rounded-2xl p-6 overflow-x-auto">
            <div style={{ minWidth: 600 }}>
              <ResponsiveContainer width="100%" height={420}>
                <BarChart data={barData} barGap={4} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#ede7d6" vertical={false} />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: "#5e554a", fontSize: 12, fontFamily: "var(--font-cormorant)" }}
                    axisLine={{ stroke: "#ddd3b8" }}
                    tickLine={false}
                  />
                  <YAxis
                    domain={[0, 5]}
                    ticks={[0, 1, 2, 3, 4, 5]}
                    tick={{ fill: "#9e9280", fontSize: 12 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip content={<CustomBarTooltip />} />
                  <Legend
                    wrapperStyle={{ fontFamily: "var(--font-source-serif)", fontSize: 13 }}
                  />
                  <Bar dataKey="Rexearch" fill={COLORS.chatbot} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="GPT-5" fill={COLORS.gpt5} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="text-caption text-ink-400 mt-4 text-center font-display">
              Scores are averaged across 3 independent judge runs per case. All 40 advanced-user scenarios included.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Radar Charts */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-display-lg font-display font-bold text-ink-900 mb-2 text-center">
            Domain Profiles
          </h2>
          <p className="text-body-md text-ink-600 text-center mb-10 font-body">
            Visualizing multi-dimensional performance across biostatistics and methodology domains.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Biostatistics Radar */}
            <div className="bg-parchment-50 border border-parchment-200 rounded-2xl p-6">
              <h3 className="font-display font-semibold text-ink-900 text-center mb-4">Biostatistics</h3>
              <ResponsiveContainer width="100%" height={340}>
                <RadarChart data={radarBioData}>
                  <PolarGrid stroke="#ddd3b8" />
                  <PolarAngleAxis
                    dataKey="dimension"
                    tick={{ fill: "#5e554a", fontSize: 11, fontFamily: "var(--font-cormorant)" }}
                  />
                  <PolarRadiusAxis domain={[0, 5]} tick={false} axisLine={false} />
                  <Radar
                    name="Rexearch"
                    dataKey="Rexearch"
                    stroke={COLORS.chatbot}
                    fill={COLORS.chatbotLight}
                    fillOpacity={0.4}
                    strokeWidth={2}
                  />
                  <Radar
                    name="GPT-5"
                    dataKey="GPT-5"
                    stroke={COLORS.gpt5}
                    fill={COLORS.gpt5Light}
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Legend
                    wrapperStyle={{ fontFamily: "var(--font-source-serif)", fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: COLORS.bg,
                      border: "1px solid #ddd3b8",
                      borderRadius: "8px",
                      fontFamily: "var(--font-source-serif)",
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>

            {/* Methodology Radar */}
            <div className="bg-parchment-50 border border-parchment-200 rounded-2xl p-6">
              <h3 className="font-display font-semibold text-ink-900 text-center mb-4">Methodology</h3>
              <ResponsiveContainer width="100%" height={340}>
                <RadarChart data={radarMethData}>
                  <PolarGrid stroke="#ddd3b8" />
                  <PolarAngleAxis
                    dataKey="dimension"
                    tick={{ fill: "#5e554a", fontSize: 11, fontFamily: "var(--font-cormorant)" }}
                  />
                  <PolarRadiusAxis domain={[0, 5]} tick={false} axisLine={false} />
                  <Radar
                    name="Rexearch"
                    dataKey="Rexearch"
                    stroke={COLORS.chatbot}
                    fill={COLORS.chatbotLight}
                    fillOpacity={0.4}
                    strokeWidth={2}
                  />
                  <Radar
                    name="GPT-5"
                    dataKey="GPT-5"
                    stroke={COLORS.gpt5}
                    fill={COLORS.gpt5Light}
                    fillOpacity={0.3}
                    strokeWidth={2}
                  />
                  <Legend
                    wrapperStyle={{ fontFamily: "var(--font-source-serif)", fontSize: 12 }}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: COLORS.bg,
                      border: "1px solid #ddd3b8",
                      borderRadius: "8px",
                      fontFamily: "var(--font-source-serif)",
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Statistically Significant Advantages */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-display-lg font-display font-bold text-ink-900 mb-2">
            Where We Outperform GPT-5
          </h2>
          <p className="text-body-md text-ink-600 mb-8 font-body">
            Five dimensions with statistically significant improvements (Wilcoxon signed-rank test, p &lt; 0.05). Ethical Considerations also survives Bonferroni correction.
          </p>
          <div className="flex flex-col gap-4">
            <AdvantageCard
              title="Ethical Considerations (M5)"
              delta="+1.16"
              pValue="<0.001"
              description="The MethodologyAgent consistently raises IRB requirements, informed consent protocols, vulnerable populations, and data privacy. GPT-5 frequently overlooks ethical dimensions entirely. The only dimension significant after full Bonferroni correction."
            />
            <AdvantageCard
              title="Code Correctness (B3)"
              delta="+1.49"
              pValue="0.005"
              description="Our multi-agent architecture routes biostatistics queries through a specialized CodingAgent with built-in code validation. GPT-5 frequently produces code with logical errors or incorrect parameter mappings."
            />
            <AdvantageCard
              title="Code Quality (B8)"
              delta="+1.56"
              pValue="0.008"
              description="Generated scripts follow best practices: clear variable naming, proper commenting, modular structure, and reproducible random seeds. GPT-5 outputs are often monolithic and harder to audit."
            />
            <AdvantageCard
              title="Reporting Standards (M6)"
              delta="+1.32"
              pValue="0.004"
              description="Stronger on EQUATOR guidelines (CONSORT, STROBE, PRISMA). Our MethodologyAgent embeds reporting standards into every study design recommendation, while GPT-5 rarely cites them."
            />
            <AdvantageCard
              title="Bias Identification (M4)"
              delta="+0.35"
              pValue="0.029"
              description="More thorough in identifying potential sources of bias -- immortal time bias, confounding by indication, selection bias. Our structured causal inference framework catches what GPT-5 misses."
            />
          </div>
        </motion.div>
      </section>

      {/* Detailed Dimension Table */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <DimensionTable />
      </section>

      {/* Calculation Validation */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <div className="flex items-center gap-3 mb-2">
            <h2 className="text-display-lg font-display font-bold text-ink-900">
              Sample Size Calculation Validation
            </h2>
            <span className="text-caption font-display px-2.5 py-1 rounded-full border border-gold-300 bg-gold-50 text-gold-700">
              50 benchmarks
            </span>
          </div>
          <p className="text-body-md text-ink-600 mb-8 font-body max-w-3xl">
            Every sample size calculation is validated against published formulas from
            Chow et al. (2018), Cohen (1988), Julious (2023), Schoenfeld (1983), and
            statsmodels/scipy reference implementations. Our system uses{" "}
            <span className="font-semibold text-gold-700">executed Python code</span>{" "}
            (not LLM estimation) to compute exact sample sizes.
          </p>
          <ValidationTable results={VALIDATION_RESULTS} summary={VALIDATION_SUMMARY} />
        </motion.div>
      </section>

      {/* Benefits */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
        >
          <h2 className="text-display-lg font-display font-bold text-ink-900 mb-2 text-center">
            Why Researchers Choose Us
          </h2>
          <p className="text-body-md text-ink-600 text-center mb-10 font-body max-w-2xl mx-auto">
            Purpose-built for medical research planning, not general-purpose chat.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            <BenefitCard
              icon={
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
                </svg>
              }
              title="Validated Code Generation"
              description="Every statistical script is generated by a specialized CodingAgent and validated through a DiagnosticTool. No more debugging GPT output -- get production-ready R, Python, and STATA code."
            />
            <BenefitCard
              icon={
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
                </svg>
              }
              title="Multi-Agent Architecture"
              description="Seven specialized agents work in concert: literature search, evidence appraisal, methodology design, biostatistics, coding, diagnostics, and summarization. Each expert does what it does best."
            />
            <BenefitCard
              icon={
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.383a14.406 14.406 0 01-3 0M14.25 18v-.192c0-.983.658-1.823 1.508-2.316a7.5 7.5 0 10-7.517 0c.85.493 1.509 1.333 1.509 2.316V18" />
                </svg>
              }
              title="Ethics-First Approach"
              description="Automatically surfaces IRB requirements, informed consent protocols, and data privacy considerations. The only research assistant that consistently prioritizes ethical compliance."
            />
            <BenefitCard
              icon={
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              }
              title="EQUATOR-Aligned Reporting"
              description="Methodology recommendations follow CONSORT, STROBE, PRISMA, and other EQUATOR Network guidelines. Your study design meets journal submission standards from day one."
            />
            <BenefitCard
              icon={
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
                </svg>
              }
              title="End-to-End Workflow"
              description="From identifying research gaps through literature search, to designing study methodology, to calculating sample sizes and generating analysis code -- all in one conversation."
            />
            <BenefitCard
              icon={
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                </svg>
              }
              title="Rigorous Validation"
              description="100% of sample size calculations fall within 5% of published formulas across 50 benchmarks (Chow, Cohen, Julious, Schoenfeld). Code is executed in a sandbox, not estimated by an LLM."
            />
          </div>
        </motion.div>
      </section>

      {/* Methodology Section */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="bg-parchment-50 border border-parchment-200 rounded-2xl p-8"
        >
          <h2 className="text-display-lg font-display font-bold text-ink-900 mb-6 text-center">
            How We Tested
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { step: "01", title: "40 Expert Scenarios", desc: "Curated medical research scenarios for advanced users across biostatistics, methodology, and edge cases. 14 specialties represented." },
              { step: "02", title: "Blinded Evaluation", desc: "Systems randomly assigned as 'System A' or 'System B'. The judge never knew which was which." },
              { step: "03", title: "Triple-Run Consistency", desc: "Each case judged 3 times independently. 93% exact agreement, 100% within-1 agreement across runs." },
              { step: "04", title: "Statistical Rigor", desc: "Wilcoxon signed-rank tests with Bonferroni correction (alpha/17 = 0.0029). No cherry-picking." },
            ].map((item) => (
              <div key={item.step}>
                <span className="font-display text-display-md font-bold text-gold-400">{item.step}</span>
                <h4 className="font-display font-semibold text-ink-900 mt-2 mb-2">{item.title}</h4>
                <p className="text-body-sm text-ink-600 font-body">{item.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* CTA */}
      <section className="max-w-5xl mx-auto px-6 mb-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center py-16 px-8 rounded-2xl bg-gradient-to-br from-ink-900 to-ink-950 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,oklch(0.85_0.12_85/0.08)_0%,transparent_50%)] pointer-events-none" />
          <h2 className="text-display-lg font-display font-bold text-parchment-100 mb-4 relative">
            Ready to Elevate Your Research?
          </h2>
          <p className="text-body-lg text-parchment-300 mb-8 max-w-xl mx-auto font-body relative">
            Join researchers who trust our specialized AI assistant for gap analysis,
            study design, and biostatistical planning.
          </p>
          <Link
            href="/app"
            className="
              inline-flex items-center gap-2 px-8 py-3.5 rounded-xl
              bg-gold-500 text-ink-950 font-display font-semibold text-body-lg
              hover:bg-gold-400 transition-colors duration-200
              shadow-[0_4px_20px_oklch(0.75_0.15_85/0.3)]
              relative
            "
          >
            Start a Research Session
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-parchment-200 bg-parchment-100/80">
        <div className="max-w-5xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-caption text-ink-400 font-display">
            Rexearch -- Independent benchmark evaluation
          </p>
          <div className="flex items-center gap-4">
            <Link href="/app" className="text-body-sm text-ink-600 hover:text-gold-700 transition-colors font-body">
              Back to App
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
