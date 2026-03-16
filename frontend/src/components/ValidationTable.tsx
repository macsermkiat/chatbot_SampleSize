"use client";

import { useState } from "react";
import { motion } from "framer-motion";

export interface ValidationResult {
  id: string;
  scenario: string;
  expected: number;
  actual: number | null;
  deviation_pct: number;
  exact_match: boolean;
  within_5pct: boolean;
  within_10pct: boolean;
}

export interface ValidationSummary {
  total: number;
  scored: number;
  exact_match_count: number;
  within_5pct_count: number;
  within_10pct_count: number;
  exact_match_rate: number;
  within_5pct_rate: number;
  within_10pct_rate: number;
  mean_deviation: number;
  median_deviation: number;
}

interface Props {
  results: ValidationResult[];
  summary: ValidationSummary;
}

const CATEGORY_MAP: Record<string, string> = {
  two_sample_t: "t-test",
  one_sample_t: "t-test",
  paired_t: "t-test",
  proportions: "Proportions",
  anova: "ANOVA",
  survival: "Survival",
  correlation: "Correlation",
  non_inferiority: "NI/Equiv",
  equivalence: "NI/Equiv",
  cluster: "Cluster",
  mcnemar: "Paired prop",
  logistic: "Regression",
  crossover: "Crossover",
  chi_square: "Chi-square",
  repeated: "Repeated",
  single_prop: "Proportions",
};

function getCategoryForId(id: string, scenario: string): string {
  const lower = scenario.toLowerCase();
  if (lower.includes("survival")) return "Survival";
  if (lower.includes("anova") || lower.includes("one-way")) return "ANOVA";
  if (lower.includes("cluster")) return "Cluster";
  if (lower.includes("non-inferiority")) return "NI/Equiv";
  if (lower.includes("equivalence")) return "NI/Equiv";
  if (lower.includes("correlation")) return "Correlation";
  if (lower.includes("mcnemar")) return "Paired prop";
  if (lower.includes("crossover")) return "Crossover";
  if (lower.includes("chi-square")) return "Chi-square";
  if (lower.includes("logistic")) return "Regression";
  if (lower.includes("repeated")) return "Repeated";
  if (lower.includes("paired")) return "t-test";
  if (lower.includes("one-sample")) return "t-test";
  if (lower.includes("proportion") || lower.includes("single proportion")) return "Proportions";
  if (lower.includes("t-test") || lower.includes("means")) return "t-test";
  return "Other";
}

export default function ValidationTable({ results, summary }: Props) {
  const [showAll, setShowAll] = useState(false);
  const displayResults = showAll ? results : results.slice(0, 20);

  return (
    <div>
      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
        <SummaryStat
          label="Exact Match"
          value={`${summary.exact_match_rate.toFixed(0)}%`}
          detail={`${summary.exact_match_count}/${summary.scored}`}
        />
        <SummaryStat
          label="Within 5%"
          value={`${summary.within_5pct_rate.toFixed(0)}%`}
          detail={`${summary.within_5pct_count}/${summary.scored}`}
          highlight
        />
        <SummaryStat
          label="Within 10%"
          value={`${summary.within_10pct_rate.toFixed(0)}%`}
          detail={`${summary.within_10pct_count}/${summary.scored}`}
        />
        <SummaryStat
          label="Mean Deviation"
          value={`${summary.mean_deviation.toFixed(1)}%`}
          detail={`median ${summary.median_deviation.toFixed(1)}%`}
        />
      </div>

      {/* Results table */}
      <div className="bg-parchment-50 border border-parchment-200 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-body-sm">
            <thead>
              <tr className="border-b-2 border-parchment-300">
                <th className="text-left px-4 py-3 font-display font-semibold text-ink-800">ID</th>
                <th className="text-left px-4 py-3 font-display font-semibold text-ink-800">Scenario</th>
                <th className="text-left px-4 py-3 font-display font-semibold text-ink-800">Category</th>
                <th className="text-right px-4 py-3 font-display font-semibold text-ink-800">Expected</th>
                <th className="text-right px-4 py-3 font-display font-semibold text-ink-800">Computed</th>
                <th className="text-right px-4 py-3 font-display font-semibold text-ink-800">Dev %</th>
                <th className="text-center px-4 py-3 font-display font-semibold text-ink-800">Result</th>
              </tr>
            </thead>
            <tbody>
              {displayResults.map((r) => (
                <tr key={r.id} className="border-b border-parchment-200 hover:bg-parchment-100/50 transition-colors">
                  <td className="px-4 py-2.5 font-mono text-caption text-ink-500">{r.id}</td>
                  <td className="px-4 py-2.5 text-ink-700 max-w-[200px] truncate" title={r.scenario}>
                    {r.scenario}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-caption px-2 py-0.5 rounded-full bg-parchment-100 text-ink-500 font-display">
                      {getCategoryForId(r.id, r.scenario)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-ink-700">
                    {r.expected.toLocaleString()}
                  </td>
                  <td className="px-4 py-2.5 text-right font-mono text-ink-700">
                    {r.actual !== null ? r.actual.toLocaleString() : "--"}
                  </td>
                  <td className={`px-4 py-2.5 text-right font-mono ${
                    r.actual === null ? "text-ink-400" :
                    r.exact_match ? "text-green-700" :
                    r.within_5pct ? "text-gold-700" :
                    r.within_10pct ? "text-orange-600" :
                    "text-red-600"
                  }`}>
                    {r.actual !== null ? `${r.deviation_pct.toFixed(1)}%` : "--"}
                  </td>
                  <td className="px-4 py-2.5 text-center">
                    {r.actual === null ? (
                      <span className="text-caption text-ink-400">--</span>
                    ) : r.exact_match ? (
                      <span className="inline-block px-2 py-0.5 rounded-full bg-green-100 text-green-700 text-caption font-display">
                        Exact
                      </span>
                    ) : r.within_5pct ? (
                      <span className="inline-block px-2 py-0.5 rounded-full bg-gold-100 text-gold-700 text-caption font-display">
                        5%
                      </span>
                    ) : r.within_10pct ? (
                      <span className="inline-block px-2 py-0.5 rounded-full bg-orange-100 text-orange-700 text-caption font-display">
                        10%
                      </span>
                    ) : (
                      <span className="inline-block px-2 py-0.5 rounded-full bg-red-100 text-red-600 text-caption font-display">
                        Out
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {results.length > 20 && (
          <div className="px-4 py-3 border-t border-parchment-200 text-center">
            <button
              onClick={() => setShowAll(!showAll)}
              className="text-body-sm text-gold-700 hover:text-gold-600 font-display transition-colors"
            >
              {showAll ? "Show fewer" : `Show all ${results.length} benchmarks`}
            </button>
          </div>
        )}

        <div className="px-4 py-3 border-t border-parchment-200">
          <p className="text-caption text-ink-400 font-display">
            Expected values from Chow et al. (2018), Cohen (1988), Julious (2023), Schoenfeld (1983), and statsmodels/scipy reference implementations.
          </p>
        </div>
      </div>
    </div>
  );
}

function SummaryStat({ label, value, detail, highlight }: {
  label: string;
  value: string;
  detail: string;
  highlight?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className={`
        rounded-xl border p-4 text-center
        ${highlight
          ? "border-gold-400 bg-gold-50"
          : "border-parchment-200 bg-parchment-50"
        }
      `}
    >
      <p className="text-caption font-display uppercase tracking-wider text-ink-500 mb-1">{label}</p>
      <p className={`text-display-md font-display font-bold ${highlight ? "text-gold-700" : "text-ink-900"}`}>
        {value}
      </p>
      <p className="text-caption text-ink-400 mt-0.5">{detail}</p>
    </motion.div>
  );
}
