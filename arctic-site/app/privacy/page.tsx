'use client';

export default function PrivacyPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>
        <p className="text-gray-400 mb-8">Last updated: December 2024</p>

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
            <p>We collect information you provide directly:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Account information (email, company name, usage preferences)</li>
              <li>Payment information (processed by Stripe, not stored by us)</li>
              <li>Support requests and communications</li>
              <li>Usage data (API calls, feature usage, performance metrics)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. How We Use Your Information</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Provide and improve our service</li>
              <li>Send product updates and support communications</li>
              <li>Monitor system health and security</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Data Encryption & Security</h2>
            <p>
              All customer data is encrypted at rest using AES-256-GCM and in transit using TLS 1.3.
              We do not access customer vault data.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. Data Retention</h2>
            <p>
              We retain your data only as long as necessary to provide services or as required by law.
              You may request deletion of your account and associated data at any time.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Your Rights</h2>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Access your data</li>
              <li>Correct inaccurate data</li>
              <li>Request deletion (Right to be forgotten)</li>
              <li>Port your data (GDPR Data Portability)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. Contact Us</h2>
            <p>
              For privacy concerns, contact us at{' '}
              <a href="mailto:privacy@arcticcodex.com" className="text-cyan-400 hover:underline">
                privacy@arcticcodex.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
