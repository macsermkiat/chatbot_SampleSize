import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Terms of Service - ProtoCol",
  description: "Terms of service for ProtoCol, the AI-powered research methodology assistant.",
};

export default function TermsOfService() {
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
        <h1 className="font-display text-display-sm text-ink-900 mb-2">Terms of Service</h1>
        <p className="text-body-sm text-ink-400 mb-10">Last updated: {lastUpdated}</p>

        <div className="space-y-8 text-body-sm leading-relaxed text-ink-700">
          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">1. Acceptance of Terms</h2>
            <p>
              By accessing or using ProtoCol at www.protocol.med (the &quot;Service&quot;), operated by
              Royyak Co., Ltd., you agree to be bound by these Terms of Service. If you do not agree,
              do not use the Service.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">2. Description of Service</h2>
            <p>
              ProtoCol is an AI-powered research methodology assistant that helps researchers with
              gap analysis, study design, and biostatistical analysis. The Service uses large language
              models and literature search to generate research guidance.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">3. Not Medical or Clinical Advice</h2>
            <p className="font-semibold text-ink-900">
              The Service is intended for research planning purposes only. It does not provide
              medical advice, clinical recommendations, or diagnostic guidance. All generated
              protocols and methodologies must be reviewed by qualified experts before use in
              any research study. You assume full responsibility for any decisions made based
              on the Service&apos;s output.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">4. AI Output Disclaimer</h2>
            <p className="font-semibold text-ink-900 mb-3">
              Royyak Co., Ltd. does not guarantee the accuracy, completeness, or correctness of any
              AI-generated content, including but not limited to research protocols, manuscripts,
              statistical analyses, sample size calculations, study designs, and methodology recommendations.
            </p>
            <ul className="list-disc pl-6 space-y-2">
              <li>
                All AI-generated outputs are drafts intended as a starting point. It is the
                user&apos;s sole responsibility to review, verify, and validate all content before
                submission or use in any capacity.
              </li>
              <li>
                Users should consult qualified subject-matter experts, biostatisticians, and
                methodologists as appropriate for their research context.
              </li>
              <li>
                The Service does not guarantee acceptance for publication in any journal, approval
                by any Institutional Review Board (IRB) or Ethics Committee (EC), successful
                registration with any trial registry (e.g., ClinicalTrials.gov, Thai Clinical
                Trials Registry), or approval by any regulatory authority.
              </li>
              <li>
                AI-generated citations and references may be inaccurate, incomplete, or fabricated.
                Users must independently verify all cited sources.
              </li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">5. User Accounts</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>You must provide accurate information when creating an account.</li>
              <li>You are responsible for maintaining the security of your account credentials.</li>
              <li>You must not share your account with others or use another person&apos;s account.</li>
              <li>We reserve the right to suspend or terminate accounts that violate these terms.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">6. Acceptable Use</h2>
            <p className="mb-3">You agree not to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Use the Service for any unlawful purpose.</li>
              <li>Attempt to reverse-engineer, exploit, or abuse the AI systems.</li>
              <li>Upload malicious files or content.</li>
              <li>Exceed usage limits or circumvent billing mechanisms.</li>
              <li>Use the Service to generate misleading or fabricated research.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">7. Intellectual Property</h2>
            <p>
              You retain ownership of your research content and uploaded documents.
              AI-generated outputs (methodology suggestions, statistical analyses, protocol drafts)
              are provided for your use but come with no guarantee of originality or accuracy.
              The ProtoCol name, logo, and platform design are the property of Royyak Co., Ltd.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">8. Subscriptions and Billing</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>Paid subscriptions are billed through LemonSqueezy.</li>
              <li>Free tier usage is subject to the limits described on the pricing page.</li>
              <li>Refunds are handled on a case-by-case basis within 14 days of purchase.</li>
              <li>We reserve the right to change pricing with 30 days notice.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">9. Limitation of Liability</h2>
            <p>
              The Service is provided &quot;as is&quot; without warranties of any kind. Royyak Co., Ltd.
              is not liable for any damages arising from your use of the Service, including but
              not limited to inaccurate AI outputs, data loss, or service interruptions.
              Our total liability shall not exceed the amount you paid for the Service in the
              12 months preceding any claim.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">10. Changes to Terms</h2>
            <p>
              We may update these terms at any time. Continued use of the Service after changes
              constitutes acceptance. We will notify users of material changes via email or
              in-app notification.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">11. Contact</h2>
            <p>
              For questions about these terms, contact us at{" "}
              <a href="mailto:contact@protocol.med" className="text-ink-600 hover:text-ink-800 underline underline-offset-2 transition-colors">
                contact@protocol.med
              </a>.
            </p>
          </section>
        </div>
      </main>
    </div>
  );
}
