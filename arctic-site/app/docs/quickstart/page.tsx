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
              Get ArcticCodex running in 10 minutes. From installation to your first vault query.
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
              Python 3.10 or newer
            </li>
            <li className="flex gap-2">
              <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
              pip or conda package manager
            </li>
            <li className="flex gap-2">
              <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
              PostgreSQL 12+ (or SQLite for development)
            </li>
            <li className="flex gap-2">
              <CheckCircle size={18} className="text-green-400 mt-0.5 flex-shrink-0" />
              4GB RAM minimum (8GB recommended)
            </li>
          </ul>
        </div>

        {/* Step 1: Installation */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              1
            </div>
            <h3 className="text-xl font-bold">Install ArcticCodex</h3>
          </div>

          <p className="text-gray-400 mb-4">Install via pip (recommended for most users):</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4">
            pip install arcticcodex
          </code>

          <p className="text-gray-400 mb-2">Or install from source:</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono">
            git clone https://github.com/salisburytristan-arch/ArcticCodex.git
            <br />
            cd ArcticCodex
            <br />
            pip install -e .
          </code>
        </div>

        {/* Step 2: Initialize */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              2
            </div>
            <h3 className="text-xl font-bold">Create Your Vault</h3>
          </div>

          <p className="text-gray-400 mb-4">Initialize a new vault (knowledge base):</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4">
            arctic init --name my-vault --storage sqlite
          </code>

          <p className="text-gray-400 mb-4">For production, use PostgreSQL:</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono">
            arctic init --name my-vault --storage postgresql --db-url
            postgresql://user:pass@localhost/arctic
          </code>
        </div>

        {/* Step 3: Add Data */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              3
            </div>
            <h3 className="text-xl font-bold">Add Knowledge to Vault</h3>
          </div>

          <p className="text-gray-400 mb-4">Store your first frame (knowledge unit):</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4">
            arctic store --vault my-vault --text "Python is a high-level programming language" --tags
            programming,python
          </code>

          <p className="text-gray-400 mb-4">Or import from a file:</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono">
            arctic import --vault my-vault --file documents/knowledge.txt
          </code>
        </div>

        {/* Step 4: Query */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              4
            </div>
            <h3 className="text-xl font-bold">Query Your Vault</h3>
          </div>

          <p className="text-gray-400 mb-4">Search your vault:</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4">
            arctic search --vault my-vault --query "What is Python?"
          </code>

          <p className="text-gray-400 mb-4">Expected output:</p>
          <pre className="px-4 py-3 bg-black/50 border border-white/10 rounded text-green-400 text-sm font-mono">
            {`Frame ID: 0x1A2B3C4D
Content: Python is a high-level programming language
Confidence: 0.95
HMAC: ✓ Verified
Tags: programming, python`}
          </pre>
        </div>

        {/* Step 5: API Server */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-cyan-600/30 border border-cyan-500/50 flex items-center justify-center text-cyan-400 font-bold">
              5
            </div>
            <h3 className="text-xl font-bold">Start API Server (Optional)</h3>
          </div>

          <p className="text-gray-400 mb-4">Launch the REST API server:</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono mb-4">
            arctic serve --vault my-vault --port 8000
          </code>

          <p className="text-gray-400 mb-4">Test the API:</p>
          <code className="block px-4 py-3 bg-black/50 border border-white/10 rounded text-cyan-400 text-sm font-mono">
            curl http://localhost:8000/health
          </code>
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
              href="mailto:acrticasters@gmail.com"
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
                q: 'ImportError: No module named arcticcodex',
                a: 'Make sure you activated your virtual environment: source .venv/bin/activate',
              },
              {
                q: 'Permission denied when running arctic commands',
                a: 'You may need to use sudo or adjust file permissions: chmod +x ~/.local/bin/arctic',
              },
              {
                q: 'PostgreSQL connection refused',
                a: 'Check that PostgreSQL is running: sudo systemctl status postgresql',
              },
              {
                q: 'HMAC verification failed',
                a: 'Frame may be corrupted. Use arctic verify --vault my-vault to scan all frames.',
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
