import type { Variants } from "framer-motion";

// ---------------------------------------------------------------------------
// Spring physics presets
// ---------------------------------------------------------------------------

export const springs = {
  gentle: { type: "spring" as const, stiffness: 120, damping: 20, mass: 0.8 },
  snappy: { type: "spring" as const, stiffness: 300, damping: 28, mass: 0.6 },
  slow: { type: "spring" as const, stiffness: 60, damping: 18, mass: 1.2 },
};

// ---------------------------------------------------------------------------
// Easing curves (matches existing Tailwind cubic-bezier)
// ---------------------------------------------------------------------------

export const easings = {
  standard: [0.16, 1, 0.3, 1] as const,
  easeOut: [0.0, 0.0, 0.2, 1] as const,
  easeIn: [0.4, 0.0, 1.0, 1.0] as const,
};

// ---------------------------------------------------------------------------
// Stagger timing constants
// ---------------------------------------------------------------------------

export const STAGGER = {
  messageDelay: 0.06,
  welcomeDelay: 0.14,
  promptDelay: 0.07,
} as const;

// ---------------------------------------------------------------------------
// Presence transition: empty state <-> conversation view
// ---------------------------------------------------------------------------

export const presenceVariants: Variants = {
  initial: { opacity: 0, y: 10, filter: "blur(4px)" },
  animate: {
    opacity: 1,
    y: 0,
    filter: "blur(0px)",
    transition: springs.slow,
  },
  exit: {
    opacity: 0,
    y: -8,
    filter: "blur(2px)",
    transition: { duration: 0.25, ease: easings.easeIn },
  },
};

// ---------------------------------------------------------------------------
// Message bubble entry (directional)
// ---------------------------------------------------------------------------

export const userMessageVariants: Variants = {
  initial: { opacity: 0, x: 16, y: 8, scale: 0.97 },
  animate: {
    opacity: 1,
    x: 0,
    y: 0,
    scale: 1,
    transition: springs.gentle,
  },
};

export const assistantMessageVariants: Variants = {
  initial: { opacity: 0, x: -12, y: 8, scale: 0.98 },
  animate: {
    opacity: 1,
    x: 0,
    y: 0,
    scale: 1,
    transition: springs.gentle,
  },
};

// ---------------------------------------------------------------------------
// Welcome screen sections
// ---------------------------------------------------------------------------

export const welcomeVariants = {
  logo: {
    initial: { opacity: 0, scale: 0.82, y: 12 },
    animate: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { ...springs.slow, delay: 0.1 },
    },
  } satisfies Variants,

  divider: {
    initial: { opacity: 0, scaleX: 0.4 },
    animate: {
      opacity: 1,
      scaleX: 1,
      transition: { duration: 0.5, ease: easings.standard, delay: 0.3 },
    },
  } satisfies Variants,

  text: {
    initial: { opacity: 0, y: 10 },
    animate: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.45, ease: easings.standard, delay: 0.45 },
    },
  } satisfies Variants,

  quote: {
    initial: { opacity: 0, y: 6 },
    animate: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.4, ease: easings.standard, delay: 0.58 },
    },
  } satisfies Variants,

  promptContainer: {
    initial: {},
    animate: {
      transition: {
        staggerChildren: STAGGER.promptDelay,
        delayChildren: 0.7,
      },
    },
  } satisfies Variants,

  promptItem: {
    initial: { opacity: 0, y: 12, scale: 0.97 },
    animate: {
      opacity: 1,
      y: 0,
      scale: 1,
      transition: springs.gentle,
    },
  } satisfies Variants,
} as const;

// ---------------------------------------------------------------------------
// Send button states
// ---------------------------------------------------------------------------

export const sendButtonVariants: Variants = {
  idle: { scale: 1, rotate: 0 },
  ready: {
    scale: 1,
    rotate: 0,
    transition: springs.snappy,
  },
  sending: {
    scale: 0.9,
    transition: { duration: 0.1, ease: easings.easeIn },
  },
  disabled: { scale: 1, opacity: 0.5 },
};
