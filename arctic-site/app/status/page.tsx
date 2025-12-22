'use client';

import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Clock } from 'lucide-react';

export default function StatusPage() {
  return (
    <main className="min-h-screen py-16">
      <div className="max-w-4xl mx-auto px-6">
        <h1 className="text-4xl font-bold mb-2">System Status</h1>
        <p className="text-gray-400 mb-8">
          Real-time status of all ArcticCodex services. Uptime: <strong>99.98%</strong> (30 days)
        </p>

        {/* Overall Status */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="border border-green-800/50 bg-green-950/20 rounded-lg p-6 mb-8 flex items-center gap-4"
        >
          <CheckCircle size={32} className="text-green-400" />
          <div>
            <h2 className="text-xl font-bold text-green-400">All Systems Operational</h2>
            <p className="text-gray-400 text-sm">Last updated: 2 minutes ago</p>
          </div>
        </motion.div>

        {/* Service Status */}
        <div className="space-y-4 mb-12">
          {[
            { name: 'Console Web', status: 'operational', uptime: '100%' },
            { name: 'API Gateway', status: 'operational', uptime: '99.99%' },
            { name: 'Vault Storage', status: 'operational', uptime: '99.98%' },
            { name: 'Audit Logs', status: 'operational', uptime: '100%' },
            { name: 'Authentication', status: 'operational', uptime: '99.95%' },
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
          <h2 className="text-2xl font-bold mb-6">Incidents (30 Days)</h2>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="border border-white/10 rounded-lg p-6 bg-white/[0.02]"
          >
            <div className="flex gap-4">
              <CheckCircle size={24} className="text-green-400 flex-shrink-0" />
              <div>
                <h3 className="font-bold mb-2">No incidents recorded</h3>
                <p className="text-gray-400 text-sm">
                  ArcticCodex has been operating without any recorded incidents over the past 30 days.
                </p>
              </div>
            </div>
          </motion.div>
        </section>

        {/* Maintenance */}
        <section className="border-t border-white/10 pt-8 mt-8">
          <h2 className="text-2xl font-bold mb-6">Scheduled Maintenance</h2>

          <div className="space-y-4">
            {[
              {
                date: 'December 25, 2024',
                time: '02:00 - 04:00 UTC',
                service: 'Vault Storage',
                description: 'Database optimization and backup verification',
              },
              {
                date: 'January 8, 2025',
                time: '12:00 - 13:00 UTC',
                service: 'API Gateway',
                description: 'SSL certificate renewal and security patch deployment',
              },
            ].map((maintenance, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                viewport={{ once: true }}
                className="border border-white/10 rounded-lg p-4 bg-white/[0.02] flex gap-4"
              >
                <Clock size={20} className="text-yellow-400 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-bold">{maintenance.service}</h3>
                  <p className="text-sm text-gray-400">
                    {maintenance.date} at {maintenance.time}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">{maintenance.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
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
