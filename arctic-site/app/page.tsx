'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Shield, Cpu, Database, Terminal, Lock, CheckCircle, Zap, GitBranch } from 'lucide-react';
import LogoTrinity from '../components/LogoTrinity';
import TrinaryDemo from '../components/TrinaryDemo';
import TeacherSystemDemo from '../components/TeacherSystemDemo';
import VaultIntegrationDemo from '../components/VaultIntegrationDemo';

export default function Home() {
  const [terminalLines, setTerminalLines] = useState<string[]>([]);
  
  // The Script Narrative (Integrity Breach Demo)
  useEffect(() => {
    const logs = [
      "Wait...",
      "> SYSTEM_INIT: ARCTIC_CODEX_TIER_0",
      "> MOUNT: VAULT_MEMORY [OK]",
      "> MOUNT: FORGE_NUMERICS [OK]",
      "> ACCESS: /memory/frames/0x4F2A",
      "> INJECTING_VECTOR: 'compaction_test.frame'",
      "> ...",
      "[WARN] INTEGRITY SCANNING...",
      "[ALERT] BIT ROT DETECTED. HASH MISMATCH.",
      "[DEFENSE] HMAC GATE LOCKED.",
      "[DEFENSE] RESPONSE HALTED.",
      "> SYSTEM INTEGRITY PRESERVED."
    ];

    let delay = 0;
    logs.forEach((log) => {
      delay += Math.random() * 800 + 400; // Random typing speed
      setTimeout(() => {
        setTerminalLines(prev => [...prev, log]);
      }, delay);
    });
  }, []);

  return (
    <main id="top" className="min-h-screen relative font-sans selection:bg-cyan-500/30">
      {/* Background Grid */}
      <div className="absolute inset-0 bg-grid z-0 pointer-events-none" />
      <div className="scanlines fixed inset-0 z-50 pointer-events-none opacity-20"></div>

      {/* Hero Section */}
      <section className="relative z-10 flex flex-col lg:flex-row items-center justify-between max-w-7xl mx-auto px-6 pt-20 pb-32 gap-12">
        
        {/* Left: Value Prop */}
        <div className="flex-1 space-y-8">
          <motion.div 
            initial={{ opacity: 0, y: 20 }} 
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/30 border border-cyan-800/50 text-cyan-400 text-xs font-mono tracking-widest uppercase"
          >
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            Enterprise AI Platform | Live
          </motion.div>
          
          <motion.h1 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold tracking-tight leading-[1.1]"
          >
            Audit-Ready <br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600 text-glow">
              Intelligence.
            </span>
          </motion.h1>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-lg text-gray-400 max-w-lg leading-relaxed"
          >
            Enterprise AI with <strong className="text-white">forensic audit trails</strong> and cryptographic integrity. 
            Handle uncertainty with <strong className="text-cyan-400">Φ-state reasoning</strong>. 
            HIPAA/SOC2-ready. Multi-teacher verification. Zero hallucination compliance.
            <br/><br/>
            <strong className="text-white">AI you can trust in regulated industries.</strong>
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex flex-wrap gap-4 pt-4"
          >
            <Link href="/console" className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold px-8 py-4 rounded-sm transition-all duration-300 flex items-center gap-2 hover:shadow-lg hover:shadow-cyan-500/30">
              <Terminal size={18} /> Try Now
            </Link>
            <a href="mailto:acrticasters@gmail.com?subject=ArcticCodex Demo Request" className="px-8 py-4 border border-white/10 hover:border-white/30 text-white/70 hover:text-white transition-all duration-300 font-mono text-sm flex items-center gap-2">
              <Lock size={18} /> Schedule Demo
            </a>
            <a href="/docs" className="px-8 py-4 border border-white/10 hover:border-white/30 text-white/70 hover:text-white transition-all duration-300 font-mono text-sm">
              Read Docs
            </a>
          </motion.div>
        </div>

        {/* Right: The Terminal (The Proof) */}
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }} 
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3, duration: 0.8 }}
          className="flex-1 w-full max-w-lg"
        >
          <div className="rounded-lg overflow-hidden border border-gray-800 bg-[#0a0a0a] shadow-2xl shadow-cyan-900/20">
            <div className="bg-[#111] px-4 py-2 border-b border-gray-800 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
              <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
              <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
              <div className="text-xs text-gray-600 font-mono ml-2">root@arctic-node:~</div>
            </div>
            <div className="p-6 font-mono text-sm h-[320px] overflow-y-auto flex flex-col justify-end bg-[#050505]">
              {terminalLines.map((line, i) => (
                <div key={i} className={`mb-1 whitespace-pre-wrap break-words ${
                  line.includes("ALERT") || line.includes("MISMATCH") ? "text-red-500 font-bold" :
                  line.includes("OK") || line.includes("PRESERVED") ? "text-green-400" :
                  line.includes("WARN") ? "text-yellow-400" : "text-gray-400"
                }`}>
                  {line}
                </div>
              ))}
              {terminalLines.length < 12 && (
                <div className="w-2 h-5 bg-cyan-500 animate-pulse mt-1"></div>
              )}
            </div>
          </div>
          <div className="flex justify-between mt-4 px-2 text-xs text-gray-600 font-mono">
             <div>SHA-256: VERIFIED</div>
             <div className="text-cyan-500">LATENCY: 12ms</div>
          </div>
        </motion.div>
      </section>

      {/* Metrics Strip */}
      <section className="border-y border-white/5 bg-white/[0.02]">
        <div className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { label: "Unit Tests", val: "79", icon: CheckCircle },
            { label: "Logic States", val: "⊙⊗Φ", icon: Zap },
            { label: "Architecture", val: "Tier-0", icon: Cpu },
            { label: "Teachers", val: "Multi", icon: GitBranch }
          ].map((stat, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              viewport={{ once: true }}
              className="flex flex-col items-center justify-center text-center"
            >
              <stat.icon className="w-6 h-6 text-gray-600 mb-4" />
              <span className="text-3xl font-bold font-mono tracking-tighter">{stat.val}</span>
              <span className="text-xs text-gray-500 uppercase tracking-widest mt-1">{stat.label}</span>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Logo Trinity Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl font-bold mb-4">The Logic Trinity</h2>
          <p className="text-gray-500 text-lg max-w-2xl mx-auto">
            Three states. One intelligence. The symbolic foundation of ForgeNumerics.
          </p>
        </motion.div>

        <div className="flex justify-center mb-12">
          <LogoTrinity size={200} showLabel={true} animated={true} />
        </div>

        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {[
            {
              symbol: '⊙',
              title: 'State 0',
              desc: 'Ground state. Absence. The foundation of all logical operations.',
              color: 'text-[#00FF41]'
            },
            {
              symbol: '⊗',
              title: 'State 1',
              desc: 'Power state. Presence. Truth verified and stored.',
              color: 'text-[#00FF41]'
            },
            {
              symbol: 'Φ',
              title: 'State Φ',
              desc: 'Paradox state. Uncertainty. The key to handling unknown truths.',
              color: 'text-white'
            }
          ].map((state, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              viewport={{ once: true }}
              className="border border-white/10 p-6 rounded-lg bg-white/[0.02] text-center hover:border-cyan-500/30 transition-all"
            >
              <div className={`text-5xl mb-4 ${state.color}`}>{state.symbol}</div>
              <h3 className="text-lg font-bold mb-2 text-cyan-400">{state.title}</h3>
              <p className="text-gray-400 text-sm">{state.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Trinary Demo Section */}
      <section id="trinary" className="relative z-10 bg-white/[0.01] border-y border-white/5 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Interactive Trinary Logic</h2>
            <p className="text-gray-500 text-lg">
              See how three-state reasoning handles uncertainty that binary logic cannot.
            </p>
          </motion.div>
          <TrinaryDemo />
        </div>
      </section>

      {/* Specs Section */}
      <section id="specs" className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="space-y-8"
        >
          <div>
            <h2 className="text-4xl font-bold mb-2">Technical Specifications</h2>
            <p className="text-gray-500 text-lg">Production-ready knowledge OS, built for defense.</p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            {[
              {
                title: "ForgeNumerics Language",
                desc: "Trinary-based symbolic codec with canonical frame format, deterministic serialization, and lossless compression. State Φ enables epistemic uncertainty."
              },
              {
                title: "Agent Vault",
                desc: "Air-gapped memory system with 5-tier architecture: working, episodic, semantic, procedural, and long-term KB storage."
              },
              {
                title: "Multi-Teacher System",
                desc: "Draft-Critique-Revise protocol with DeepSeek R1 integration. Quality scores averaging 0.917. Automated training pair generation."
              },
              {
                title: "Cryptographic Integrity",
                desc: "Real-time bit-rot scanning, HMAC validation gates, and corruption flagging at retrieval time. Every frame is signed."
              }
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.6, delay: i * 0.1 }}
                viewport={{ once: true }}
                className="border border-white/10 p-6 rounded-lg bg-white/[0.02] hover:border-cyan-500/30 transition-all"
              >
                <h3 className="text-lg font-bold mb-2 text-cyan-400">{item.title}</h3>
                <p className="text-gray-400">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Teacher System Demo Section */}
      <section id="teacher" className="relative z-10 bg-white/[0.01] border-y border-white/5 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-4xl font-bold mb-4">Multi-Teacher Orchestration</h2>
            <p className="text-gray-500 text-lg">
              Draft → Critique → Revise. Automated quality improvement through teacher feedback loops.
            </p>
          </motion.div>
          <TeacherSystemDemo />
        </div>
      </section>

      {/* Technology Stack Section */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="space-y-8"
        >
          <div className="text-center mb-12">
            <h2 className="text-4xl font-bold mb-2">Complete System Architecture</h2>
            <p className="text-gray-500 text-lg">79 passing tests. Production-ready. Local-first.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                title: "Core Runtime",
                items: ["Python 3.10+", "FastAPI + uvicorn", "Click CLI", "Pydantic validation"]
              },
              {
                title: "Intelligence Layer",
                items: ["ForgeNumerics frames", "DeepSeek R1 teachers", "Multi-model support", "Local inference"]
              },
              {
                title: "Storage & Security",
                items: ["PostgreSQL audit logs", "HMAC signatures", "Docker deployment", "Zero cloud dependencies"]
              }
            ].map((column, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: idx * 0.1 }}
                viewport={{ once: true }}
                className="border border-white/10 p-6 rounded-lg bg-white/[0.02]"
              >
                <h3 className="text-lg font-bold mb-4 text-cyan-400">{column.title}</h3>
                <ul className="space-y-2">
                  {column.items.map((item, i) => (
                    <li key={i} className="text-sm text-gray-400 flex items-center gap-2">
                      <div className="w-1.5 h-1.5 bg-cyan-400 rounded-full"></div>
                      {item}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </section>

      {/* Vault Integration Demo */}
      <section id="vault" className="relative z-10 max-w-7xl mx-auto px-6 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-12"
        >
          <h2 className="text-4xl font-bold mb-4">Agent Vault Integration</h2>
          <p className="text-gray-500 text-lg">
            5-tier memory architecture. Hybrid search. Real-time frame integrity verification.
          </p>
        </motion.div>
        <VaultIntegrationDemo />
      </section>

      {/* 
      {/* Footer */}
    </main>
  );
}
