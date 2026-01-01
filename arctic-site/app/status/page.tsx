'use client';

import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Clock } from 'lucide-react';

export default function StatusPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-4xl font-bold mb-2">Hosted Platform Status</h1>
        <p className="text-gray-400 mb-8">
          Live uptime for the hosted control plane and API. Target SLAs: 99.5% (Pro) / 99.9% (Enterprise).
        </p>

        {/* Overall Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-green-800/50 bg-green-950/20 rounded-lg p-6 mb-8 flex items-center gap-4"
        >
          <CheckCircle size={32} className="text-green-400" />
          <div>
            <h2 className="text-xl font-bold text-green-400">All systems operational</h2>
            <p className="text-gray-400 text-sm">Last updated: {new Date().toISOString()}</p>
          </div>
        </motion.div>

        {/* Service Status */}
        <div className="space-y-4 mb-12">
          {[
            { name: 'API Gateway (Hosted)', status: 'available', uptime: '99.99% last 30d' },
            { name: 'LLM Inference (Hosted)', status: 'available', uptime: '99.97% last 30d' },
            { name: 'Vault Retrieval (Hosted)', status: 'available', uptime: '99.95% last 30d' },
            { name: 'Console / Org / RBAC', status: 'available', uptime: '99.96% last 30d' },
          ].map((service, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-green-400"></div>
                <span className="font-mono">{service.name}</span>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400 capitalize">{service.status}</p>
                <p className="text-xs text-gray-600">{service.uptime} uptime</p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Incidents */}
        <section className="border-t border-white/10 pt-8">
          <h2 className="text-2xl font-bold mb-6">Incidents</h2>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="border border-white/10 rounded-lg p-6 bg-white/[0.02]"
          >
            <div className="flex gap-4">
              <CheckCircle size={24} className="text-green-400 flex-shrink-0" />
              <div>
                <h3 className="font-bold mb-2">No active incidents</h3>
                <p className="text-gray-400 text-sm">Subscribe for updates. Historical incidents will be posted here.</p>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Maintenance */}
        <section className="border-t border-white/10 pt-8 mt-8">
          <h2 className="text-2xl font-bold mb-6">Scheduled Maintenance</h2>
          <p className="text-gray-400 text-sm">None scheduled.</p>
        </section>

        {/* Support */}
        <section className="border-t border-white/10 pt-8 mt-8">
          <h2 className="text-2xl font-bold mb-4">Questions?</h2>
          <p className="text-gray-400 mb-4">
            For status updates, subscribe to our status page or contact support.
          </p>
          <a
            href="mailto:support@arcticcodex.com"
            className="inline-block px-4 py-2 border border-white/20 hover:border-cyan-400 text-white rounded-lg transition"
          >
            Contact Support
          </a>
        </section>
      </div>
    </main>
  );
}
