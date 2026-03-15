import type { Metadata } from "next";
import PricingClient from "./PricingClient";

export const metadata: Metadata = {
  title: "Pricing - DAB Research",
  description: "Choose a plan for AI-powered medical research methodology assistance.",
};

export default function PricingPage() {
  return <PricingClient />;
}
