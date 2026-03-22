"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { createClient } from "@/lib/supabase/client";
import Footer from "@/components/Footer";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import { useTranslation } from "@/lib/i18n";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.12 } },
};

const FEATURE_ICONS = [
  <svg key="1" className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <circle cx="11" cy="11" r="8" />
    <path d="M21 21l-4.35-4.35" />
    <path d="M8 11h6M11 8v6" />
  </svg>,
  <svg key="2" className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2" />
    <rect x="9" y="3" width="6" height="4" rx="1" />
    <path d="M9 14l2 2 4-4" />
  </svg>,
  <svg key="3" className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M3 3v18h18" />
    <path d="M7 16l4-8 4 4 5-10" />
  </svg>,
  <svg key="4" className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
    <polyline points="14 2 14 8 20 8" />
    <line x1="16" y1="13" x2="8" y2="13" />
    <line x1="16" y1="17" x2="8" y2="17" />
  </svg>,
];

const COMPARISONS = [
  { name: "nQuery", price: "$925\u2013$7,495/yr", guided: false, codeGen: false, litSearch: false, highlight: false },
  { name: "PASS", price: "$1,095\u2013$2,995/yr", guided: false, codeGen: false, litSearch: false, highlight: false },
  { name: "G*Power", price: "Free", guided: false, codeGen: false, litSearch: false, highlight: false },
  { name: "ProtoCol", price: "From $0/mo", guided: true, codeGen: true, litSearch: true, highlight: true },
];

export default function LandingClient() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const { t: tNav } = useTranslation("nav");
  const { t } = useTranslation("landing");

  const FEATURES = [
    { title: t("feature_1_title"), description: t("feature_1_desc"), icon: FEATURE_ICONS[0] },
    { title: t("feature_2_title"), description: t("feature_2_desc"), icon: FEATURE_ICONS[1] },
    { title: t("feature_3_title"), description: t("feature_3_desc"), icon: FEATURE_ICONS[2] },
    { title: t("feature_4_title"), description: t("feature_4_desc"), icon: FEATURE_ICONS[3] },
  ];

  const PAIN_POINTS = [
    { problem: t("pain_1_problem"), solution: t("pain_1_solution") },
    { problem: t("pain_2_problem"), solution: t("pain_2_solution") },
    { problem: t("pain_3_problem"), solution: t("pain_3_solution") },
    { problem: t("pain_4_problem"), solution: t("pain_4_solution") },
  ];

  const FAQS = [
    { q: t("faq_1_q"), a: t("faq_1_a") },
    { q: t("faq_2_q"), a: t("faq_2_a") },
    { q: t("faq_3_q"), a: t("faq_3_a") },
    { q: t("faq_4_q"), a: t("faq_4_a") },
    { q: t("faq_5_q"), a: t("faq_5_a") },
  ];

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
              {tNav("pricing")}
            </Link>
            <Link href="/benchmark" className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body">
              {tNav("benchmark")}
            </Link>
            <Link href="/blog" className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body">
              {tNav("blog")}
            </Link>
            <LanguageSwitcher />
            {isLoggedIn ? (
              <Link
                href="/app"
                className="
                  text-body-sm font-body font-medium px-4 py-2 rounded-lg
                  bg-ink-900 text-parchment-100
                  hover:bg-ink-800 transition-colors
                "
              >
                {tNav("go_to_app")}
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body"
                >
                  {tNav("sign_in")}
                </Link>
                <Link
                  href="/app"
                  className="
                    text-body-sm font-body font-medium px-4 py-2 rounded-lg
                    bg-ink-900 text-parchment-100
                    hover:bg-ink-800 transition-colors
                  "
                >
                  {tNav("try_free")}
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
              {isLoggedIn ? tNav("go_to_app") : tNav("try_free")}
            </Link>
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              aria-label={menuOpen ? tNav("close_menu") : tNav("open_menu")}
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
                  { href: "/pricing", label: tNav("pricing") },
                  { href: "/benchmark", label: tNav("benchmark") },
                  { href: "/blog", label: tNav("blog") },
                  ...(isLoggedIn
                    ? [{ href: "/app", label: tNav("go_to_app") }]
                    : [{ href: "/login", label: tNav("sign_in") }]),
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
                <div className="py-2">
                  <LanguageSwitcher />
                </div>
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
            {t("hero_title")}
          </motion.h1>

          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-body-lg text-ink-600 font-body max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            {t("hero_subtitle")}
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
              {t("hero_cta")}
            </Link>
          </motion.div>

          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="mt-4 text-body-sm text-ink-400 font-body"
          >
            {t("hero_footnote")}
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
            {t("pain_heading")}
          </motion.h2>
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="text-body-md text-ink-500 font-body text-center mb-12 max-w-2xl mx-auto"
          >
            {t("pain_subheading")}
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
        <div className="divider">{t("how_it_works")}</div>
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
              {t("mid_cta")}
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Benchmark callout -- social proof */}
      <section className="py-10 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <p className="text-body-sm text-ink-500 font-body leading-relaxed">
            {t("benchmark_text")}{" "}
            <Link href="/benchmark" className="text-gold-600 hover:text-gold-700 underline underline-offset-2 transition-colors">
              {t("benchmark_link")}
            </Link>
          </p>
        </div>
      </section>

      {/* Comparison */}
      <section className="py-20 px-6 bg-parchment-50/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 text-center mb-3">
            {t("comparison_heading")}
          </h2>
          <p className="text-body-md text-ink-500 font-body text-center mb-10">
            {t("comparison_subheading")}
          </p>

          <div className="bg-white/80 border border-parchment-200 rounded-xl overflow-x-auto">
            <table className="w-full min-w-[28rem]">
              <thead>
                <tr className="border-b border-parchment-200">
                  <th className="text-left px-4 sm:px-5 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    {t("col_tool")}
                  </th>
                  <th className="text-left px-4 sm:px-5 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    {t("col_price")}
                  </th>
                  <th className="text-center px-3 sm:px-4 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    {t("col_ai")}
                  </th>
                  <th className="text-center px-3 sm:px-4 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    {t("col_code")}
                  </th>
                  <th className="text-center px-3 sm:px-4 py-3 text-caption text-ink-500 font-display uppercase tracking-wider">
                    {t("col_lit")}
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
            {t("faq_heading")}
          </motion.h2>
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.4 }}
            className="text-body-md text-ink-500 font-body text-center mb-12"
          >
            {t("faq_subheading")}
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
            {t("final_heading")}
          </h2>
          <p className="text-body-md text-ink-500 font-body mb-8">
            {t("final_subheading")}
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
