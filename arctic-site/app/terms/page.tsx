'use client';

export default function TermsPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-gray-400 mb-8">Last updated: December 2025</p>

        <div className="prose prose-invert max-w-none space-y-6 text-gray-400">
          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Scope</h2>
            <p>
              These Terms govern your access to and use of the ArcticCodex hosted platform, APIs, console, and related services.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Accounts & Access</h2>
            <p>
              You must maintain accurate account information. API keys are confidential and must not be shared outside your organization. You are responsible for activity under your account and keys.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Acceptable Use</h2>
            <p>
              Do not misuse the service (no illegal content, malware, denial-of-service, credential stuffing, model abuse, or attempts to access other tenants). We may throttle or suspend for abuse.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Customer Data</h2>
            <p>
              You retain all rights to Customer Data. We do not train hosted models on your data by default. We process Customer Data solely to provide the services, subject to the Privacy Policy and any DPA/BAA executed.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. Service Levels</h2>
            <p>
              Hosted Pro targets 99.5% uptime; Enterprise targets 99.9%+. SLA credits (if applicable) are your exclusive remedy for SLA breaches. Status is published on the Status page.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Security</h2>
            <p>
              We implement encryption in transit (TLS 1.3) and at rest (AES-256), role-based access controls, and audit receipts for API responses. You must keep credentials secure and configure least-privilege roles.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. Fees & Payment</h2>
            <p>
              Paid tiers are billed as stated on the Pricing page or order form. Overages and taxes may apply. Late payments may result in suspension.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">8. Confidentiality</h2>
            <p>
              Non-public information disclosed by either party must be protected with reasonable care and used only for fulfilling these Terms.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">9. Warranties & Disclaimers</h2>
            <p>
              Services are provided “as is.” We disclaim all implied warranties to the maximum extent permitted by law.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">10. Limitation of Liability</h2>
            <p>
              To the fullest extent permitted, our aggregate liability is limited to fees paid in the prior three (3) months. We are not liable for indirect, incidental, or consequential damages.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">11. Termination</h2>
            <p>
              You may terminate by stopping use and closing your account. We may terminate or suspend for breach, abuse, or non-payment. Upon termination, you may request deletion of Customer Data subject to legal retention.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">12. Governing Law</h2>
            <p>
              These Terms are governed by the laws of Delaware, USA, without regard to conflict of laws. Venue is the state or federal courts in Delaware.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">13. Contact</h2>
            <p>
              Legal notices: <a href="mailto:legal@arcticcodex.com" className="text-cyan-400 hover:underline">legal@arcticcodex.com</a>. Security: <a href="mailto:security@arcticcodex.com" className="text-cyan-400 hover:underline">security@arcticcodex.com</a>.
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
