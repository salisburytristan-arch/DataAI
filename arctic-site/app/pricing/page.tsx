'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { Check, X } from 'lucide-react';

export default function PricingPage() {
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
            <h1 className="text-5xl font-bold mb-4">Pricing</h1>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Transparent pricing. No hidden fees. Scale as you grow.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              name: 'Sandbox (Hosted)',
              price: 'Free',
              period: 'limited',
              desc: 'For trials and evaluation of the hosted API.',
              highlighted: false,
              features: [
                { text: '50k hosted tokens/month', included: true },
                { text: 'Single org, 2 seats', included: true },
                { text: 'Audit receipts in responses', included: true },
                { text: 'Community support', included: true },
                { text: 'SLA guarantee', included: false },
                { text: 'Private tenancy', included: false },
                { text: 'Production support', included: false },
              ],
              cta: 'Get Access',
              ctaLink: '/console',
            },
            {
              name: 'Hosted Pro',
              price: '$499',
              period: '/month + usage',
              desc: 'Hosted API with SLAs and governance for teams.',
              highlighted: true,
              features: [
                { text: 'Includes 2M hosted tokens/month', included: true },
                { text: 'Org + RBAC + API keys', included: true },
                { text: 'Audit receipts + export bundles', included: true },
                { text: 'Priority support, 24x5', included: true },
                { text: '99.5% uptime SLA', included: true },
                { text: 'Fair-use burst throttling', included: true },
                { text: 'Dedicated infrastructure', included: false },
              ],
              cta: 'Start Hosted Trial',
              ctaLink: '/console',
            },
            {
              name: 'Enterprise (Hosted + Optional Self-Host)',
              price: 'Custom',
              period: 'contact us',
              desc: 'Dedicated tenancy, higher SLAs, and self-host option.',
              highlighted: false,
              features: [
                { text: 'Private VPC or on-prem option', included: true },
                { text: 'Custom token commits + overage pricing', included: true },
                { text: 'SSO/SAML + SCIM', included: true },
                { text: '24/7 support with SLA', included: true },
                { text: '99.9%+ uptime SLA', included: true },
                { text: 'Dedicated infrastructure', included: true },
                { text: 'Custom integrations & DPA/BAA', included: true },
              ],
              cta: 'Contact Sales',
              ctaLink: 'mailto:acrticasters@gmail.com',
            },
          ].map((plan, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              viewport={{ once: true }}
              className={`rounded-lg border transition-all ${
                plan.highlighted
                  ? 'border-cyan-500/50 bg-cyan-950/20 ring-2 ring-cyan-500/20 md:scale-105'
                  : 'border-white/10 bg-white/[0.02]'
              } p-8 flex flex-col`}
            >
              {plan.highlighted && (
                <div className="mb-4 px-3 py-1 rounded-full w-fit bg-cyan-500/20 text-cyan-400 text-xs font-bold">
                  POPULAR
                </div>
              )}

              <h3 className="text-2xl font-bold mb-2">{plan.name}</h3>
              <p className="text-gray-400 text-sm mb-6">{plan.desc}</p>

              <div className="mb-6">
                <div className="text-4xl font-bold">
                  {plan.price}
                  {plan.price !== 'Custom' && (
                    <span className="text-lg text-gray-400 font-normal ml-2">{plan.period}</span>
                  )}
                </div>
              </div>

              <Link
                href={plan.ctaLink}
                className={`py-3 rounded-lg font-bold text-center mb-8 transition-all ${
                  plan.highlighted
                    ? 'bg-cyan-500 hover:bg-cyan-400 text-black'
                    : 'border border-white/20 hover:border-cyan-400 text-white'
                }`}
              >
                {plan.cta}
              </Link>

              <ul className="space-y-3 flex-1">
                {plan.features.map((feature, j) => (
                  <li key={j} className="flex gap-2 text-sm">
                    {feature.included ? (
                      <Check size={18} className="text-green-400 flex-shrink-0" />
                    ) : (
                      <X size={18} className="text-gray-600 flex-shrink-0" />
                    )}
                    <span className={feature.included ? 'text-white' : 'text-gray-500'}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="max-w-4xl mx-auto px-6 py-16 border-t border-white/10">
        <h2 className="text-2xl font-bold mb-8">Frequently Asked Questions</h2>

        <div className="space-y-4">
          {[
            {
              q: 'Can I upgrade or downgrade anytime?',
              a: 'Yes. Changes take effect at your next billing cycle. No penalties for downgrading.',
            },
            {
              q: 'What payment methods do you accept?',
              a: 'We accept credit cards (Visa, Mastercard, Amex), wire transfers, and POs for Enterprise plans.',
            },
            {
              q: 'Is there a free trial?',
              a: 'Yes. Hosted Pro includes a 14-day trial with sandbox limits. No credit card required for Sandbox.',
            },
            {
              q: 'What happens if I exceed my API quota?',
              a: 'Sandbox throttles at the limit. Hosted Pro overages follow per-token pricing with fair-use burst controls. Enterprise is contracted per commit.',
            },
            {
              q: 'Do you offer discounts?',
              a: 'Yes. Annual billing includes a 20% discount. Non-profits and open-source projects get 50% off.',
            },
            {
              q: 'Can I self-host?',
              a: 'Yes. Enterprise includes an optional self-hosted deployment with DPA/BAA and support.',
            },
          ].map((item, i) => (
            <motion.details
              key={i}
              initial={{ opacity: 0 }}
              whileInView={{ opacity: 1 }}
              transition={{ delay: i * 0.05 }}
              viewport={{ once: true }}
              className="border border-white/10 rounded-lg p-4 group"
            >
              <summary className="cursor-pointer font-bold text-white hover:text-cyan-400 transition">
                {item.q}
              </summary>
              <p className="mt-4 text-gray-400 text-sm">{item.a}</p>
            </motion.details>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-white/10 py-16">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-4">Start Building Today</h2>
          <p className="text-gray-400 mb-6 max-w-2xl mx-auto">
            Choose the plan that fits your needs. Upgrade anytime. Cancel anytime.
          </p>
          <div className="flex gap-4 justify-center">
            <Link
              href="/console"
              className="px-6 py-3 bg-cyan-500 hover:bg-cyan-400 text-black font-bold rounded-lg transition"
            >
              Try Community Free
            </Link>
            <a
              href="mailto:acrticasters@gmail.com"
              className="px-6 py-3 border border-white/20 hover:border-cyan-400 text-white rounded-lg transition"
            >
              Talk to Sales
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
