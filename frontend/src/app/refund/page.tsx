import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Refund Policy - ProtoCol",
  description: "Refund policy for ProtoCol, the AI-powered research methodology assistant.",
};

export default function RefundPolicy() {
  const lastUpdated = "March 20, 2026";

  return (
    <div className="min-h-screen bg-parchment-50 text-ink-800 font-body">
      <nav className="border-b border-parchment-200 px-6 py-4">
        <div className="max-w-3xl mx-auto flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
            <Image src="/logo_protocol.png" alt="ProtoCol" width={28} height={28} className="h-7 w-auto" />
            <span className="font-display text-body-md font-semibold text-ink-800">ProtoCol</span>
          </Link>
          <Link href="/" className="text-body-sm text-ink-500 hover:text-ink-700 transition-colors">
            Back to Home
          </Link>
        </div>
      </nav>

      <main className="max-w-3xl mx-auto px-6 py-12">
        <h1 className="font-display text-display-sm text-ink-900 mb-2">Refund Policy</h1>
        <p className="text-body-sm text-ink-400 mb-10">Last updated: {lastUpdated}</p>

        <div className="space-y-8 text-body-sm leading-relaxed text-ink-700">
          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">1. Overview</h2>
            <p>
              We want you to be satisfied with ProtoCol. If you are not happy with your subscription,
              we offer refunds under the conditions described below.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">2. 14-Day Money-Back Guarantee</h2>
            <p>
              If you are not satisfied with your paid subscription, you may request a full refund
              within 14 days of your initial purchase. No questions asked.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">3. Subscription Cancellation</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You may cancel your subscription at any time from your account settings.</li>
              <li>Upon cancellation, you retain access until the end of your current billing period.</li>
              <li>No partial refunds are provided for unused time after the 14-day window.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">4. Refunds After 14 Days</h2>
            <p>
              Refund requests made after 14 days are reviewed on a case-by-case basis.
              We may issue a refund or credit if:
            </p>
            <ul className="list-disc pl-6 space-y-2 mt-3">
              <li>The Service experienced significant downtime or technical issues preventing use.</li>
              <li>You were charged incorrectly or in error.</li>
              <li>Other exceptional circumstances at our discretion.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">5. Free Tier</h2>
            <p>
              The free tier is provided at no cost and is not subject to refunds.
              Free tier usage limits are described on our{" "}
              <Link href="/pricing" className="text-ink-600 hover:text-ink-800 underline underline-offset-2 transition-colors">
                pricing page
              </Link>.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">6. How to Request a Refund</h2>
            <p>
              To request a refund, email us at{" "}
              <a href="mailto:contact@protocol.med" className="text-ink-600 hover:text-ink-800 underline underline-offset-2 transition-colors">
                contact@protocol.med
              </a>{" "}
              with your account email and reason for the request. We aim to process all refund
              requests within 5 business days.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">7. Payment Processing</h2>
            <p>
              Refunds are processed through LemonSqueezy, our payment provider. Once approved,
              the refund will appear on your original payment method within 5-10 business days
              depending on your bank or card issuer.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
