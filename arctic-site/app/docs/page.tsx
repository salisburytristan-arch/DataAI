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
              title: 'Quickstart Guide',
              desc: 'Get up and running in 10 minutes with Docker or pip installation.',
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
              desc: 'Deep dive into the ForgeNumerics language and memory architecture.',
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
          <h2 className="text-3xl font-bold mb-8">Getting Started</h2>

          <div className="space-y-8">
            {[
              {
                step: '1',
                title: 'Install',
                code: 'pip install arcticcodex',
              },
              {
                step: '2',
                title: 'Initialize',
                code: 'arctic init --name my-vault',
              },
              {
                step: '3',
                title: 'Connect',
                code: 'arctic console --api https://api.arcticcodex.com',
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
              q: 'What Python versions are supported?',
              a: 'ArcticCodex requires Python 3.10 or newer. We test against 3.10, 3.11, and 3.12.',
            },
            {
              q: 'Can I run this offline?',
              a: 'Yes. ArcticCodex is local-first and can run entirely offline. Optional cloud sync available.',
            },
            {
              q: 'What databases are supported?',
              a: 'PostgreSQL (recommended for production), SQLite (development), MySQL 8.0+.',
            },
            {
              q: 'Is there a free tier?',
              a: 'Yes. Community edition is free for up to 10GB vault storage and 1,000 monthly API calls.',
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
          <h2 className="text-2xl font-bold mb-4">Ready to Deploy?</h2>
          <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
            Join 100+ companies using ArcticCodex for audit-ready intelligence.
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
