'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Code, BookOpen, Zap, Shield } from 'lucide-react';

export default function DocsPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="border-b border-white/10 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold mb-4">Documentation</h1>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Everything you need to deploy and integrate ArcticCodex into your infrastructure.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Quick Links */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-2 gap-8">
          {[
            {
              title: 'Hosted Quickstart',
              desc: 'Call the hosted API with an API key and see audit receipts.',
              icon: Zap,
              href: '/docs/quickstart',
            },
            {
              title: 'API Reference',
              desc: 'Complete REST API documentation for all endpoints and models.',
              icon: Code,
              href: '/docs/api',
            },
            {
              title: 'Architecture',
              desc: 'How the hosted control plane, vault, and audit pipeline fit together.',
              icon: BookOpen,
              href: '/docs/architecture',
            },
            {
              title: 'Security',
              desc: 'Threat models, encryption details, and compliance requirements.',
              icon: Shield,
              href: '/security',
            },
          ].map((item, i) => (
            <motion.a
              key={i}
              href={item.href}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="border border-white/10 p-8 rounded-lg bg-white/[0.02] hover:border-cyan-400/50 transition-all cursor-pointer group"
            >
              <item.icon className="w-8 h-8 text-cyan-400 mb-4 group-hover:scale-110 transition" />
              <h3 className="text-xl font-bold mb-2 group-hover:text-cyan-400 transition">
                {item.title}
              </h3>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </motion.a>
          ))}
        </div>
      </section>

      {/* Getting Started */}
      <section className="border-t border-white/10 bg-white/[0.01] py-16">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-8">Getting Started (Hosted)</h2>

          <div className="space-y-8">
            {[
              {
                step: '1',
                title: 'Get an API key',
                code: 'Sign in to Console → API Keys → Create key',
              },
              {
                step: '2',
                title: 'Call hosted chat',
                code: 'curl -X POST https://api.arcticcodex.com/v1/chat \\\n  -H "Authorization: Bearer <API_KEY>" \\\n  -H "Content-Type: application/json" \\\n  -d "{\\"messages\\":[{\\"role\\":\\"user\\",\\"content\\":\\"Hello\\"}]}"',
              },
              {
                step: '3',
                title: 'Verify audit receipt',
                code: 'Response includes: audit.event_id, audit.hash, audit.timestamp, audit.export_url',
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="flex gap-6"
              >
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-cyan-600/30 border border-cyan-500/50 text-cyan-400 font-bold">
                    {item.step}
                  </div>
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                  <code className="block px-4 py-2 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono">
                    {item.code}
                  </code>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-4xl mx-auto px-6 py-16">
          <h2 className="text-3xl font-bold mb-8">Frequently Asked Questions</h2>

        <div className="space-y-4">
          {[
            {
              q: 'Is this hosted or self-hosted?',
              a: 'Primary offering is hosted with private tenancy. Enterprise can add self-hosted deployments.',
            },
            {
              q: 'How do you handle auth?',
              a: 'API keys per org, role-based policies, and optional SSO/SAML on Enterprise.',
            },
            {
              q: 'Do responses include proof?',
              a: 'Yes. Each response returns an audit receipt with event_id, hash, timestamp, and export URL.',
            },
            {
              q: 'Is there a free tier?',
              a: 'Sandbox is free with limited hosted tokens. Hosted Pro adds higher quotas and SLA.',
            },
          ].map((item, i) => (
            <motion.details
              key={i}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ delay: i * 0.05 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-4 group"
            >
              <summary className="cursor-pointer font-bold text-white hover:text-cyan-400 transition">
                {item.q}
              </summary>
              <p className="mt-4 text-gray-400 text-sm">{item.a}</p>
            </motion.details>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/10 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to call the hosted API?</h2>
          <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
            Get an API key, hit the hosted endpoint, and download an audit receipt for every response.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/console"
              className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-lg transition"
            >
              Try Now
            </Link>
            <a
              href="mailto:acrticasters@gmail.com"
              className="px-6 py-3 border border-white/20 hover:border-cyan-400 text-white rounded-lg transition"
            >
              Contact Sales
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
