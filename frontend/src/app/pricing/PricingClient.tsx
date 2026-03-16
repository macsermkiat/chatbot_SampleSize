"use client";

import { useState } from "react";
import Link from "next/link";

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
    <div className="min-h-screen bg-parchment-100 py-12 sm:py-16 px-4 sm:px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10 sm:mb-12">
          <Link
            href="/app"
            className="text-body-sm text-ink-500 hover:text-ink-800 font-body mb-4 inline-block transition-colors"
          >
            &larr; Back to app
          </Link>
          <h1 className="font-display text-display-lg font-semibold text-ink-900 mb-3">
            Choose Your Plan
          </h1>
          <p className="text-body-md text-ink-500 font-body max-w-xl mx-auto">
            AI-guided research methodology, study design, and sample size
            calculation. 95% cheaper than legacy statistical software.
          </p>
        </div>

        {/* Annual toggle */}
        <div className="flex items-center justify-center gap-3 mb-8 sm:mb-10">
          <span
            className={`text-body-sm font-body transition-colors ${!annual ? "text-ink-900 font-medium" : "text-ink-400"}`}
          >
            Monthly
          </span>
          <button
            onClick={() => setAnnual(!annual)}
            aria-pressed={annual}
            className={`relative w-12 h-7 rounded-full transition-colors ${
              annual ? "bg-ink-700" : "bg-ink-400"
            }`}
          >
            <span
              className={`absolute top-1 left-1 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-200 ${
                annual ? "translate-x-5" : "translate-x-0"
              }`}
            />
          </button>
          <span
            className={`text-body-sm font-body transition-colors ${annual ? "text-ink-900 font-medium" : "text-ink-400"}`}
          >
            Annual{" "}
            <span className="text-green-700 font-medium">(Save 20%)</span>
          </span>
        </div>

        {/* Pricing cards -- highlighted card first on mobile */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {TIERS.map((tier) => (
            <div
              key={tier.name}
              className={`
                bg-parchment-50/80 border rounded-xl p-5 sm:p-6 flex flex-col
                ${tier.highlighted
                  ? "border-gold-500 ring-2 ring-gold-400/20 order-first md:order-none"
                  : "border-parchment-200"
                }
              `}
            >
              {tier.highlighted && (
                <span className="inline-block text-caption font-display font-medium bg-gold-500 text-parchment-50 px-2.5 py-0.5 rounded-full self-start mb-3 tracking-wide uppercase">
                  Most Popular
                </span>
              )}
              <h3 className="font-display text-display-md font-semibold text-ink-800">
                {tier.name}
              </h3>
              <div className="mt-2 mb-1">
                <span className="text-3xl font-semibold text-ink-900 font-display">
                  {annual ? tier.annual : tier.price}
                </span>
                {tier.price !== "$0" && tier.name !== "Institutional" && (
                  <span className="text-ink-400 text-body-sm font-body">/mo</span>
                )}
              </div>
              <p className="text-ink-500 text-body-sm font-body mb-5 sm:mb-6">
                {tier.description}
              </p>

              <ul className="space-y-2.5 flex-1 mb-5 sm:mb-6">
                {tier.features.map((feature) => (
                  <li
                    key={feature}
                    className="flex items-start gap-2 text-body-sm font-body text-ink-700"
                  >
                    <svg
                      className="w-4 h-4 text-green-700 mt-0.5 shrink-0"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                      aria-hidden="true"
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
                className={`
                  w-full py-2.5 rounded-xl text-body-sm font-display font-medium transition-colors
                  ${tier.highlighted
                    ? "bg-ink-900 text-parchment-100 hover:bg-ink-800"
                    : "bg-parchment-100 text-ink-800 hover:bg-parchment-200 border border-parchment-300"
                  }
                `}
              >
                {tier.cta}
              </button>
            </div>
          ))}
        </div>

        {/* Comparison note */}
        <div className="mt-10 sm:mt-12 text-center">
          <p className="text-body-sm text-ink-400 font-body">
            Compare: nQuery costs $925-$7,495/year with no AI guidance.
            <br className="hidden sm:block" />
            {" "}Rexearch provides AI-guided methodology for a fraction of the cost.
          </p>
        </div>
      </div>
    </div>
  );
}
