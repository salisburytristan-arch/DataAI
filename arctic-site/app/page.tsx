'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Shield, Cpu, Database, Terminal, Lock, CheckCircle } from 'lucide-react';

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

      {/* Navbar */}
      <nav className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 px-8 py-6 border-b border-white/5 bg-black/50 backdrop-blur-md sticky top-0">
        <div className="flex items-center gap-3">
          <div className="text-xl font-mono font-bold tracking-tighter text-white">
            ARCTIC<span className="text-cyan-400">CODEX</span>
            <span className="text-xs ml-2 text-gray-500 border border-gray-700 px-2 py-1 rounded">V.1.0</span>
          </div>
          <span className="text-[11px] text-gray-500 font-mono border border-gray-800 px-2 py-1 rounded uppercase">Enterprise AI</span>
        </div>

        <div className="flex items-center gap-6 text-sm font-mono text-gray-400">
          <Link href="#top" className="hover:text-white transition">HOME</Link>
          <a href="#specs" className="hover:text-white transition">SPECS</a>
          <Link href="/agent" className="hover:text-white transition">CONSOLE</Link>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/agent" className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold px-5 py-2 rounded-sm transition-all duration-300 text-sm">
            Launch Console
          </Link>
          <a href="mailto:acrticasters@gmail.com" className="bg-white/5 hover:bg-cyan-500/10 border border-white/10 hover:border-cyan-400 text-sm font-mono px-4 py-2 transition-all duration-300">
            CONTACT_SALES
          </a>
        </div>
      </nav>

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
            Sovereign <br />
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
            Local-first enterprise AI agents with policy-driven governance. 
            40-phase reasoning pipeline. HIPAA/SOC2-ready. On-premise deployment.
            <br/><br/>
            <strong className="text-white">Compliance teams actually approve it.</strong>
          </motion.p>

          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex flex-wrap gap-4 pt-4"
          >
            <Link href="/agent" className="bg-cyan-500 hover:bg-cyan-400 text-black font-bold px-8 py-4 rounded-sm transition-all duration-300 flex items-center gap-2 hover:shadow-lg hover:shadow-cyan-500/30">
              <Terminal size={18} /> Launch Console
            </Link>
            <a href="mailto:acrticasters@gmail.com?subject=ArcticCodex Demo Request" className="px-8 py-4 border border-white/10 hover:border-white/30 text-white/70 hover:text-white transition-all duration-300 font-mono text-sm flex items-center gap-2">
              <Lock size={18} /> Schedule Demo
            </a>
            <a href="#specs" className="px-8 py-4 border border-white/10 hover:border-white/30 text-white/70 hover:text-white transition-all duration-300 font-mono text-sm">
              VIEW_SPECS
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
            { label: "Unit Tests", val: "41", icon: CheckCircle },
            { label: "Security", val: "HMAC", icon: Shield },
            { label: "Architecture", val: "Tier-0", icon: Cpu },
            { label: "Dependencies", val: "Minimal", icon: Database }
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
                title: "Vault",
                desc: "Air-gapped memory system with cryptographic chunk verification and tombstone-based soft deletes."
              },
              {
                title: "ForgeNumerics",
                desc: "Self-describing canonical frame format with deterministic serialization and lossless compression."
              },
              {
                title: "Integrity Detection",
                desc: "Real-time bit-rot scanning, HMAC validation gates, and corruption flagging at retrieval time."
              },
              {
                title: "Zero Dependencies",
                desc: "Pure Python implementation. No external ML frameworks, no API calls, no licensing entropy."
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

      {/* Footer */}
      <footer className="py-12 text-center text-gray-600 text-sm font-mono border-t border-white/5 mt-20">
        <p>ARCTIC_CODEX // ASSET_ID: AC-85M // PROPERTY_OF_HOLDER</p>
      </footer>
    </main>
  );
}
