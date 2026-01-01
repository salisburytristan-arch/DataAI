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
              Hosted API for ArcticCodex. OpenAI-compatible chat completions plus vault search and audit receipts.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Base URL */}
      <section className="max-w-4xl mx-auto px-6 py-12">
        <div className="border border-white/10 rounded-lg p-6 bg-white/[0.02] mb-8">
          <h3 className="text-sm font-bold text-gray-400 mb-2">Base URL</h3>
          <code className="text-cyan-400 font-mono">https://api.arcticcodex.com</code>
          <p className="text-xs text-gray-500 mt-2">All requests require HTTPS and a Bearer API key.</p>
        </div>

        {/* Authentication */}
        <h2 className="text-2xl font-bold mb-4">Authentication</h2>
        <p className="text-gray-400 mb-8">Send <span className="font-mono text-cyan-400">Authorization: Bearer &lt;API_KEY&gt;</span> for every request. Keys are scoped to orgs; rotate in Console.</p>

        {/* Endpoints */}
        <h2 className="text-2xl font-bold mb-6">Endpoints</h2>

        {/* Chat Completions (OpenAI-compatible) */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-blue-900/30 text-blue-400 text-xs font-mono">POST</span>
            <code className="text-cyan-400 font-mono">/v1/chat/completions</code>
          </div>
          <p className="text-gray-400 mb-4">Drop-in compatible with OpenAI chat completions; returns audit receipts and citations.</p>
          <details className="text-sm mb-4">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">Request Body</summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 font-mono text-xs overflow-x-auto">
{JSON.stringify({
  model: 'ac-hosted-pro',
  messages: [{ role: 'user', content: 'What is ArcticCodex?' }],
  temperature: 0.3,
  max_tokens: 800
}, null, 2)}
            </pre>
          </details>
          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">Example Response</summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
{JSON.stringify({
  id: 'chatcmpl-123',
  object: 'chat.completion',
  created: 1735600000,
  model: 'ac-hosted-pro',
  choices: [{ message: { role: 'assistant', content: 'ArcticCodex is an audit-ready hosted LLM platform.' }, finish_reason: 'stop' }],
  audit: {
    event_id: 'ev_abc123',
    hash: 'sha256:... ',
    timestamp: '2025-12-30T00:00:00Z',
    export_url: 'https://api.arcticcodex.com/v1/audit/receipts/ev_abc123',
    citations: [{ doc: 'vault://doc/123', offset: 0 }]
  }
}, null, 2)}
            </pre>
          </details>
        </div>

        {/* Vault Search */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-blue-900/30 text-blue-400 text-xs font-mono">POST</span>
            <code className="text-cyan-400 font-mono">/v1/vault/search</code>
          </div>
          <p className="text-gray-400 mb-4">Hybrid search over your hosted vault with citations.</p>
          <details className="text-sm mb-4">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">Request Body</summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 font-mono text-xs overflow-x-auto">
{JSON.stringify({ query: 'audit logging', limit: 5 }, null, 2)}
            </pre>
          </details>
          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">Example Response</summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
{JSON.stringify({
  results: [
    { chunk_id: 'ch_1', score: 0.82, snippet: 'Every response is signed and logged...', citation: { doc: 'vault://doc/123', offset: 0 } }
  ]
}, null, 2)}
            </pre>
          </details>
        </div>

        {/* Audit Receipts */}
        <div className="mb-8 border border-white/10 rounded-lg p-6 bg-white/[0.02]">
          <div className="flex items-center gap-2 mb-4">
            <span className="px-2 py-1 rounded bg-green-900/30 text-green-400 text-xs font-mono">GET</span>
            <code className="text-cyan-400 font-mono">/v1/audit/receipts/:event_id</code>
          </div>
          <p className="text-gray-400 mb-4">Download the signed audit receipt for a prior response.</p>
          <details className="text-sm">
            <summary className="cursor-pointer text-cyan-400 hover:text-cyan-300 mb-2">Example Response</summary>
            <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 font-mono text-xs overflow-x-auto">
{JSON.stringify({
  event_id: 'ev_abc123',
  hash: 'sha256:...',
  timestamp: '2025-12-30T00:00:00Z',
  signer: 'ac-hosted',
  citations: [{ doc: 'vault://doc/123', offset: 0 }],
  signature: 'hex...'
}, null, 2)}
            </pre>
          </details>
        </div>
      </section>

      {/* Rate Limits */}
      <section className="border-t border-white/10 bg-white/[0.01] py-12">
        <div className="max-w-4xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-6">Rate Limits</h2>
          <div className="border border-white/10 rounded-lg p-6 bg-white/[0.02]">
            <p className="text-gray-400 text-sm">Sandbox: 50k tokens/month, bursts limited. Hosted Pro: 2M tokens/month included; fair-use burst protection applies. Enterprise: contracted per-tenant limits.</p>
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
          <h2 className="text-2xl font-bold mb-6">SDKs</h2>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              { lang: 'Python', status: 'Local examples only', link: '#' },
              { lang: 'JavaScript/TypeScript', status: 'Local examples only', link: '#' },
              { lang: 'Go', status: 'Planned', link: '#' },
              { lang: 'Rust', status: 'Planned', link: '#' },
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
