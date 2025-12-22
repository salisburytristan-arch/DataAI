'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';

export default function APIReferencePage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="border-b border-white/10 py-12">
        <div className="max-w-4xl mx-auto px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
            <Link href="/docs" className="text-sm text-cyan-400 hover:underline mb-4 inline-block">
              ← Back to Docs
            </Link>
            <h1 className="text-4xl font-bold mb-4">API Reference</h1>
            <p className="text-gray-400 text-lg">
              Complete REST API documentation for ArcticCodex. All endpoints, parameters, and examples.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Base URL */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <div className="border border-white/10 rounded-lg p-6 bg-white/[0.02] mb-8">
          <h3 className="text-sm font-bold text-gray-400 mb-2">Base URL</h3>
          <code className="text-cyan-400 font-mono">https://api.arcticcodex.com/v1</code>
          <p className="text-xs text-gray-500 mt-2">
            Or use localhost for self-hosted: http://localhost:8000/v1
          </p>
        </div>

        {/* Authentication */}
        <h2 className="text-2xl font-bold mb-4">Authentication</h2>
        <p className="text-gray-400 mb-4">
          All API requests require an API key in the Authorization header:
        </p>
        <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-8">
          Authorization: Bearer YOUR_API_KEY
        </code>

        {/* Endpoints */}
        <h2 className="text-2xl font-bold mb-6">Endpoints</h2>

        {/* Health Check */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-green-900/30 text-green-400 text-xs font-mono">
              GET
            </span>
            <code className="text-cyan-400 font-mono">/health</code>
          </div>
          <p className="text-gray-400 mb-4">Check API server health status.</p>
          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Example Response
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  status: 'healthy',
                  version: '1.0.0',
                  uptime: 3600,
                },
                null,
                2
              )}
            </pre>
          </details>
        </div>

        {/* Store Frame */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-blue-900/30 text-blue-400 text-xs font-mono">
              POST
            </span>
            <code className="text-cyan-400 font-mono">/vault/:vault_id/frames</code>
          </div>
          <p className="text-gray-400 mb-4">Store a new frame in the vault.</p>

          <details className="text-sm mb-4">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Request Body
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  content: 'Your knowledge text here',
                  tags: ['tag1', 'tag2'],
                  metadata: {
                    source: 'user_input',
                    timestamp: '2024-12-21T12:00:00Z',
                  },
                },
                null,
                2
              )}
            </pre>
          </details>

          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Example Response
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  frame_id: '0x1A2B3C4D',
                  hmac: 'a1b2c3d4...',
                  status: 'stored',
                  created_at: '2024-12-21T12:00:00Z',
                },
                null,
                2
              )}
            </pre>
          </details>
        </div>

        {/* Search */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-blue-900/30 text-blue-400 text-xs font-mono">
              POST
            </span>
            <code className="text-cyan-400 font-mono">/vault/:vault_id/search</code>
          </div>
          <p className="text-gray-400 mb-4">Search frames in the vault.</p>

          <details className="text-sm mb-4">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Request Body
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  query: 'What is Python?',
                  limit: 10,
                  threshold: 0.7,
                },
                null,
                2
              )}
            </pre>
          </details>

          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Example Response
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  results: [
                    {
                      frame_id: '0x1A2B3C4D',
                      content: 'Python is a high-level programming language',
                      score: 0.95,
                      hmac_verified: true,
                    },
                  ],
                  total: 1,
                },
                null,
                2
              )}
            </pre>
          </details>
        </div>

        {/* Verify Frame */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-green-900/30 text-green-400 text-xs font-mono">
              GET
            </span>
            <code className="text-cyan-400 font-mono">/vault/:vault_id/frames/:frame_id/verify</code>
          </div>
          <p className="text-gray-400 mb-4">Verify frame integrity with HMAC.</p>

          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Example Response
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  frame_id: '0x1A2B3C4D',
                  verified: true,
                  hmac_match: true,
                  checked_at: '2024-12-21T12:00:00Z',
                },
                null,
                2
              )}
            </pre>
          </details>
        </div>

        {/* Audit Log */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-green-900/30 text-green-400 text-xs font-mono">
              GET
            </span>
            <code className="text-cyan-400 font-mono">/vault/:vault_id/audit</code>
          </div>
          <p className="text-gray-400 mb-4">Retrieve audit log entries.</p>

          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">
              Example Response
            </summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
              {JSON.stringify(
                {
                  entries: [
                    {
                      timestamp: '2024-12-21T12:00:00Z',
                      action: 'frame_stored',
                      user_id: 'user_123',
                      frame_id: '0x1A2B3C4D',
                    },
                  ],
                  total: 1,
                },
                null,
                2
              )}
            </pre>
          </details>
        </div>
      </section>

      {/* Rate Limits */}
      <section className="border-t border-white/10 bg-white/[0.01] py-12">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">Rate Limits</h2>

          <div className="border border-white/10 rounded-lg p-6 bg-white/[0.02]">
            <ul className="space-y-2 text-gray-400">
              <li>
                <strong className="text-white">Community:</strong> 1,000 requests/month
              </li>
              <li>
                <strong className="text-white">Professional:</strong> Unlimited
              </li>
              <li>
                <strong className="text-white">Enterprise:</strong> Unlimited with dedicated infrastructure
              </li>
            </ul>
          </div>
        </div>
      </section>

      {/* Error Codes */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <h2 className="text-2xl font-bold mb-6">Error Codes</h2>

        <div className="space-y-3">
          {[
            { code: '400', message: 'Bad Request - Invalid parameters' },
            { code: '401', message: 'Unauthorized - Invalid API key' },
            { code: '403', message: 'Forbidden - Insufficient permissions' },
            { code: '404', message: 'Not Found - Resource does not exist' },
            { code: '429', message: 'Too Many Requests - Rate limit exceeded' },
            { code: '500', message: 'Internal Server Error - Server issue' },
          ].map((error, i) => (
            <div
              key={i}
              className="border border-white/10 rounded-lg p-4 bg-white/[0.02] flex gap-4"
            >
              <code className="text-red-400 font-mono font-bold">{error.code}</code>
              <p className="text-gray-400 text-sm">{error.message}</p>
            </div>
          ))}
        </div>
      </section>

      {/* SDKs */}
      <section className="border-t border-white/10 py-12">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">Official SDKs</h2>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              { lang: 'Python', status: 'Available', link: '#' },
              { lang: 'JavaScript/TypeScript', status: 'Available', link: '#' },
              { lang: 'Go', status: 'Coming Soon', link: '#' },
              { lang: 'Rust', status: 'Coming Soon', link: '#' },
            ].map((sdk, i) => (
              <div
                key={i}
                className="border border-white/10 rounded-lg p-6 bg-white/[0.02] flex justify-between items-center"
              >
                <div>
                  <h4 className="font-bold">{sdk.lang}</h4>
                  <p className="text-sm text-gray-400">{sdk.status}</p>
                </div>
                {sdk.status === 'Available' && (
                  <a href={sdk.link} className="text-cyan-400 hover:underline text-sm">
                    Docs →
                  </a>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
