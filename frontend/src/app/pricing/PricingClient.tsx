"use client";

import { useState } from "react";

interface PricingTier {
  name: string;
  price: string;
  annual: string;
  description: string;
  features: string[];
  cta: string;
  highlighted?: boolean;
  variantId?: string;
}

const TIERS: PricingTier[] = [
  {
    name: "Free",
    price: "$0",
    annual: "$0",
    description: "Explore the basics",
    features: [
      "5 queries per month",
      "Basic study design guidance",
      "Simple & Advanced modes",
    ],
    cta: "Get Started",
  },
  {
    name: "Researcher",
    price: "$15",
    annual: "$12",
    description: "For individual researchers",
    features: [
      "50 queries per month",
      "Full methodology + sample size",
      "File upload (PDF, DOCX, images)",
      "Session history",
      "Protocol export (DOCX & PDF)",
    ],
    cta: "Subscribe",
    highlighted: true,
    // variantId: "TODO", // Set after creating LemonSqueezy products
  },
  {
    name: "Pro",
    price: "$29",
    annual: "$23",
    description: "For active researchers",
    features: [
      "Unlimited queries",
      "Everything in Researcher",
      "Priority AI models",
      "Advanced statistical scenarios",
      "Citation generation",
    ],
    cta: "Subscribe",
    // variantId: "TODO",
  },
  {
    name: "Institutional",
    price: "$49-99",
    annual: "Contact us",
    description: "Per user/month for teams",
    features: [
      "Unlimited queries",
      "Everything in Pro",
      "Admin dashboard",
      "Usage analytics",
      "SSO & invoice billing",
      "Priority support",
    ],
    cta: "Contact Sales",
  },
];

export default function PricingClient() {
  const [annual, setAnnual] = useState(false);

  return (
    <div className="min-h-screen bg-parchment-100 py-16 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <a
            href="/app"
            className="text-parchment-600 text-sm hover:text-parchment-800 mb-4 inline-block"
          >
            &larr; Back to app
          </a>
          <h1 className="font-cormorant text-4xl font-semibold text-parchment-900 mb-3">
            Choose Your Plan
          </h1>
          <p className="text-parchment-600 max-w-xl mx-auto">
            AI-guided research methodology, study design, and sample size
            calculation. 95% cheaper than legacy statistical software.
          </p>
        </div>

        {/* Annual toggle */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <span
            className={`text-sm transition-colors ${!annual ? "text-parchment-900 font-medium" : "text-parchment-500"}`}
          >
            Monthly
          </span>
          <button
            onClick={() => setAnnual(!annual)}
            aria-pressed={annual}
            className={`relative w-12 h-7 rounded-full transition-colors ${
              annual ? "bg-parchment-700" : "bg-parchment-600"
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                annual ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
          <span
            className={`text-sm transition-colors ${annual ? "text-parchment-900 font-medium" : "text-parchment-500"}`}
          >
            Annual{" "}
            <span className="text-green-600 font-medium">(Save 20%)</span>
          </span>
        </div>

        {/* Pricing cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`bg-white/80 backdrop-blur-sm border rounded-xl p-6 flex flex-col ${
                tier.highlighted
                  ? "border-parchment-700 ring-2 ring-parchment-700/20"
                  : "border-parchment-200"
              }`}
            >
              {tier.highlighted && (
                <span className="inline-block text-xs font-medium bg-parchment-700 text-white px-2.5 py-0.5 rounded-full self-start mb-3">
                  Most Popular
                </span>
              )}
              <h3 className="font-cormorant text-xl font-semibold text-parchment-800">
                {tier.name}
              </h3>
              <div className="mt-2 mb-1">
                <span className="text-3xl font-semibold text-parchment-900">
                  {annual ? tier.annual : tier.price}
                </span>
                {tier.price !== "$0" && tier.name !== "Institutional" && (
                  <span className="text-parchment-500 text-sm">/mo</span>
                )}
              </div>
              <p className="text-parchment-500 text-sm mb-6">
                {tier.description}
              </p>

              <ul className="space-y-2 flex-1 mb-6">
                {tier.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-2 text-sm text-parchment-700"
                  >
                    <svg
                      className="w-4 h-4 text-green-600 mt-0.5 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    {feature}
                  </li>
                ))}
              </ul>

              <button
                className={`w-full py-2.5 rounded-lg text-sm font-medium transition-colors ${
                  tier.highlighted
                    ? "bg-parchment-800 text-white hover:bg-parchment-900"
                    : "bg-parchment-100 text-parchment-800 hover:bg-parchment-200 border border-parchment-300"
                }`}
              >
                {tier.cta}
              </button>
            </div>
          ))}
        </div>

        {/* Comparison note */}
        <div className="mt-12 text-center">
          <p className="text-sm text-parchment-500">
            Compare: nQuery costs $925-$7,495/year with no AI guidance.
            <br />
            Rexearch provides AI-guided methodology for a fraction of the
            cost.
          </p>
        </div>
      </div>
    </div>
  );
}
