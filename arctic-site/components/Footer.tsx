'use client';

import React from 'react';
import Link from 'next/link';
import { Github, Mail, Shield, FileText, Lock } from 'lucide-react';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-white/10 bg-black/50 mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        
        {/* Main Footer Content */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          
          {/* Brand */}
          <div>
            <h3 className="text-sm font-mono font-bold text-white mb-4">ARCTICCODEX</h3>
            <p className="text-xs text-gray-400 mb-4">
              Enterprise AI with trinary logic and forensic audit trails.
            </p>
            <div className="text-xs text-gray-500 font-mono">
              v1.0 • Production Ready
            </div>
          </div>

          {/* Product */}
          <div>
            <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-4">Product</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="#top" className="text-gray-400 hover:text-white transition">Overview</Link></li>
              <li><Link href="#specs" className="text-gray-400 hover:text-white transition">Features</Link></li>
              <li><Link href="/use-cases" className="text-gray-400 hover:text-white transition">Use Cases</Link></li>
              <li><Link href="/pricing" className="text-gray-400 hover:text-white transition">Pricing</Link></li>
              <li><Link href="/console" className="text-gray-400 hover:text-white transition">Console</Link></li>
            </ul>
          </div>

          {/* Resources */}
          <div>
            <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-4">Resources</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="/docs" className="text-gray-400 hover:text-white transition">Documentation</Link></li>
              <li><Link href="/docs/quickstart" className="text-gray-400 hover:text-white transition">Quickstart</Link></li>
              <li><Link href="/docs/api" className="text-gray-400 hover:text-white transition">API Reference</Link></li>
              <li><a href="https://github.com/salisburytristan-arch/ArcticCodex" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-white transition">GitHub</a></li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-xs font-mono font-bold text-white uppercase tracking-wider mb-4">Company</h4>
            <ul className="space-y-2 text-xs">
              <li><Link href="/security" className="text-gray-400 hover:text-white transition">Security</Link></li>
              <li><a href="mailto:acrticasters@gmail.com" className="text-gray-400 hover:text-white transition">Contact</a></li>
              <li><Link href="/privacy" className="text-gray-400 hover:text-white transition">Privacy</Link></li>
              <li><Link href="/terms" className="text-gray-400 hover:text-white transition">Terms</Link></li>
            </ul>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-white/5 my-8"></div>

        {/* Bottom Bar */}
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          
          {/* Copyright */}
          <div className="text-xs text-gray-500 font-mono">
            © {currentYear} ArcticCodex. Proprietary. All rights reserved.
          </div>

          {/* Status & Links */}
          <div className="flex items-center gap-6">
            <a
              href="/status"
              className="text-xs text-gray-500 hover:text-gray-400 font-mono transition flex items-center gap-1"
            >
              <div className="w-2 h-2 rounded-full bg-green-400"></div>
              Status
            </a>
            <a
              href="/security"
              className="text-xs text-gray-500 hover:text-gray-400 font-mono transition flex items-center gap-1"
            >
              <Shield size={12} />
              Security
            </a>
            <a
              href="mailto:security@arcticcodex.com"
              className="text-xs text-gray-500 hover:text-gray-400 font-mono transition"
            >
              Report a Vulnerability
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
