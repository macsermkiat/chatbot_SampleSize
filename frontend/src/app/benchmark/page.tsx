import type { Metadata } from "next";
import BenchmarkClient from "./BenchmarkClient";

export const metadata: Metadata = {
  title: "Benchmark: ProtoCol vs GPT-5",
  description:
    "Blinded evaluation results comparing ProtoCol against GPT-5 across 40 medical research scenarios and 16 scoring dimensions.",
  openGraph: {
    title: "Benchmark: ProtoCol vs GPT-5",
    description:
      "Blinded evaluation results comparing ProtoCol against GPT-5 across 40 medical research scenarios and 16 scoring dimensions.",
    url: "https://research-assistant.app/benchmark",
    type: "website",
  },
  twitter: {
    card: "summary",
    title: "Benchmark: ProtoCol vs GPT-5",
    description:
      "Blinded evaluation results comparing ProtoCol against GPT-5 across 40 medical research scenarios.",
  },
};

export default function BenchmarkPage() {
  return <BenchmarkClient />;
}
