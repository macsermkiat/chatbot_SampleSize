import type { Metadata } from "next";
import { Cormorant_Garamond, Source_Serif_4, JetBrains_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/react";
import "./globals.css";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-cormorant",
  display: "swap",
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-source-serif",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains",
  display: "swap",
});

// Note: poweredByHeader: false is configured in next.config.js
export const metadata: Metadata = {
  metadataBase: new URL("https://research-assistant.app"),
  title: "Research Assistant",
  description:
    "Medical research planning: gap analysis, methodology design, biostatistics",
  openGraph: {
    title: "Research Assistant",
    description:
      "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
    url: "https://research-assistant.app",
    siteName: "Research Assistant",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Research Assistant",
    description:
      "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={`${cormorant.variable} ${sourceSerif.variable} ${jetbrains.variable}`}
    >
      <body className="min-h-screen bg-parchment-100">
        {children}
        <Analytics />
      </body>
    </html>
  );
}
