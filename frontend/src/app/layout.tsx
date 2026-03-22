import type { Metadata } from "next";
import { Cormorant_Garamond, Inter, JetBrains_Mono } from "next/font/google";
import { Analytics } from "@vercel/analytics/react";
import { GoogleAnalytics } from "@next/third-parties/google";
import { LocaleProvider } from "@/lib/i18n";
import "./globals.css";

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-cormorant",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-jetbrains",
  display: "swap",
});

// Note: poweredByHeader: false is configured in next.config.js
export const viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover" as const,
};

export const metadata: Metadata = {
  metadataBase: new URL("https://research-assistant.app"),
  title: "ProtoCol",
  description:
    "AI-powered medical research planning: gap analysis, methodology design, biostatistics",
  openGraph: {
    title: "ProtoCol",
    description:
      "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
    url: "https://research-assistant.app",
    siteName: "ProtoCol",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "ProtoCol",
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
      className={`${cormorant.variable} ${inter.variable} ${jetbrains.variable}`}
    >
      <body className="min-h-screen bg-parchment-100">
        <LocaleProvider>
          {children}
        </LocaleProvider>
        <Analytics />
        <GoogleAnalytics gaId="G-6H4BMG51H3" />
      </body>
    </html>
  );
}
