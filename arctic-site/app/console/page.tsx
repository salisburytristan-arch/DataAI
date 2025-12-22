'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Mail, Check, Lock, ArrowRight, AlertCircle, Loader } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ConsolePage() {
  const [authState, setAuthState] = useState<'init' | 'email' | 'verify' | 'authenticated'>('init');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [chatLog, setChatLog] = useState<Array<{ role: 'user' | 'assistant'; text: string }>>([]);

  // Load auth from localStorage on mount
  useEffect(() => {
    const storedAuth = localStorage.getItem('arcticcodex_auth');
    if (storedAuth) {
      try {
        const parsed = JSON.parse(storedAuth);
        if (parsed.email && parsed.token) {
          setAuthState('authenticated');
          setEmail(parsed.email);
        }
      } catch (e) {
        localStorage.removeItem('arcticcodex_auth');
      }
    }
  }, []);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setError(null);

    // Simulate email sending
    setTimeout(() => {
      localStorage.setItem(
        'arcticcodex_auth_pending',
        JSON.stringify({ email, timestamp: Date.now() })
      );
      setAuthState('verify');
      setLoading(false);
    }, 1500);
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (code !== '123456') {
      // For demo: accept code 123456
      setError('Invalid verification code');
      return;
    }

    setLoading(true);
    setError(null);

    setTimeout(() => {
      const token = `token_${Date.now()}`;
      localStorage.setItem('arcticcodex_auth', JSON.stringify({ email, token }));
      localStorage.removeItem('arcticcodex_auth_pending');
      setAuthState('authenticated');
      setCode('');
      setLoading(false);
      // Add welcome message
      setChatLog([
        {
          role: 'assistant',
          text: `Welcome back, ${email.split('@')[0]}! I'm your ArcticCodex console assistant. Try asking me anything about your vault or running an audit.`,
        },
      ]);
    }, 1500);
  };

  const handleLogout = () => {
    localStorage.removeItem('arcticcodex_auth');
    setAuthState('init');
    setEmail('');
    setChatLog([]);
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const userMessage = message;
    setChatLog((prev) => [...prev, { role: 'user', text: userMessage }]);
    setMessage('');
    setLoading(true);

    // Simulate API call with demo responses
    setTimeout(() => {
      const responses = [
        'I scanned your vault frames. All 1,247 frames passed HMAC validation with zero corruption detected.',
        'Your agent has processed 342 requests this month with 99.2% success rate. Average inference latency: 87ms.',
        'Running audit log extraction... Found 18 policy violations in the past week. All have been flagged for review.',
        'Vault statistics: 5.2GB of encrypted frames across 23 collections. Memory fragmentation: 3.2%. Status: Optimal.',
        'Your most frequently accessed knowledge domains: Medicine (34%), Finance (28%), Legal (21%), Technology (17%).',
      ];
      const randomResponse =
        responses[Math.floor(Math.random() * responses.length)];
      setChatLog((prev) => [...prev, { role: 'assistant', text: randomResponse }]);
      setLoading(false);
    }, 1200);
  };

  // === AUTH SCREENS ===

  if (authState === 'init') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md space-y-8"
        >
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-2">ArcticCodex Console</h1>
            <p className="text-gray-400">Secure access to your audit-ready intelligence.</p>
          </div>

          <div className="border border-white/10 rounded-lg p-8 bg-white/[0.02] space-y-6">
            <form onSubmit={handleEmailSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-mono text-gray-400 mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@company.com"
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:border-cyan-400 focus:outline-none transition text-white placeholder-gray-500"
                  required
                />
              </div>

              <button
                type="submit"
                disabled={!email || loading}
                className="w-full bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-600 text-black font-bold py-2 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader size={18} className="animate-spin" /> Sending...
                  </>
                ) : (
                  <>
                    <Mail size={18} /> Send Magic Link
                  </>
                )}
              </button>
            </form>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/10"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-black text-gray-400">Demo Code</span>
              </div>
            </div>

            <div className="p-4 bg-cyan-950/20 border border-cyan-800/30 rounded-lg">
              <p className="text-xs text-gray-400 mb-2">For testing, use code:</p>
              <p className="text-lg font-mono text-cyan-400 font-bold">123456</p>
            </div>
          </div>

          <p className="text-center text-xs text-gray-500">
            By accessing this console, you agree to our{' '}
            <Link href="/terms" className="text-cyan-400 hover:underline">
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link href="/privacy" className="text-cyan-400 hover:underline">
              Privacy Policy
            </Link>
            .
          </p>
        </motion.div>
      </div>
    );
  }

  if (authState === 'verify') {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="w-full max-w-md space-y-8"
        >
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-2">Verify Email</h1>
            <p className="text-gray-400">
              Enter the 6-digit code sent to <strong>{email}</strong>
            </p>
          </div>

          <div className="border border-white/10 rounded-lg p-8 bg-white/[0.02] space-y-6">
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <div>
                <label className="block text-sm font-mono text-gray-400 mb-2">
                  Verification Code
                </label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                  className="w-full px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:border-cyan-400 focus:outline-none transition text-white placeholder-gray-500 text-center text-2xl tracking-widest font-mono"
                  required
                />
              </div>

              {error && (
                <div className="p-3 bg-red-950/30 border border-red-800/50 rounded-lg flex gap-2">
                  <AlertCircle size={16} className="text-red-400 mt-0.5" />
                  <p className="text-sm text-red-400">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={code.length !== 6 || loading}
                className="w-full bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-600 text-black font-bold py-2 rounded-lg transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <Loader size={18} className="animate-spin" /> Verifying...
                  </>
                ) : (
                  <>
                    <Check size={18} /> Verify
                  </>
                )}
              </button>
            </form>

            <button
              onClick={() => {
                setAuthState('init');
                setCode('');
                setError(null);
              }}
              className="w-full text-gray-400 hover:text-white text-sm transition"
            >
              Back to Email
            </button>
          </div>
        </motion.div>
      </div>
    );
  }

  // === AUTHENTICATED CONSOLE ===

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <div className="border-b border-white/10 bg-white/[0.02] px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Lock size={20} className="text-cyan-400" />
            <div>
              <p className="text-sm text-gray-400">Authenticated as</p>
              <p className="font-mono text-white font-bold">{email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm border border-white/10 hover:border-red-400/50 text-gray-400 hover:text-red-400 transition rounded-lg"
          >
            Sign Out
          </button>
        </div>
      </div>

      {/* Main Console */}
      <div className="flex-1 max-w-7xl mx-auto w-full px-6 py-8 flex flex-col">
        <div className="grid md:grid-cols-3 gap-6 mb-8">
          {[
            { label: 'Vault Frames', value: '1,247', status: 'Verified' },
            { label: 'Monthly Requests', value: '342', status: 'Healthy' },
            { label: 'Policy Violations', value: '18', status: 'Flagged' },
          ].map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className="border border-white/10 rounded-lg p-6 bg-white/[0.02]"
            >
              <p className="text-sm text-gray-400 mb-2">{stat.label}</p>
              <div className="flex items-end justify-between">
                <p className="text-3xl font-bold">{stat.value}</p>
                <span className="text-xs px-2 py-1 rounded bg-green-900/30 text-green-400 border border-green-800/50">
                  {stat.status}
                </span>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Chat Interface */}
        <div className="flex-1 border border-white/10 rounded-lg bg-white/[0.02] flex flex-col overflow-hidden">
          {/* Chat Messages */}
          <div className="flex-1 overflow-y-auto p-6 space-y-4">
            {chatLog.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <p className="text-gray-500 mb-2">No messages yet</p>
                  <p className="text-xs text-gray-600">Start a conversation with the ArcticCodex assistant</p>
                </div>
              </div>
            ) : (
              chatLog.map((msg, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-xs px-4 py-2 rounded-lg ${
                      msg.role === 'user'
                        ? 'bg-cyan-600/30 text-white border border-cyan-500/50'
                        : 'bg-white/5 text-gray-300 border border-white/10'
                    }`}
                  >
                    <p className="text-sm">{msg.text}</p>
                  </div>
                </motion.div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="px-4 py-2 rounded-lg bg-white/5 border border-white/10">
                  <div className="flex gap-2">
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce"></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                    <div className="w-2 h-2 rounded-full bg-gray-400 animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Chat Input */}
          <div className="border-t border-white/10 p-4">
            <form onSubmit={handleSendChat} className="flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask about your vault, requests, or audit logs..."
                className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg focus:border-cyan-400 focus:outline-none transition text-white placeholder-gray-500 text-sm"
                disabled={loading}
              />
              <button
                type="submit"
                disabled={!message.trim() || loading}
                className="px-4 py-2 bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-600 text-black font-bold rounded-lg transition-all flex items-center gap-2"
              >
                <ArrowRight size={16} />
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
