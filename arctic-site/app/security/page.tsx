'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Check, Shield, Lock, Eye, AlertCircle } from 'lucide-react';

export default function SecurityPage() {
  return (
    <main className="min-h-screen">
      {/* Hero */}
      <section className="border-b border-white/10 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center"
          >
            <h1 className="text-5xl font-bold mb-4">Security & Compliance</h1>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Hosted, audit-ready platform with cryptographic integrity. Transparent compliance status with verifiable receipts.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Compliance Badges */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-b border-white/10">
        <h2 className="text-2xl font-bold mb-8 text-center">Certifications & Standards</h2>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { label: 'SOC 2 (in progress)', icon: '⧗' },
            { label: 'HIPAA BAA (available on request)', icon: '🏥' },
            { label: 'GDPR-aligned (DPA available)', icon: '🔒' },
            { label: 'Encryption (AES-256 / TLS 1.3)', icon: '🔐' },
          ].map((cert, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-6 text-center bg-white/[0.02]"
            >
              <div className="text-4xl mb-2">{cert.icon}</div>
              <p className="font-bold">{cert.label}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Security Features */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-bold mb-8">Security Architecture</h2>

        <div className="grid md:grid-cols-2 gap-8">
          {[
            {
              title: 'Cryptographic Integrity',
              icon: Lock,
              points: [
                'HMAC-SHA256 signing on all frames',
                'Real-time bit-rot detection',
                'SHA-256 verification gates at retrieval',
                'Quantum-resistant signature prep',
              ],
            },
            {
              title: 'Data Protection',
              icon: Shield,
              points: [
                'AES-256-GCM encryption at rest',
                'TLS 1.3 for all transport',
                'Salted key derivation (Argon2id)',
                'Hardware security module (HSM) support',
              ],
            },
            {
              title: 'Access Control',
              icon: Eye,
              points: [
                'Role-based access control (RBAC)',
                'Resource-level permissions',
                'Audit logging of all operations',
                'Immutable audit trail (append-only)',
              ],
            },
            {
              title: 'Operational Security',
              icon: AlertCircle,
              points: [
                'Hosted with private tenancy; on-prem optional for Enterprise',
                'Network segmentation and VPC peering',
                'Immutable audit logging with exportable receipts',
                'Vulnerability disclosure program',
              ],
            },
          ].map((feature, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-8 bg-white/[0.02]"
            >
              <feature.icon className="w-8 h-8 text-cyan-400 mb-4" />
              <h3 className="text-lg font-bold mb-4">{feature.title}</h3>
              <ul className="space-y-2">
                {feature.points.map((point, j) => (
                  <li key={j} className="text-sm text-gray-400 flex gap-2">
                    <Check size={16} className="text-green-400 mt-0.5 flex-shrink-0" />
                    {point}
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Threat Model */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-t border-white/10">
        <h2 className="text-2xl font-bold mb-8">Threat Model & Mitigations</h2>

        <div className="space-y-6">
          {[
            {
              threat: 'Unauthorized Data Access',
              mitigation: 'All data encrypted at rest. Role-based access controls. Audit logging.',
            },
            {
              threat: 'Data Corruption (Bit Rot)',
              mitigation: 'HMAC gates on all frames. Real-time hash verification. Redundancy.',
            },
            {
              threat: 'Insider Threats',
              mitigation: 'Immutable audit logs. Resource-level permissions. MFA for console.',
            },
            {
              threat: 'Man-in-the-Middle Attacks',
              mitigation: 'Enforced TLS 1.3. Certificate pinning. HSTS headers.',
            },
            {
              threat: 'Inference Model Poisoning',
              mitigation: 'Multi-teacher verification. Output validation. Flagged anomalies.',
            },
            {
              threat: 'Supply Chain Compromise',
              mitigation: 'Signed releases. Dependency scanning. SBOMs provided.',
            },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-6 flex gap-6 bg-white/[0.02]"
            >
              <AlertCircle className="text-red-400 flex-shrink-0 mt-1" size={20} />
              <div className="flex-1">
                <h4 className="font-bold mb-1">{item.threat}</h4>
                <p className="text-sm text-gray-400">{item.mitigation}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Compliance */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-t border-white/10">
        <h2 className="text-2xl font-bold mb-8">Regulatory Compliance</h2>

        <div className="space-y-6">
          {[
            {
              reg: 'SOC 2',
              details:
                'Type II audit in progress; mapped controls for security/availability. Reports shared under NDA.',
            },
            {
              reg: 'HIPAA',
              details:
                'BAA available for Enterprise. PHI encryption, access controls, audit logging. Hosted in HIPAA-aligned regions.',
            },
            {
              reg: 'GDPR',
              details:
                'DPA available. EU/US data residency options. Data subject rights honored (access, erasure, portability).',
            },
            {
              reg: 'CCPA',
              details:
                'Consumer rights respected; opt-out mechanisms; subprocessors listed in Trust Center.',
            },
          ].map((item, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-6 bg-white/[0.02]"
            >
              <h4 className="font-bold text-cyan-400 mb-2">{item.reg}</h4>
              <p className="text-gray-400 text-sm">{item.details}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Reporting */}
      <section className="max-w-7xl mx-auto px-6 py-16 border-t border-white/10">
        <div className="bg-white/[0.02] border border-white/10 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold mb-4">Trust Center</h2>
          <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
            Review our security posture, subprocessors, data flow, and disclosure process. Evidence shared under NDA for Enterprise.
          </p>
          <div className="flex gap-3 justify-center flex-wrap">
            <a
              href="/security/trust-center"
              className="inline-block px-6 py-2 border border-white/20 hover:border-cyan-400 text-white rounded-lg transition"
            >
              View Trust Center
            </a>
            <a
              href="/security/vulnerability-disclosure"
              className="inline-block px-6 py-2 border border-white/20 hover:border-cyan-400 text-white rounded-lg transition"
            >
              Vulnerability Disclosure Policy
            </a>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/10 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready for Enterprise?</h2>
          <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
            Contact our team for detailed security assessments, BAAs, and deployment support.
          </p>
          <a
            href="mailto:acrticasters@gmail.com"
            className="inline-block px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-lg transition"
          >
            Contact Sales
          </a>
        </div>
      </section>
    </main>
  );
}
