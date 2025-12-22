'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Database, Brain, CheckCircle, AlertCircle } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  citations?: string[];
  frame?: string;
}

export default function VaultIntegrationDemo() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'system',
      content: 'ArcticCodex Vault initialized. 5-tier memory system active.',
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [vaultStats, setVaultStats] = useState({
    documents: 247,
    facts: 1893,
    embeddings: 15420,
    frames: 89
  });

  const handleSendMessage = async () => {
    if (!input.trim() || isProcessing) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsProcessing(true);

    // Simulate agent processing
    setTimeout(() => {
      const agentResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: `Based on vault retrieval (BM25 + embeddings), I found relevant context. State Φ detected for uncertain claims requiring verification.`,
        timestamp: new Date(),
        citations: ['doc_142.txt', 'frame_0x4A2F'],
        frame: 'SUMMARY#0x7B3A'
      };

      setMessages(prev => [...prev, agentResponse]);
      setIsProcessing(false);
      
      // Update stats
      setVaultStats(prev => ({
        ...prev,
        facts: prev.facts + 1,
        frames: prev.frames + 1
      }));
    }, 2000);
  };

  return (
    <div className="w-full max-w-5xl mx-auto">
      {/* Vault Statistics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Documents', value: vaultStats.documents, icon: Database },
          { label: 'Facts', value: vaultStats.facts, icon: CheckCircle },
          { label: 'Embeddings', value: vaultStats.embeddings.toLocaleString(), icon: Brain },
          { label: 'Frames', value: vaultStats.frames, icon: AlertCircle }
        ].map((stat, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.1 }}
            className="bg-[#0a0a0a] border border-gray-800 rounded-lg p-4"
          >
            <div className="flex items-center justify-between mb-2">
              <stat.icon className="text-cyan-400" size={16} />
              <span className="text-2xl font-bold text-white">{stat.value}</span>
            </div>
            <div className="text-xs text-gray-500 font-mono">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Chat Interface */}
      <div className="bg-[#0a0a0a] border border-gray-800 rounded-lg overflow-hidden">
        {/* Header */}
        <div className="bg-[#111] px-4 py-3 border-b border-gray-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            <span className="text-sm font-mono text-gray-400">vault.agent.session</span>
          </div>
          <div className="text-xs text-gray-600 font-mono">5-TIER MEMORY ACTIVE</div>
        </div>

        {/* Messages */}
        <div className="h-96 overflow-y-auto p-4 space-y-4">
          <AnimatePresence>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[80%] ${
                  msg.role === 'user' 
                    ? 'bg-cyan-950/50 border-cyan-500/30' 
                    : msg.role === 'system'
                    ? 'bg-yellow-950/20 border-yellow-500/30'
                    : 'bg-white/[0.02] border-white/10'
                } border rounded-lg p-4`}>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-mono text-gray-500">
                      {msg.role.toUpperCase()}
                    </span>
                    {msg.frame && (
                      <span className="text-xs font-mono text-cyan-400">
                        {msg.frame}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-300">{msg.content}</div>
                  {msg.citations && (
                    <div className="mt-2 pt-2 border-t border-white/5">
                      <div className="text-xs text-gray-600 mb-1">Citations:</div>
                      <div className="flex flex-wrap gap-2">
                        {msg.citations.map((cite, idx) => (
                          <span 
                            key={idx}
                            className="text-xs font-mono bg-gray-900 px-2 py-1 rounded text-cyan-400"
                          >
                            {cite}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isProcessing && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex justify-start"
            >
              <div className="bg-white/[0.02] border border-white/10 rounded-lg p-4">
                <div className="flex items-center gap-2">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-75"></div>
                    <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse delay-150"></div>
                  </div>
                  <span className="text-xs text-gray-500 font-mono">
                    Retrieving from vault...
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </div>

        {/* Input */}
        <div className="border-t border-gray-800 p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Ask about your knowledge base..."
              className="flex-1 bg-black border border-gray-800 rounded px-4 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-cyan-500"
              disabled={isProcessing}
            />
            <button
              onClick={handleSendMessage}
              disabled={isProcessing || !input.trim()}
              className="bg-cyan-500 hover:bg-cyan-400 disabled:bg-gray-800 disabled:text-gray-600 text-black font-bold px-6 py-2 rounded transition-all flex items-center gap-2"
            >
              <Send size={16} />
            </button>
          </div>
          <div className="mt-2 text-xs text-gray-600 font-mono">
            Hybrid search: BM25 + embeddings | State Φ for uncertain claims
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-4 mt-6">
        {[
          { title: 'Hybrid Search', desc: 'BM25 keyword + vector embeddings' },
          { title: 'Frame Integrity', desc: 'HMAC signatures on every response' },
          { title: 'Memory Tiers', desc: 'Working → Episodic → Semantic → KB' }
        ].map((feature, idx) => (
          <div 
            key={idx}
            className="bg-white/[0.02] border border-white/10 rounded-lg p-4"
          >
            <div className="text-sm font-bold text-cyan-400 mb-1">{feature.title}</div>
            <div className="text-xs text-gray-500">{feature.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
