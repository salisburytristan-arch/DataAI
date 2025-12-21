'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AgentConsole() {
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState<string[]>([]);
  const [phaseOutput, setPhaseOutput] = useState<any>(null);
  const [audit, setAudit] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function callApi(path: string, options: RequestInit = {}) {
    setError(null);
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {}),
      },
    });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(txt || res.statusText);
    }
    return res.json();
  }

  async function sendChat() {
    if (!message.trim()) return;
    setLoading(true);
    try {
      const data = await callApi('/chat', {
        method: 'POST',
        body: JSON.stringify({ message, org_id: 'demo_org', user_id: 'demo_user', roles: ['admin'] }),
      });
      setChatLog((prev) => [...prev, `You: ${message}`, `Agent: ${data.text}`]);
      setMessage('');
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function runPhase(num: number) {
    setLoading(true);
    try {
      const data = await callApi(`/phase/${num}`, {
        method: 'POST',
        body: JSON.stringify({ org_id: 'demo_org', user_id: 'demo_user', roles: ['admin'], export: true }),
      });
      setPhaseOutput(data);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadAudit() {
    setLoading(true);
    try {
      const data = await callApi('/audit');
      setAudit(data || []);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadAudit();
  }, []);

  return (
    <main className="min-h-screen bg-black text-gray-100 p-6 space-y-6">
      <nav className="flex flex-wrap items-center justify-between gap-3 border border-white/10 bg-white/5 px-4 py-3 rounded">
        <div className="text-lg font-mono font-bold tracking-tight">
          <Link href="/" className="hover:text-cyan-400 transition">ARCTIC<span className="text-cyan-400">CODEX</span></Link>
          <span className="text-[11px] ml-2 text-gray-500 border border-gray-700 px-2 py-1 rounded">Agent Vault</span>
        </div>
        <div className="flex items-center gap-3 text-sm font-mono">
          <Link href="/" className="px-3 py-2 border border-white/10 hover:border-white/30 rounded">← Back</Link>
          <a href="mailto:ArctiCasters@gmail.com" className="px-3 py-2 border border-white/10 hover:border-cyan-400 rounded">Contact</a>
        </div>
      </nav>

      <header className="flex flex-col gap-2">
        <h1 className="text-3xl font-bold">Agent Vault Console</h1>
        <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400">
          <p>Interact with the AGI, run phases, and inspect audit logs.</p>
          <span className="px-2 py-1 rounded border border-white/10 bg-white/5 text-xs">API: {API_URL}</span>
        </div>
      </header>

      {error && <div className="rounded border border-red-500/50 bg-red-500/10 px-3 py-2 text-sm">{error}</div>}

      <section className="grid md:grid-cols-2 gap-6">
        <div className="rounded border border-white/10 p-4 space-y-3 bg-white/5">
          <h2 className="text-xl font-semibold">Chat</h2>
          <div className="flex gap-2">
            <input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Ask the agent..."
              className="flex-1 rounded bg-black/40 border border-white/10 px-3 py-2"
            />
            <button onClick={sendChat} disabled={loading} className="px-4 py-2 bg-cyan-500 text-black font-semibold rounded">
              Send
            </button>
          </div>
          <div className="h-56 overflow-auto text-sm bg-black/40 border border-white/5 rounded p-3 space-y-1">
            {chatLog.length === 0 && <div className="text-gray-500">No messages yet.</div>}
            {chatLog.map((line, i) => (
              <div key={i}>{line}</div>
            ))}
          </div>
        </div>

        <div className="rounded border border-white/10 p-4 space-y-3 bg-white/5">
          <h2 className="text-xl font-semibold">Run Phase</h2>
          <div className="flex gap-2">
            {[30, 31, 40].map((n) => (
              <button
                key={n}
                onClick={() => runPhase(n)}
                disabled={loading}
                className="px-3 py-2 bg-white/10 hover:bg-white/20 text-sm rounded"
              >
                Phase {n}
              </button>
            ))}
          </div>
          <div className="text-xs bg-black/40 border border-white/5 rounded p-3 h-56 overflow-auto">
            {phaseOutput ? <pre>{JSON.stringify(phaseOutput, null, 2)}</pre> : <div className="text-gray-500">No phase run yet.</div>}
          </div>
        </div>
      </section>

      <section className="rounded border border-white/10 p-4 space-y-3 bg-white/5">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold">Audit Log</h2>
          <button onClick={loadAudit} disabled={loading} className="px-3 py-2 bg-white/10 hover:bg-white/20 text-sm rounded">Refresh</button>
        </div>
        <div className="overflow-auto">
          <table className="min-w-full text-xs">
            <thead className="text-gray-400">
              <tr>
                <th className="text-left p-2">Time</th>
                <th className="text-left p-2">Action</th>
                <th className="text-left p-2">Resource</th>
                <th className="text-left p-2">Result</th>
              </tr>
            </thead>
            <tbody>
              {audit.length === 0 && (
                <tr>
                  <td colSpan={4} className="p-2 text-gray-500">No audit entries yet.</td>
                </tr>
              )}
              {audit.map((a, idx) => (
                <tr key={idx} className="border-t border-white/5">
                  <td className="p-2 text-gray-300">{a.timestamp}</td>
                  <td className="p-2 text-gray-300">{a.action}</td>
                  <td className="p-2 text-gray-300">{a.resource}</td>
                  <td className="p-2 text-gray-300">{a.result}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}
