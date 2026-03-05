"use client";

import { motion } from "framer-motion";
import { springs, easings } from "@/lib/motion.config";

export type ExpertiseLevel = "simple" | "advanced";

interface ExpertisePickerProps {
  onSelect: (level: ExpertiseLevel) => void;
}

const containerVariants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.3,
    },
  },
};

const cardVariants = {
  initial: { opacity: 0, y: 16, scale: 0.97 },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: springs.gentle,
  },
};

const labelVariants = {
  initial: { opacity: 0, y: 6 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: easings.standard, delay: 0.1 },
  },
};

export default function ExpertisePicker({ onSelect }: ExpertisePickerProps) {
  return (
    <motion.div
      className="flex flex-col items-center w-full max-w-lg mx-auto"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <motion.span
        className="text-caption text-ink-400 font-display text-center tracking-wider uppercase mb-4"
        variants={labelVariants}
      >
        How should I explain things?
      </motion.span>

      <div className="flex flex-col sm:flex-row gap-4 w-full">
        {/* Simple mode card */}
        <motion.button
          variants={cardVariants}
          whileHover={{
            scale: 1.02,
            borderColor: "#e6ad36",
            transition: { duration: 0.15 },
          }}
          whileTap={{ scale: 0.97 }}
          onClick={() => onSelect("simple")}
          className="
            flex-1 text-left p-5 rounded-xl
            bg-parchment-50 border-2 border-parchment-200
            hover:bg-gold-50
            transition-colors duration-200
            cursor-pointer
          "
        >
          {/* Icon: open book */}
          <svg
            className="w-8 h-8 text-gold-600 mb-3"
            viewBox="0 0 32 32"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path d="M5 7c3-2 6-2 11 0v19c-5-2-8-2-11 0V7z" />
            <path d="M27 7c-3-2-6-2-11 0v19c5-2 8-2 11 0V7z" />
          </svg>
          <span className="block font-display text-body-md font-semibold text-ink-800 mb-1">
            Getting Started
          </span>
          <span className="block text-caption text-ink-500 font-body leading-snug">
            Plain language explanations, step-by-step guidance. Best for
            residents, fellows, and students new to research.
          </span>
        </motion.button>

        {/* Advanced mode card */}
        <motion.button
          variants={cardVariants}
          whileHover={{
            scale: 1.02,
            borderColor: "#e6ad36",
            transition: { duration: 0.15 },
          }}
          whileTap={{ scale: 0.97 }}
          onClick={() => onSelect("advanced")}
          className="
            flex-1 text-left p-5 rounded-xl
            bg-parchment-50 border-2 border-parchment-200
            hover:bg-gold-50
            transition-colors duration-200
            cursor-pointer
          "
        >
          {/* Icon: flask/beaker */}
          <svg
            className="w-8 h-8 text-ink-600 mb-3"
            viewBox="0 0 32 32"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            aria-hidden="true"
          >
            <path d="M12 4h8M13 4v10l-6 13a1 1 0 001 1h16a1 1 0 001-1l-6-13V4" />
            <path d="M10 22h12" strokeDasharray="2 2" />
          </svg>
          <span className="block font-display text-body-md font-semibold text-ink-800 mb-1">
            Advanced
          </span>
          <span className="block text-caption text-ink-500 font-body leading-snug">
            Full technical detail with frameworks and terminology. For
            researchers familiar with epidemiology and biostatistics.
          </span>
        </motion.button>
      </div>
    </motion.div>
  );
}
