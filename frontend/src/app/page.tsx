import { Suspense } from "react";
import type { Metadata } from "next";
import LandingClient from "./LandingClient";

export const metadata: Metadata = {
  title: "ProtoCol - AI-Powered Research Methodology",
  description:
    "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
  openGraph: {
    title: "ProtoCol - AI-Powered Research Methodology",
    description:
      "From research question to study protocol, guided by AI. Gap analysis, methodology design, and biostatistics.",
    url: "https://research-assistant.app",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "ProtoCol - AI-Powered Research Methodology",
    description:
      "From research question to study protocol, guided by AI.",
  },
};

export default function Home() {
  return (
    <Suspense>
      <LandingClient />
    </Suspense>
  );
}
