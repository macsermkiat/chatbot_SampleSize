import { Suspense } from "react";
import type { Metadata } from "next";
import HomeClient from "./HomeClient";

export const metadata: Metadata = {
  title: "Research Assistant",
  description:
    "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
  openGraph: {
    title: "Research Assistant",
    description:
      "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
    url: "https://research-assistant.app",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Research Assistant",
    description:
      "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
  },
};

export default function Home() {
  return (
    <Suspense>
      <HomeClient />
    </Suspense>
  );
}
