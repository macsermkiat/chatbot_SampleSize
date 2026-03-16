"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import FloatingParticles from "@/components/FloatingParticles";
import { BLOG_POSTS } from "./posts";

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
  return (
    <div className="min-h-screen bg-parchment-100">
      {/* Navigation */}
      <nav className="border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link
            href="/"
            className="font-display text-display-md font-semibold text-ink-900 tracking-tight"
          >
            Rexearch
          </Link>
          <div className="flex items-center gap-6">
            <Link
              href="/pricing"
              className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body"
            >
              Pricing
            </Link>
            <Link
              href="/benchmark"
              className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body"
            >
              Benchmark
            </Link>
            <Link
              href="/blog"
              className="text-body-sm text-ink-900 font-medium transition-colors font-body"
            >
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
        </div>
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
                  rounded-xl p-8 hover:border-gold-300
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
            Try Rexearch for your next study
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
      <footer className="border-t border-parchment-200 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-caption text-ink-400 font-display">
            Rexearch -- AI-powered research methodology
          </p>
          <div className="flex items-center gap-6">
            <Link
              href="/pricing"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display"
            >
              Pricing
            </Link>
            <Link
              href="/blog"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display"
            >
              Blog
            </Link>
            <Link
              href="/login"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display"
            >
              Sign In
            </Link>
            <Link
              href="/app"
              className="text-caption text-ink-400 hover:text-ink-600 transition-colors font-display"
            >
              App
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
