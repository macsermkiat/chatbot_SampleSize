"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { BlogPost } from "../posts";

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
};

const stagger = {
  animate: { transition: { staggerChildren: 0.1 } },
};

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + "T00:00:00");
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function renderContent(content: string): React.ReactNode[] {
  const lines = content.trim().split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    if (line.startsWith("## ")) {
      elements.push(
        <h2
          key={i}
          className="font-display text-display-md font-semibold text-ink-900 mt-10 mb-4"
        >
          {line.slice(3)}
        </h2>
      );
      i++;
      continue;
    }

    if (line.startsWith("**The fix:**") || line.startsWith("**What goes wrong")) {
      const text = line.replace(/\*\*(.*?)\*\*/g, "");
      const boldMatch = line.match(/\*\*(.*?)\*\*/);
      elements.push(
        <p
          key={i}
          className="text-body-md text-ink-700 font-body leading-relaxed mb-4 pl-4 border-l-2 border-gold-300"
        >
          <strong className="text-ink-900">{boldMatch?.[1]}</strong>
          {text}
        </p>
      );
      i++;
      continue;
    }

    if (line.trim() === "") {
      i++;
      continue;
    }

    // Regular paragraph -- collect consecutive non-empty, non-heading lines
    const paragraphLines: string[] = [line];
    i++;
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].startsWith("## ") &&
      !lines[i].startsWith("**The fix:**") &&
      !lines[i].startsWith("**What goes wrong")
    ) {
      paragraphLines.push(lines[i]);
      i++;
    }

    const text = paragraphLines.join(" ");
    // Render inline bold
    const parts = text.split(/(\*\*.*?\*\*)/g);
    elements.push(
      <p
        key={`p-${i}`}
        className="text-body-md text-ink-700 font-body leading-relaxed mb-4"
      >
        {parts.map((part, j) => {
          if (part.startsWith("**") && part.endsWith("**")) {
            return (
              <strong key={j} className="text-ink-900">
                {part.slice(2, -2)}
              </strong>
            );
          }
          return part;
        })}
      </p>
    );
  }

  return elements;
}

import Image from "next/image";

export default function BlogPostClient({ post }: { readonly post: BlogPost }) {
  return (
    <div className="min-h-screen bg-parchment-100">
      {/* Navigation */}
      <nav className="border-b border-parchment-200 bg-parchment-100/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Image src="/logo_protocol.png" alt="Protocol" width={28} height={28} className="h-7 w-auto" />
            <span className="font-display text-body-md font-semibold text-ink-900 tracking-tight">Protocol</span>
          </Link>
          <div className="flex items-center gap-6">
            <Link
              href="/blog"
              className="text-body-sm text-ink-600 hover:text-ink-900 transition-colors font-body"
            >
              &larr; All Posts
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

      {/* Article */}
      <motion.article
        className="py-16 px-6"
        initial="initial"
        animate="animate"
        variants={stagger}
      >
        <div className="max-w-2xl mx-auto">
          {/* Meta */}
          <motion.div
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="flex items-center gap-3 mb-6"
          >
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
          </motion.div>

          {/* Title */}
          <motion.h1
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="font-display text-display-xl font-semibold text-ink-900 mb-6 text-balance"
          >
            {post.title}
          </motion.h1>

          {/* Lead */}
          <motion.p
            variants={fadeUp}
            transition={{ duration: 0.5 }}
            className="text-body-lg text-ink-600 font-body leading-relaxed mb-10 pb-10 border-b border-parchment-200"
          >
            {post.description}
          </motion.p>

          {/* Body */}
          <motion.div variants={fadeUp} transition={{ duration: 0.5 }}>
            {renderContent(post.content)}
          </motion.div>
        </div>
      </motion.article>

      {/* CTA */}
      <section className="py-16 px-6 bg-parchment-50/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="font-display text-display-lg font-semibold text-ink-900 mb-4">
            Put these ideas into practice
          </h2>
          <p className="text-body-md text-ink-500 font-body mb-8">
            ProtoCol guides you through gap analysis, methodology design, and
            biostatistical planning -- step by step.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/app"
              className="
                inline-block font-body font-medium px-8 py-3.5 rounded-xl text-body-md
                bg-ink-900 text-parchment-100
                hover:bg-ink-800 transition-colors
                shadow-sm
              "
            >
              Start Research
            </Link>
            <Link
              href="/blog"
              className="
                inline-block font-body font-medium px-6 py-3.5 rounded-xl text-body-md
                bg-parchment-50 text-ink-800 border border-parchment-300
                hover:bg-parchment-200 transition-colors
              "
            >
              More Articles
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-parchment-200 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-caption text-ink-400 font-display">
            ProtoCol -- AI-powered research methodology
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
