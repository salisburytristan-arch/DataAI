'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Menu, X } from 'lucide-react';

export default function Header() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState('top');

  // Listen to scroll for active section highlighting
  React.useEffect(() => {
    const handleScroll = () => {
      const sections = ['top', 'trinary', 'specs', 'teacher', 'vault'];
      
      for (const section of sections) {
        const element = document.getElementById(section);
        if (element) {
          const rect = element.getBoundingClientRect();
          if (rect.top <= 120 && rect.bottom >= 120) {
            setActiveSection(section);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { label: 'Try Chat', href: '/demo', id: 'demo', highlight: true },
    { label: 'Product', href: '#top', id: 'top' },
    { label: 'How It Works', href: '#specs', id: 'specs' },
    { label: 'Docs', href: '/docs', id: 'docs' },
    { label: 'Security', href: '/security', id: 'security' },
    { label: 'Pricing', href: '/pricing', id: 'pricing' },
  ];

  const isActive = (id: string) => activeSection === id;

  return (
    <header className="sticky top-0 z-50 w-full bg-white/80 backdrop-saturate-150 border-b border-black/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0 group">
            <div className="text-sm font-mono font-bold text-slate-900 group-hover:text-cyan-600 transition">
              ARCTIC<span className="text-cyan-400">CODEX</span>
            </div>
            <span className="hidden sm:inline text-xs text-gray-600 border border-gray-300 px-2 py-1 rounded group-hover:border-cyan-400 transition">
              FORGE NUMERICS
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.id}
                href={item.href}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`text-sm font-mono transition-colors relative py-2 px-2 ${
                  item.highlight
                    ? 'text-cyan-600 font-bold'
                    : isActive(item.id)
                    ? 'text-cyan-600'
                    : 'text-gray-700 hover:text-gray-900'
                }`}
              >
                {item.label}
                {isActive(item.id) && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-cyan-600"></div>
                )}
              </a>
            ))}
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              href="/demo"
              className="px-4 py-2 rounded text-sm font-mono font-bold bg-cyan-500 text-white hover:bg-cyan-600 transition-all shadow-sm"
            >
              Try Chat
            </Link>
            <Link
              href="/console"
              className="px-4 py-2 rounded text-sm font-mono text-slate-900 border border-gray-300 hover:border-cyan-400 hover:bg-cyan-50 transition-all"
            >
              Console
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 text-gray-400 hover:text-white transition"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <nav className="md:hidden border-t border-white/10 py-4 space-y-2">
            {navItems.map((item) => (
              <a
                key={item.id}
                href={item.href}
                onClick={() => setIsMobileMenuOpen(false)}
                className={`block px-4 py-2 rounded text-sm font-mono transition-colors ${
                  isActive(item.id)
                    ? 'bg-cyan-400/20 text-cyan-400'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {item.label}
              </a>
            ))}
            <div className="border-t border-white/10 pt-4 mt-4 space-y-2">
              <a
                href="mailto:acrticasters@gmail.com?subject=Request%20Demo"
                className="block px-4 py-2 rounded text-sm font-mono text-white border border-white/20 hover:border-cyan-400 text-center transition-all"
              >
                Request Demo
              </a>
              <Link
                href="/console"
                className="block px-4 py-2 rounded text-sm font-mono font-bold bg-cyan-500 text-black hover:bg-cyan-400 text-center transition-all"
              >
                Console
              </Link>
            </div>
          </nav>
        )}
      </div>
    </header>
  );
}
