"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import Footer from "@/components/Footer";

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

const PAIN_POINTS = [
  {
    problem: "Waiting weeks for a biostatistician consultation",
    solution: "Get sample size calculations in minutes, not weeks",
  },
  {
    problem: "Guessing which statistical test fits your design",
    solution: "AI recommends the right test based on your study parameters",
  },
  {
    problem: "Reviewer comments that your methodology is weak",
    solution: "Structured methodology with EQUATOR checklist compliance",
  },
  {
    problem: "Underpowered studies that waste months of work",
    solution: "Validated power analysis with generated code you can verify",
  },
];

const COMPARISONS = [
  { name: "nQuery", price: "$925\u2013$7,495/yr", guided: false, codeGen: false, litSearch: false, highlight: false },
  { name: "PASS", price: "$1,095\u2013$2,995/yr", guided: false, codeGen: false, litSearch: false, highlight: false },
  { name: "G*Power", price: "Free", guided: false, codeGen: false, litSearch: false, highlight: false },
  { name: "ProtoCol", price: "From $0/mo", guided: true, codeGen: true, litSearch: true, highlight: true },
];

const FAQS = [
  {
    q: "Can I trust AI for sample size calculations?",
    a: "ProtoCol uses deterministic statistical formulas \u2014 the same math behind G*Power and PASS. The AI guides you through selecting the right parameters (effect size, alpha, power), then runs validated calculations. Every result includes the formula used and generated R/Python code so you can verify independently.",
  },
  {
    q: "Will this be accepted by my IRB or ethics committee?",
    a: "ProtoCol generates documentation following EQUATOR reporting guidelines (CONSORT, STROBE, PRISMA). The output is a starting point for your protocol \u2014 you review and refine it with your team before submission, just as you would with any statistical consultation.",
  },
  {
    q: "How is this different from just using ChatGPT?",
    a: "General-purpose chatbots hallucinate statistical methods and fabricate references. ProtoCol uses a structured multi-agent pipeline: separate specialized agents for literature search, methodology design, and biostatistics \u2014 each with domain-specific validation. In blinded evaluation against GPT-5, ProtoCol scored significantly higher on statistical accuracy, ethical awareness, and code generation.",
  },
  {
    q: "What study designs are supported?",
    a: "RCTs (parallel, crossover, cluster, non-inferiority, equivalence), cohort studies, case-control, cross-sectional, diagnostic accuracy, survival analysis, and more. The methodology agent handles Target Trial Emulation for observational studies and DAG-based confounding analysis.",
  },
  {
    q: "Do I need to know statistics to use this?",
    a: "No. ProtoCol adapts to your expertise level. In \"simple\" mode, it explains concepts in plain language and walks you through each decision. In \"advanced\" mode, it assumes familiarity with statistical frameworks and focuses on technical details.",
  },
];

export default function LandingClient() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data }) => {
      setIsLoggedIn(!!data.session);
    });
  }, []);

  return (
    <div className="min-h-screen bg-parchment-100">
      {/* Navigation */}
      <nav className="border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Image src="/logo_protocol.png" alt="Protocol" width={28} height={28} className="h-7 w-auto" />
            <span className="font-display text-body-md font-semibold text-ink-900 tracking-tight">Protocol</span>
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
            {isLoggedIn ? (
              <Link
                href="/app"
                className="
                  text-body-sm font-body font-medium px-4 py-2 rounded-lg
                  bg-ink-900 text-parchment-100
                  hover:bg-ink-800 transition-colors
                "
              >
                Go to App
              </Link>
            ) : (
              <>
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
                  Try Free
                </Link>
              </>
            )}
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
              {isLoggedIn ? "Go to App" : "Try Free"}
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
                  ...(isLoggedIn
                    ? [{ href: "/app", label: "Go to App" }]
                    : [{ href: "/login", label: "Sign In" }]),
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

      {/* Hero -- Core Offer */}
      <motion.section
        className="relative py-24 sm:py-32 px-6 overflow-hidden"
        initial="initial"
        animate="animate"
        variants={stagger}
      >
        {/* Subtle formula watermark reinforcing the statistics theme */}
        <div className="absolute inset-0 pointer-events-none select-none overflow-hidden" aria-hidden="true">
          <span className="absolute top-[18%] left-[8%] text-parchment-300/40 font-mono text-body-sm rotate-[-12deg]">
            n = (Z&#178; &middot; p(1-p)) / e&#178;
          </span>
          <span className="absolute top-[72%] right-[6%] text-parchment-300/30 font-mono text-caption rotate-[8deg]">
            1 &minus; &beta;
          </span>
          <span className="absolute top-[35%] right-[12%] text-parchment-300/25 font-mono text-caption rotate-[-4deg]">
            &alpha; = 0.05
          </span>
        </div>
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <motion.h1
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="font-display text-display-xl font-semibold text-ink-900 mb-6 text-balance"
          >
            Design your study methodology and calculate sample size — powered by AI
          </motion.h1>

          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-body-lg text-ink-600 font-body max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            From research question to IRB-ready protocol in one session.
            Gap analysis, methodology design, power analysis, and code generation
            — without waiting weeks for a biostatistician.
          </motion.p>

          <motion.div
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-3 sm:gap-4"
          >
            <Link
              href="/app"
              className="
                font-body font-medium px-8 py-3.5 rounded-xl text-body-md
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors
                shadow-sm w-full sm:w-auto text-center
              "
            >
              Start Your Research Plan — Free
            </Link>
          </motion.div>

          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="mt-4 text-body-sm text-ink-400 font-body"
          >
            5 free queries per month. No credit card required.
          </motion.p>

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

      {/* Pain Points */}
      <section className="py-20 px-6 bg-parchment-50/50">
        <motion.div
          className="max-w-4xl mx-auto"
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, margin: "-100px" }}
          variants={stagger}
        >
          <motion.h2
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="font-display text-display-lg font-semibold text-ink-900 text-center mb-4"
          >
            Sound familiar?
          </motion.h2>
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="text-body-md text-ink-500 font-body text-center mb-12 max-w-2xl mx-auto"
          >
            These problems cost researchers months of work and thousands in wasted funding.
          </motion.p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {PAIN_POINTS.map((item) => (
              <motion.div
                key={item.problem}
                variants={fadeUp}
                transition={{ duration: 0.4 }}
                className="bg-white border border-parchment-200 rounded-xl p-6"
              >
                <p className="text-body-md text-ink-700 font-body mb-3 flex items-start gap-2.5">
                  <span className="flex-none w-5 h-5 mt-0.5 rounded-full border border-parchment-400 flex items-center justify-center">
                    <span className="w-1.5 h-1.5 rounded-full bg-parchment-500" />
                  </span>
                  {item.problem}
                </p>
                <p className="text-body-sm text-ink-600 font-body font-medium flex items-start gap-2.5 pl-[1.875rem]">
                  <svg className="w-4 h-4 text-gold-600 flex-none mt-0.5" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 10l3 3 5-5" />
                  </svg>
                  {item.solution}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Divider */}
      <div className="max-w-xs mx-auto py-4">
        <div className="divider">How It Works</div>
      </div>

      {/* How It Works -- numbered vertical steps */}
      <motion.section
        className="py-20 px-6"
        initial="initial"
        whileInView="animate"
        viewport={{ once: true, margin: "-100px" }}
        variants={stagger}
      >
        <div className="max-w-2xl mx-auto">
          <div className="space-y-0">
            {FEATURES.map((feature, i) => (
              <motion.div
                key={feature.title}
                variants={fadeUp}
                transition={{ duration: 0.4 }}
                className="relative flex gap-5 sm:gap-6 pb-10 last:pb-0"
              >
                {/* Vertical connector line */}
                {i < FEATURES.length - 1 && (
                  <div className="absolute left-[1.1875rem] top-10 bottom-0 w-px bg-parchment-300" />
                )}

                {/* Step number */}
                <div className="flex-none w-[2.375rem] h-[2.375rem] rounded-full border border-gold-300 bg-gold-50 flex items-center justify-center text-gold-700 font-display text-body-md font-semibold">
                  {i + 1}
                </div>

                {/* Content */}
                <div className="pt-1">
                  <h3 className="font-display text-display-md font-semibold text-ink-900 mb-1.5">
                    {feature.title}
                  </h3>
                  <p className="text-body-sm text-ink-600 font-body leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Mid-page CTA */}
          <div className="mt-14 text-center">
            <Link
              href="/app"
              className="
                inline-block font-body font-medium px-8 py-3.5 rounded-xl text-body-md
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors shadow-sm
              "
            >
              Try Free
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Benchmark callout -- social proof */}
      <section className="py-10 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-body-sm text-ink-500 font-body leading-relaxed">
            In blinded evaluation against GPT-5, ProtoCol scored significantly higher
            on statistical accuracy, ethical awareness, and code generation.{" "}
            <Link href="/benchmark" className="text-gold-600 hover:text-gold-700 underline underline-offset-2 transition-colors">
              See benchmark results
            </Link>
          </p>
        </div>
      </section>

      {/* Comparison */}
      <section className="py-20 px-6 bg-parchment-50/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 text-center mb-3">
            95% cheaper than legacy tools
          </h2>
          <p className="text-body-md text-ink-500 font-body text-center mb-10">
            Traditional statistical software charges thousands per year with no AI guidance.
          </p>

          <div className="bg-white/80 border border-parchment-200 rounded-xl overflow-x-auto">
            <table className="w-full min-w-[28rem]">
              <thead>
                <tr className="border-b border-parchment-200">
                  <th className="text-left px-4 sm:px-5 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    Tool
                  </th>
                  <th className="text-left px-4 sm:px-5 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    Price
                  </th>
                  <th className="text-center px-3 sm:px-4 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    AI Guidance
                  </th>
                  <th className="text-center px-3 sm:px-4 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    Code Gen
                  </th>
                  <th className="text-center px-3 sm:px-4 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    Lit Search
                  </th>
                </tr>
              </thead>
              <tbody>
                {COMPARISONS.map((item) => {
                  const check = (
                    <svg className="w-4 h-4 text-gold-600 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  );
                  const dash = <span className="block text-center text-ink-300">&mdash;</span>;

                  return (
                    <tr
                      key={item.name}
                      className={`border-b border-parchment-100 last:border-b-0 ${
                        item.highlight ? "bg-gold-50/60 border-gold-200" : ""
                      }`}
                    >
                      <td className="px-4 sm:px-5 py-3 text-body-sm font-body text-ink-800 font-medium">
                        {item.name}
                      </td>
                      <td className="px-4 sm:px-5 py-3 text-body-sm font-body text-ink-600">
                        {item.price}
                      </td>
                      <td className="px-3 sm:px-4 py-3">{item.guided ? check : dash}</td>
                      <td className="px-3 sm:px-4 py-3">{item.codeGen ? check : dash}</td>
                      <td className="px-3 sm:px-4 py-3">{item.litSearch ? check : dash}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ / Objection Handling */}
      <section className="py-20 px-6">
        <motion.div
          className="max-w-3xl mx-auto"
          initial="initial"
          whileInView="animate"
          viewport={{ once: true, margin: "-100px" }}
          variants={stagger}
        >
          <motion.h2
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="font-display text-display-lg font-semibold text-ink-900 text-center mb-4"
          >
            Common questions
          </motion.h2>
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="text-body-md text-ink-500 font-body text-center mb-12"
          >
            The short answer: yes, the calculations are real math — not AI guessing.
          </motion.p>

          <div className="space-y-3">
            {FAQS.map((faq, i) => (
              <motion.div
                key={i}
                variants={fadeUp}
                transition={{ duration: 0.3 }}
                className="bg-white border border-parchment-200 rounded-xl overflow-hidden"
              >
                <button
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full text-left px-6 py-4 flex items-center justify-between gap-4 cursor-pointer"
                  aria-expanded={openFaq === i}
                >
                  <span className="text-body-md font-body font-medium text-ink-800">
                    {faq.q}
                  </span>
                  <svg
                    className={`w-5 h-5 text-ink-400 flex-none transition-transform duration-200 ${
                      openFaq === i ? "rotate-180" : ""
                    }`}
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
                <AnimatePresence>
                  {openFaq === i && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.2 }}
                      className="overflow-hidden"
                    >
                      <p className="px-6 pb-5 text-body-sm text-ink-600 font-body leading-relaxed">
                        {faq.a}
                      </p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Final CTA */}
      <section className="py-24 px-6 bg-parchment-50/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 mb-4">
            Stop guessing. Start designing.
          </h2>
          <p className="text-body-md text-ink-500 font-body mb-8">
            5 free queries per month. No credit card. No biostatistician waitlist.
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
            Start Your Research Plan
          </Link>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}
