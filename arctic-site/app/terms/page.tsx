'use client';

export default function TermsPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>
        <p className="text-gray-400 mb-8">Last updated: December 2024</p>

        <div className="prose prose-invert max-w-none space-y-6 text-gray-400">
          <section>
            <h2 className="text-2xl font-bold text-white mb-3">1. Agreement to Terms</h2>
            <p>
              By accessing and using ArcticCodex, you accept and agree to be bound by the terms and
              provision of this agreement.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">2. Use License</h2>
            <p>
              Permission is granted to temporarily download one copy of the materials (information or
              software) on ArcticCodex for personal, non-commercial transitory viewing only.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">3. Disclaimer</h2>
            <p>
              The materials on ArcticCodex are provided on an 'as is' basis. We make no warranties,
              expressed or implied, and hereby disclaim and negate all other warranties including,
              without limitation, implied warranties or conditions of merchantability, fitness for a
              particular purpose, or non-infringement of intellectual property or other violation of
              rights.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">4. Limitations</h2>
            <p>
              In no event shall ArcticCodex or its suppliers be liable for any damages (including,
              without limitation, damages for loss of data or profit, or due to business interruption)
              arising out of the use or inability to use ArcticCodex.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">5. Accuracy of Materials</h2>
            <p>
              The materials appearing on ArcticCodex could include technical, typographical, or
              photographic errors. We do not warrant that any of the materials on ArcticCodex are
              accurate, complete, or current.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">6. Modifications</h2>
            <p>
              We may revise these Terms of Service at any time without notice. By using this website,
              you are agreeing to be bound by the then current version of these terms of service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">7. Governing Law</h2>
            <p>
              These terms and conditions are governed by and construed in accordance with the laws of
              the United States, and you irrevocably submit to the exclusive jurisdiction of the courts
              located in this location.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-bold text-white mb-3">8. Contact</h2>
            <p>
              If you have any questions about these Terms, please contact us at{' '}
              <a href="mailto:legal@arcticcodex.com" className="text-cyan-400 hover:underline">
                legal@arcticcodex.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </main>
  );
}
