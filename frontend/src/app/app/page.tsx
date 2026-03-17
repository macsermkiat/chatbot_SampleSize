import { Suspense } from "react";
import type { Metadata } from "next";
import HomeClient from "../HomeClient";

export const metadata: Metadata = {
  title: "ProtoCol - Research Assistant",
  description:
    "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
  openGraph: {
    title: "ProtoCol - Research Assistant",
    description:
      "AI-powered medical research planning: gap analysis, study methodology design, and biostatistical analysis.",
    url: "https://research-assistant.app/app",
    type: "website",
  },
};

export default function AppPage() {
  return (
    <Suspense>
      <HomeClient />
    </Suspense>
  );
}
