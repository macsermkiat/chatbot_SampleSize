"use client";

import { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import FloatingParticles from "@/components/FloatingParticles";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.12 } },
};

const FEATURES = [
  {
    title: "Research Gap Analysis",
    description:
      "Systematically identify knowledge gaps across your field with AI-powered literature search and evidence appraisal.",
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <circle cx="11" cy="11" r="8" />
        <path d="M21 21l-4.35-4.35" />
        <path d="M8 11h6M11 8v6" />
      </svg>
    ),
  },
  {
    title: "Study Methodology Design",
    description:
      "Get expert guidance on study design, including Target Trial Emulation, DAG confounding analysis, and EQUATOR reporting.",
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
        <rect x="9" y="3" width="6" height="4" rx="1" />
        <path d="M9 14l2 2 4-4" />
      </svg>
    ),
  },
  {
    title: "Biostatistical Analysis",
    description:
      "Power analysis, sample size calculation, and statistical test selection with generated R/Python/STATA code.",
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M3 3v18h18" />
        <path d="M7 16l4-8 4 4 5-10" />
      </svg>
    ),
  },
  {
    title: "Protocol Export",
    description:
      "Export your complete research protocol as a formatted DOCX or PDF document with citations, ready for IRB submission.",
    icon: (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
];

const COMPARISONS = [
  { name: "nQuery", price: "$925 - $7,495/yr", ai: false },
  { name: "PASS", price: "$1,095 - $2,995/yr", ai: false },
  { name: "G*Power", price: "Free", ai: false },
  { name: "ProtoCol", price: "From $0/mo", ai: true },
];

export default function LandingClient() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="min-h-screen bg-parchment-100">
      {/* Navigation */}
      <nav className="border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-display text-display-md font-semibold text-ink-900 tracking-tight">
            ProtoCol
          </Link>

          {/* Desktop nav */}
          <div className="hidden sm:flex items-center gap-6">
            <Link href="/pricing" className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body">
              Pricing
            </Link>
            <Link href="/benchmark" className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body">
              Benchmark
            </Link>
            <Link href="/blog" className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body">
              Blog
            </Link>
            <Link
              href="/login"
              className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body"
            >
              Sign In
            </Link>
            <Link
              href="/app"
              className="
                text-body-sm font-body font-medium px-4 py-2 rounded-lg
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors
              "
            >
              Open App
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center gap-3 sm:hidden">
            <Link
              href="/app"
              className="
                text-body-sm font-body font-medium px-3.5 py-1.5 rounded-lg
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors
              "
            >
              Open App
            </Link>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              className="w-10 h-10 flex items-center justify-center rounded-lg text-ink-700 hover:bg-parchment-200 transition-colors"
            >
              <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                {menuOpen ? (
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                ) : (
                  <path fillRule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clipRule="evenodd" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile dropdown */}
        <AnimatePresence>
          {menuOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="sm:hidden overflow-hidden border-t border-parchment-200"
            >
              <div className="px-6 py-3 flex flex-col gap-1">
                {[
                  { href: "/pricing", label: "Pricing" },
                  { href: "/benchmark", label: "Benchmark" },
                  { href: "/blog", label: "Blog" },
                  { href: "/login", label: "Sign In" },
                ].map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMenuOpen(false)}
                    className="text-body-sm text-ink-600 hover:text-ink-900 font-body py-2 transition-colors"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </nav>

      {/* Hero */}
      <motion.section
        className="relative py-24 px-6 overflow-hidden"
        initial="initial"
        animate="animate"
        variants={stagger}
      >
        <FloatingParticles count={20} />
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-caption text-gold-600 font-display tracking-wider uppercase mb-4"
          >
            AI-Powered Research Methodology
          </motion.p>

          <motion.h1
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="font-display text-display-xl font-semibold text-ink-900 mb-6 text-balance"
          >
            From research question to study protocol, guided by AI
          </motion.h1>

          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-body-lg text-ink-600 font-body max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            ProtoCol walks you through gap analysis, study methodology design,
            and biostatistical analysis -- producing publication-ready protocols
            at a fraction of the cost of legacy statistical software.
          </motion.p>

          <motion.div
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4"
          >
            <Link
              href="/app"
              className="
                font-body font-medium px-6 py-3 rounded-xl text-body-md
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors
                shadow-sm w-full sm:w-auto text-center
              "
            >
              Start Research
            </Link>
            <Link
              href="/pricing"
              className="
                font-body font-medium px-6 py-3 rounded-xl text-body-md
                bg-parchment-50 text-ink-800 border border-parchment-300
                hover:bg-parchment-200 transition-colors w-full sm:w-auto text-center
              "
            >
              View Pricing
            </Link>
          </motion.div>

          {/* Decorative glow */}
          <div
            className="
              absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2
              w-96 h-96 rounded-full
              bg-[radial-gradient(circle,oklch(0.88_0.14_85/0.2)_0%,transparent_70%)]
              pointer-events-none -z-10
            "
          />
        </div>
      </motion.section>

      {/* Divider */}
      <div className="max-w-xs mx-auto">
        <div className="divider">Three Phases</div>
      </div>

      {/* Features */}
      <motion.section
        className="py-20 px-6"
        initial="initial"
        whileInView="animate"
        viewport={{ once: true, margin: "-100px" }}
        variants={stagger}
      >
        <div className="max-w-5xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {FEATURES.map((feature) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                transition={{ duration: 0.4 }}
                className="
                  bg-white/60 backdrop-blur-sm border border-parchment-200
                  rounded-xl p-6 hover:border-gold-300
                  transition-colors duration-200
                "
              >
                <div className="w-10 h-10 rounded-lg bg-gold-50 border border-gold-200 flex items-center justify-center text-gold-700 mb-4">
                  {feature.icon}
                </div>
                <h3 className="font-display text-display-md font-semibold text-ink-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-body-sm text-ink-600 font-body leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Comparison */}
      <section className="py-20 px-6 bg-parchment-50/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 text-center mb-3">
            95% cheaper than legacy tools
          </h2>
          <p className="text-body-md text-ink-500 font-body text-center mb-10">
            Traditional statistical software charges thousands per year with no AI guidance.
          </p>

          <div className="bg-white/80 backdrop-blur-sm border border-parchment-200 rounded-xl overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-parchment-200">
                  <th className="text-left px-4 sm:px-6 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    Tool
                  </th>
                  <th className="text-left px-4 sm:px-6 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    Price
                  </th>
                  <th className="text-center px-4 sm:px-6 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    AI
                  </th>
                </tr>
              </thead>
              <tbody>
                {COMPARISONS.map((item) => (
                  <tr
                    key={item.name}
                    className={`border-b border-parchment-100 last:border-b-0 ${
                      item.ai ? "bg-gold-50/50" : ""
                    }`}
                  >
                    <td className="px-4 sm:px-6 py-3 text-body-sm font-body text-ink-800 font-medium">
                      {item.name}
                    </td>
                    <td className="px-4 sm:px-6 py-3 text-body-sm font-body text-ink-600">
                      {item.price}
                    </td>
                    <td className="px-4 sm:px-6 py-3 text-center">
                      {item.ai ? (
                        <span className="inline-flex items-center gap-1 text-body-sm text-green-700 font-medium">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                          Yes
                        </span>
                      ) : (
                        <span className="text-body-sm text-ink-400">No</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 mb-4">
            Ready to streamline your research?
          </h2>
          <p className="text-body-md text-ink-500 font-body mb-8">
            Start with 5 free queries per month. No credit card required.
          </p>
          <Link
            href="/app"
            className="
              inline-block font-body font-medium px-8 py-3.5 rounded-xl text-body-md
              bg-ink-900 text-parchment-100
              hover:bg-ink-800 transition-colors
              shadow-sm
            "
          >
            Get Started Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-parchment-200 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-caption text-ink-400 font-display">
            ProtoCol -- AI-powered research methodology
          </p>
          <div className="flex items-center gap-6">
            <Link href="/pricing" className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display">
              Pricing
            </Link>
            <Link href="/blog" className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display">
              Blog
            </Link>
            <Link href="/login" className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display">
              Sign In
            </Link>
            <Link href="/app" className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display">
              App
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
