import type { Config } from "tailwindcss";
import plugin from "tailwindcss/plugin";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        parchment: {
          50: "#faf8f4",
          100: "#f5f1e8",
          200: "#ede7d6",
          300: "#ddd3b8",
          400: "#c9b890",
          500: "#b9a273",
          600: "#a88d5e",
          700: "#8d744e",
          800: "#745f44",
          900: "#604f3b",
        },
        ink: {
          50: "#f6f5f3",
          100: "#e8e5df",
          200: "#d3cdc3",
          300: "#b9b0a1",
          400: "#9e9280",
          500: "#8a7e6b",
          600: "#756a5a",
          700: "#5e554a",
          800: "#514940",
          900: "#2c2417",
          950: "#1a150d",
        },
        gold: {
          50: "#fdf9ed",
          100: "#f9edcc",
          200: "#f3d994",
          300: "#ecc35c",
          400: "#e6ad36",
          500: "#c6952b",
          600: "#a87320",
          700: "#88551e",
          800: "#71441f",
          900: "#5f391e",
        },
      },
      fontFamily: {
        display: ["var(--font-cormorant)", "Georgia", "serif"],
        body: ["var(--font-inter)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "Menlo", "monospace"],
      },
      fontSize: {
        "display-xl": ["clamp(2.4rem, 4vw, 3.6rem)", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        "display-lg": ["clamp(1.8rem, 3vw, 2.4rem)", { lineHeight: "1.15", letterSpacing: "-0.01em" }],
        "display-md": ["clamp(1.3rem, 2vw, 1.6rem)", { lineHeight: "1.25" }],
        "body-lg": ["1.125rem", { lineHeight: "1.7" }],
        "body-md": ["1rem", { lineHeight: "1.7" }],
        "body-sm": ["0.875rem", { lineHeight: "1.6" }],
        "caption": ["0.8rem", { lineHeight: "1.5", letterSpacing: "0.04em" }],
      },
      spacing: {
        "18": "4.5rem",
        "22": "5.5rem",
        "26": "6.5rem",
      },
      maxWidth: {
        "chat": "44rem",
      },
      keyframes: {
        "pulse-warm": {
          "0%, 100%": { opacity: "0.4" },
          "50%": { opacity: "0.8" },
        },
        "dot-bounce": {
          "0%, 80%, 100%": { transform: "scale(0.6)", opacity: "0.4" },
          "40%": { transform: "scale(1)", opacity: "1" },
        },
      },
      animation: {
        "pulse-warm": "pulse-warm 2s ease-in-out infinite",
        "dot-bounce": "dot-bounce 1.4s ease-in-out infinite",
      },
    },
  },
  plugins: [
    plugin(function ({ addVariant }) {
      // Targets mobile landscape: short viewport + landscape orientation
      addVariant("short-landscape", "@media (orientation: landscape) and (max-height: 500px)");
    }),
  ],
};

export default config;
