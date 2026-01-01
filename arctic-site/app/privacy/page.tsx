'use client';

export default function PrivacyPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-gray-400 mb-8">Last updated: December 2025</p>

        <div className="prose prose-invert max-w-none space-y-6 text-gray-400">
          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Overview</h2>
            <p>
              ArcticCodex ("we", "our", or "us") is committed to protecting your privacy. This Privacy
              Policy explains how we collect, use, disclose, and otherwise handle your information.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Information We Collect</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Account and org data (email, name, company, roles)</li>
              <li>Billing data (processed by Stripe; we do not store full card details)</li>
              <li>Product telemetry (API usage, latency, errors) for reliability and abuse prevention</li>
              <li>Content you send to the API (Customer Data) to provide responses; not used to train hosted models by default</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. How We Use Information</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Deliver the hosted service and generate responses</li>
              <li>Provide audit receipts and security logging</li>
              <li>Operate billing, support, and abuse/threat detection</li>
              <li>Meet legal and compliance obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Data Handling & Training</h2>
            <p>
              Customer Data is not used to train hosted models unless you opt in in writing. Audit receipts include hashes of responses and citations. You control deletion and retention per your plan; Enterprise can request custom retention and region pinning.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. Security</h2>
            <p>
              TLS 1.3 in transit; AES-256-GCM at rest. API keys are required for all requests. Role-based access control and audit receipts on responses. See Security and Trust Center for details.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Subprocessors</h2>
            <p>We use limited subprocessors to deliver the service:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Vercel (hosting)</li>
              <li>Supabase (optional data persistence for chat history)</li>
              <li>Stripe (billing)</li>
            </ul>
            <p className="text-sm text-gray-500">Enterprise customers may request a full subprocessors list and receive notice of material changes.</p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. Data Retention & Deletion</h2>
            <p>
              Hosted request/response logs: 30 days (configurable for Enterprise). Audit receipts: retained per contract. You may request deletion of Customer Data and account data; we honor statutory exceptions and legal holds.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">8. International Transfers</h2>
            <p>
              Data may be processed in the US. Enterprise can request EU residency. Standard Contractual Clauses (SCCs) or equivalent safeguards are used for cross-border transfers where required.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">9. Your Rights</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Access, correct, or delete your personal data</li>
              <li>Data portability where applicable</li>
              <li>Opt out of marketing communications</li>
              <li>Object to processing where permitted by law</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">10. Contact</h2>
            <p>
              Privacy requests: <a href="mailto:privacy@arcticcodex.com" className="text-cyan-400 hover:underline">privacy@arcticcodex.com</a>. DPA/BAA requests: <a href="mailto:legal@arcticcodex.com" className="text-cyan-400 hover:underline">legal@arcticcodex.com</a>.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
