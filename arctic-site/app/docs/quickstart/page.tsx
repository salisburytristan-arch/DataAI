'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Terminal, Download, Play, CheckCircle } from 'lucide-react';

export default function QuickstartPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="border-b border-white/10 py-12">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Link href="/docs" className="text-sm text-cyan-400 hover:underline mb-4 inline-block">
              ← Back to Docs
            </Link>
            <h1 className="text-4xl font-bold mb-4">Quickstart Guide</h1>
            <p className="text-gray-400 text-lg">
              Call the hosted ArcticCodex API in minutes. Hosted-first; local is optional for Enterprise.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Prerequisites */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-bold mb-6">Prerequisites</h2>
        <div className="border border-white/10 rounded-lg p-6 bg-white/[0.02] mb-8">
          <ul className="space-y-2 text-gray-400">
            <li className="flex gap-2">
              <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
              API key from Console
            </li>
            <li className="flex gap-2">
              <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
              HTTPS client (curl, Postman, or SDK)
            </li>
            <li className="flex gap-2">
              <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
              For local optional use: Python 3.10+ and uvicorn
            </li>
          </ul>
        </div>

        {/* Step 1: Get an API key */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              1
            </div>
            <h3 className="text-xl font-bold">Create an API key</h3>
          </div>
          <p className="text-gray-400 mb-2">In Console → API Keys → New key. Keep it secret; scoped to your org.</p>
        </div>

        {/* Step 2: Call hosted chat */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              2
            </div>
            <h3 className="text-xl font-bold">Send your first request</h3>
          </div>

          <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4 whitespace-pre-wrap">
{`curl -X POST https://api.arcticcodex.com/v1/chat/completions \
  -H "Authorization: Bearer $ACX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ac-hosted-pro",
    "messages": [{"role": "user", "content": "What is ArcticCodex?"}],
    "temperature": 0.3
  }'`}
          </pre>
          <p className="text-gray-500 text-sm">Response includes <span className="font-mono text-cyan-300">audit</span> with event_id, hash, timestamp, export_url, and citations.</p>
        </div>

        {/* Step 3: Retrieve audit receipt */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              3
            </div>
            <h3 className="text-xl font-bold">Download the audit receipt</h3>
          </div>
          <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4 whitespace-pre-wrap">
{`curl -X GET https://api.arcticcodex.com/v1/audit/receipts/ev_abc123 \
  -H "Authorization: Bearer $ACX_API_KEY"`}
          </pre>
        </div>

        {/* Optional: Ingest and search */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              4
            </div>
            <h3 className="text-xl font-bold">Search your hosted vault</h3>
          </div>
          <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4 whitespace-pre-wrap">
{`curl -X POST https://api.arcticcodex.com/v1/vault/search \
  -H "Authorization: Bearer $ACX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "audit", "limit": 5}'`}
          </pre>
        </div>

        {/* Optional local (Enterprise) */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              5
            </div>
            <h3 className="text-xl font-bold">Optional: Local runtime (Enterprise)</h3>
          </div>
          <p className="text-gray-400 mb-2">For regulated on-prem: run the API locally with your own models.</p>
          <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4 whitespace-pre-wrap">
{`python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn packages.core.src.api:app --port 8000`}
          </pre>
        </div>

        {/* Next Steps */}
        <div className="border-t border-white/10 pt-12">
          <h2 className="text-2xl font-bold mb-6">Next Steps</h2>

          <div className="grid md:grid-cols-2 gap-6">
            <Link
              href="/docs/api"
              className="border border-white/10 rounded-lg p-6 hover:border-cyan-400/50 transition-all"
            >
              <h4 className="font-bold mb-2 text-cyan-400">API Reference</h4>
              <p className="text-sm text-gray-400">
                Complete REST API documentation for all endpoints.
              </p>
            </Link>

            <Link
              href="/docs/architecture"
              className="border border-white/10 rounded-lg p-6 hover:border-cyan-400/50 transition-all"
            >
              <h4 className="font-bold mb-2 text-cyan-400">Architecture</h4>
              <p className="text-sm text-gray-400">
                Deep dive into ForgeNumerics and vault architecture.
              </p>
            </Link>

            <Link
              href="/security"
              className="border border-white/10 rounded-lg p-6 hover:border-cyan-400/50 transition-all"
            >
              <h4 className="font-bold mb-2 text-cyan-400">Security</h4>
              <p className="text-sm text-gray-400">
                Learn about encryption, HMAC, and compliance features.
              </p>
            </Link>

            <a
              href="mailto:support@arcticcodex.com"
              className="border border-white/10 rounded-lg p-6 hover:border-cyan-400/50 transition-all"
            >
              <h4 className="font-bold mb-2 text-cyan-400">Get Help</h4>
              <p className="text-sm text-gray-400">
                Contact support if you run into issues.
              </p>
            </a>
          </div>
        </div>
      </section>

      {/* Troubleshooting */}
      <section className="border-t border-white/10 bg-white/[0.01] py-12">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">Common Issues</h2>

          <div className="space-y-4">
            {[
              {
                q: '401 Unauthorized',
                a: 'Ensure Authorization header is set: Bearer <API_KEY>. Rotate the key if compromised.',
              },
              {
                q: '429 Too Many Requests',
                a: 'Sandbox has 50k token/month and burst limits. Upgrade or contact support for Enterprise limits.',
              },
              {
                q: 'Need EU data residency',
                a: 'Enterprise can request EU-hosted tenancy; contact support.',
              },
              {
                q: 'Missing audit receipt fields',
                a: 'All hosted responses include audit. If absent, contact support with request ID.',
              },
            ].map((item, i) => (
              <details
                key={i}
                className="border border-white/10 rounded-lg p-4 bg-white/[0.02]"
              >
                <summary className="cursor-pointer font-mono text-sm text-cyan-400 hover:text-cyan-300">
                  {item.q}
                </summary>
                <p className="mt-3 text-sm text-gray-400">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
