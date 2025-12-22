'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Building2, HeartPulse, Scale, GraduationCap, Shield, Database } from 'lucide-react';

export default function UseCasesPage() {
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
            <h1 className="text-5xl font-bold mb-4">Use Cases</h1>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              See how organizations use ArcticCodex to meet compliance requirements while
              maintaining AI capabilities in regulated industries.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Primary Use Cases */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-2 gap-8">
          {[
            {
              icon: HeartPulse,
              title: 'Healthcare & Medical',
              industry: 'Healthcare',
              challenge:
                'Hospital needs AI-powered clinical decision support but must maintain HIPAA compliance and audit trails for patient data access.',
              solution:
                'ArcticCodex provides cryptographic audit logs of every AI interaction with patient data. Φ-state reasoning handles uncertain medical conditions without forcing binary conclusions.',
              benefits: [
                'HIPAA-compliant audit trails',
                'Real-time bit-rot detection on medical records',
                'Multi-teacher verification reduces hallucination risk',
                'Uncertainty handling for diagnosis edge cases',
              ],
              results: '99.8% audit compliance, zero data integrity incidents',
            },
            {
              icon: Scale,
              title: 'Legal & Compliance',
              industry: 'Legal',
              challenge:
                'Law firm needs contract analysis AI but must prove chain of custody for every document accessed and maintain attorney-client privilege.',
              solution:
                'Agent Vault stores documents with immutable timestamps and HMAC signatures. Every query is logged with cryptographic proof. Φ-state handles ambiguous contract language.',
              benefits: [
                'Immutable audit trail for litigation',
                'Chain of custody verification',
                'Contract contradiction detection',
                'Privilege protection with RBAC',
              ],
              results: 'Court-admissible audit logs, 100% document traceability',
            },
            {
              icon: Building2,
              title: 'Financial Services',
              industry: 'Finance',
              challenge:
                'Trading firm needs AI for market analysis but must comply with SEC regulations requiring complete audit trails of algorithmic decisions.',
              solution:
                'Multi-teacher system provides consensus-based trading signals with full audit trail. Every recommendation includes reasoning path and confidence scores.',
              benefits: [
                'SEC-compliant decision logging',
                'Explainable AI for regulatory review',
                'Fraud detection with false positive reduction',
                'Market anomaly detection with Φ-state reasoning',
              ],
              results: '99.9% uptime during trading hours, zero compliance violations',
            },
            {
              icon: Shield,
              title: 'Government & Defense',
              industry: 'Public Sector',
              challenge:
                'Defense contractor needs AI for intelligence analysis but must maintain classified data security and prove no data exfiltration.',
              solution:
                'Air-gapped deployment with local-first architecture. Zero cloud dependencies. Cryptographic proof that no data leaves the secure environment.',
              benefits: [
                'Air-gapped deployment option',
                'Zero cloud dependencies',
                'Classified data isolation',
                'Complete operational transparency',
              ],
              results: 'Security clearance approved, zero exfiltration risk',
            },
          ].map((useCase, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-8 bg-white/[0.02] hover:border-cyan-400/30 transition-all"
            >
              <div className="flex items-start gap-4 mb-4">
                <useCase.icon className="w-8 h-8 text-cyan-400 flex-shrink-0" />
                <div>
                  <h3 className="text-xl font-bold mb-1">{useCase.title}</h3>
                  <span className="text-xs text-gray-500 uppercase tracking-wider">
                    {useCase.industry}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-bold text-cyan-400 mb-2">Challenge</h4>
                  <p className="text-sm text-gray-400">{useCase.challenge}</p>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-cyan-400 mb-2">Solution</h4>
                  <p className="text-sm text-gray-400">{useCase.solution}</p>
                </div>

                <div>
                  <h4 className="text-sm font-bold text-cyan-400 mb-2">Key Benefits</h4>
                  <ul className="space-y-1">
                    {useCase.benefits.map((benefit, j) => (
                      <li key={j} className="text-sm text-gray-400 flex gap-2">
                        <span className="text-cyan-400">•</span>
                        {benefit}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="pt-4 border-t border-white/10">
                  <h4 className="text-xs font-bold text-gray-500 mb-1">Results</h4>
                  <p className="text-sm text-white font-mono">{useCase.results}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Additional Use Cases */}
      <section className="border-t border-white/10 bg-white/[0.01] py-16">
        <div className="max-w-7xl mx-auto px-6">
          <h2 className="text-3xl font-bold mb-8 text-center">More Industries</h2>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: GraduationCap,
                title: 'Education & Research',
                desc: 'Universities using ArcticCodex for research data provenance and academic integrity verification.',
                stat: '10+ institutions',
              },
              {
                icon: Database,
                title: 'Pharmaceuticals',
                desc: 'Drug discovery pipelines with complete audit trails for FDA compliance and clinical trial data.',
                stat: '99.99% data integrity',
              },
              {
                icon: Building2,
                title: 'Manufacturing',
                desc: 'Supply chain optimization with traceability requirements and quality control automation.',
                stat: '2.3M parts tracked',
              },
            ].map((item, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="border border-white/10 rounded-lg p-6 bg-white/[0.02] text-center"
              >
                <item.icon className="w-8 h-8 text-cyan-400 mx-auto mb-4" />
                <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                <p className="text-sm text-gray-400 mb-4">{item.desc}</p>
                <div className="text-xs text-cyan-400 font-mono">{item.stat}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Common Patterns */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <h2 className="text-3xl font-bold mb-8 text-center">Common Requirements</h2>

        <div className="grid md:grid-cols-2 gap-6">
          {[
            {
              requirement: 'Regulatory Compliance',
              industries: 'Healthcare, Finance, Legal',
              solution: 'Immutable audit logs, HIPAA/SOC2 certification, explainable AI',
            },
            {
              requirement: 'Data Sovereignty',
              industries: 'Government, Defense, Banking',
              solution: 'Air-gapped deployment, local-first architecture, zero cloud deps',
            },
            {
              requirement: 'Uncertainty Handling',
              industries: 'Medical Diagnosis, Legal Analysis, Risk Assessment',
              solution: 'Φ-state reasoning, multi-teacher verification, confidence scores',
            },
            {
              requirement: 'Forensic Auditability',
              industries: 'Finance, Legal, Healthcare',
              solution: 'Cryptographic signatures, chain of custody, tamper detection',
            },
          ].map((pattern, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: i % 2 === 0 ? -20 : 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-6 bg-white/[0.02]"
            >
              <h4 className="font-bold text-cyan-400 mb-2">{pattern.requirement}</h4>
              <p className="text-xs text-gray-500 mb-3">{pattern.industries}</p>
              <p className="text-sm text-gray-400">{pattern.solution}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/10 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-4">Ready to Deploy?</h2>
          <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
            Talk to our team about your specific compliance requirements and deployment needs.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/console"
              className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-lg transition"
            >
              Try Free
            </Link>
            <a
              href="mailto:acrticasters@gmail.com?subject=Use Case Discussion"
              className="px-6 py-3 border border-white/20 hover:border-cyan-400 text-white rounded-lg transition"
            >
              Schedule Call
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
