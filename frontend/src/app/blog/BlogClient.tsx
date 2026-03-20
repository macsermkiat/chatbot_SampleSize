"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import FloatingParticles from "@/components/FloatingParticles";
import { BLOG_POSTS } from "./posts";
import Footer from "@/components/Footer";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.12 } },
};

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function BlogClient() {
  const [menuOpen, setMenuOpen] = useState(false);

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
            <Link href="/blog" className="text-body-sm text-ink-900 font-medium transition-colors font-body">
              Blog
            </Link>
            <Link href="/login" className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body">
              Sign In
            </Link>
            <Link
              href="/app"
              className="text-body-sm font-body font-medium px-4 py-2 rounded-lg bg-ink-900 text-parchment-100 hover:bg-ink-800 transition-colors"
            >
              Open App
            </Link>
          </div>

          {/* Mobile menu button */}
          <div className="flex items-center gap-3 sm:hidden">
            <Link
              href="/app"
              className="text-body-sm font-body font-medium px-3.5 py-1.5 rounded-lg bg-ink-900 text-parchment-100 hover:bg-ink-800 transition-colors"
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
        className="relative py-20 px-6 overflow-hidden"
        initial="initial"
        animate="animate"
        variants={stagger}
      >
        <FloatingParticles count={12} />
        <div className="max-w-3xl mx-auto text-center relative z-10">
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-caption text-gold-600 font-display tracking-wider uppercase mb-4"
          >
            Insights &amp; Methodology
          </motion.p>

          <motion.h1
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="font-display text-display-xl font-semibold text-ink-900 mb-4"
          >
            Blog
          </motion.h1>

          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-body-lg text-ink-600 font-body max-w-2xl mx-auto leading-relaxed"
          >
            Practical guidance on research methodology, biostatistics, and
            AI-assisted study planning.
          </motion.p>
        </div>
      </motion.section>

      {/* Posts */}
      <motion.section
        className="pb-24 px-6"
        initial="initial"
        animate="animate"
        variants={stagger}
      >
        <div className="max-w-3xl mx-auto space-y-8">
          {BLOG_POSTS.map((post) => (
            <motion.article
              key={post.slug}
              variants={fadeUp}
              transition={{ duration: 0.4 }}
            >
              <Link
                href={`/blog/${post.slug}`}
                className="
                  block bg-white/60 backdrop-blur-sm border border-parchment-200
                  rounded-xl p-5 sm:p-8 hover:border-gold-300
                  transition-colors duration-200 group
                "
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-caption text-gold-600 font-display uppercase tracking-wider">
                    {post.category}
                  </span>
                  <span className="text-caption text-ink-300">|</span>
                  <span className="text-caption text-ink-400 font-body">
                    {formatDate(post.date)}
                  </span>
                  <span className="text-caption text-ink-300">|</span>
                  <span className="text-caption text-ink-400 font-body">
                    {post.readingTime}
                  </span>
                </div>

                <h2 className="font-display text-display-md font-semibold text-ink-900 mb-3 group-hover:text-gold-800 transition-colors">
                  {post.title}
                </h2>

                <p className="text-body-sm text-ink-600 font-body leading-relaxed">
                  {post.description}
                </p>

                <span className="inline-block mt-4 text-body-sm text-gold-700 font-body font-medium group-hover:text-gold-900 transition-colors">
                  Read more &rarr;
                </span>
              </Link>
            </motion.article>
          ))}
        </div>
      </motion.section>

      {/* CTA */}
      <section className="py-16 px-6 bg-parchment-50/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 mb-4">
            Try ProtoCol for your next study
          </h2>
          <p className="text-body-md text-ink-500 font-body mb-8">
            AI-guided research planning from gap analysis to sample size
            calculation.
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
      <Footer variant="minimal" />
    </div>
  );
}
