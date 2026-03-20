import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Privacy Policy - ProtoCol",
  description: "Privacy policy for ProtoCol, the AI-powered research methodology assistant.",
};

export default function PrivacyPolicy() {
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
        <h1 className="font-display text-display-sm text-ink-900 mb-2">Privacy Policy</h1>
        <p className="text-body-sm text-ink-400 mb-10">Last updated: {lastUpdated}</p>

        <div className="space-y-8 text-body-sm leading-relaxed text-ink-700">
          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">1. Introduction</h2>
            <p>
              ProtoCol (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) is operated by Royyak Co., Ltd.
              This Privacy Policy explains how we collect, use, and protect your information
              when you use our AI-powered research methodology assistant at www.protocol.med (the &quot;Service&quot;).
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">2. Information We Collect</h2>
            <p className="mb-3">We collect the following types of information:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>Account information:</strong> Email address and name when you sign up or log in via Google OAuth.</li>
              <li><strong>Profile information:</strong> Role, institution, and research interests you provide during onboarding.</li>
              <li><strong>Chat content:</strong> Research questions, uploaded documents, and conversation history within your sessions.</li>
              <li><strong>Usage data:</strong> Session activity, feature usage, and token consumption for billing purposes.</li>
              <li><strong>Technical data:</strong> Browser type, IP address, and device information collected automatically.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc pl-6 space-y-2">
              <li>To provide and improve the research methodology assistant service.</li>
              <li>To process your research queries through our AI agents.</li>
              <li>To manage your account and subscriptions.</li>
              <li>To communicate with you about service updates.</li>
              <li>To monitor usage for billing and abuse prevention.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">4. Data Processing and AI</h2>
            <p className="mb-3">
              Your research queries are processed using third-party AI models (OpenAI, Google Gemini).
              These providers may process your input data according to their own privacy policies.
              We do not use your research data to train AI models.
            </p>
            <p>
              Uploaded documents (PDF, DOCX, images) are processed in memory and are not permanently stored on our servers.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">5. Data Storage and Security</h2>
            <p>
              Your data is stored in Supabase (PostgreSQL) with encryption at rest and in transit.
              Authentication is handled via Supabase Auth with JWT tokens.
              We implement industry-standard security measures to protect your information.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">6. Data Sharing</h2>
            <p className="mb-3">We do not sell your personal information. We share data only with:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li><strong>AI providers</strong> (OpenAI, Google) to process your research queries.</li>
              <li><strong>Supabase</strong> for authentication and database hosting.</li>
              <li><strong>LemonSqueezy</strong> for payment processing.</li>
              <li><strong>Tavily</strong> for literature search functionality.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">7. Your Rights</h2>
            <p className="mb-3">You have the right to:</p>
            <ul className="list-disc pl-6 space-y-2">
              <li>Access your personal data stored in our system.</li>
              <li>Request deletion of your account and associated data.</li>
              <li>Export your session history and research data.</li>
              <li>Withdraw consent for data processing at any time.</li>
            </ul>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">8. Data Retention</h2>
            <p>
              We retain your data for as long as your account is active. Upon account deletion,
              we remove your personal data within 30 days. Anonymized usage statistics may be retained
              for service improvement.
            </p>
          </section>

          <section>
            <h2 className="font-display text-body-lg font-semibold text-ink-800 mb-3">9. Contact</h2>
            <p>
              For privacy inquiries, contact us at{" "}
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
