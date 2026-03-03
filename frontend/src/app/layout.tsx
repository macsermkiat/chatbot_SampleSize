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

export const metadata: Metadata = {
  title: "Research Assistant",
  description: "Medical research planning: gap analysis, methodology design, biostatistics",
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
