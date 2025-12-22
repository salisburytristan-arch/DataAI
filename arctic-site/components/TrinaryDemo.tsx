'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';

export default function TrinaryDemo() {
  const [activeState, setActiveState] = useState<0 | 1 | 2>(0);

  const states = [
    {
      id: 0,
      symbol: '⊙',
      name: 'State 0',
      description: 'False / Ground / Absence',
      color: '#00FF41',
      example: 'Fact does not exist in knowledge base'
    },
    {
      id: 1,
      symbol: '⊗',
      name: 'State 1',
      description: 'True / Power / Presence',
      color: '#00FF41',
      example: 'Fact is verified and stored'
    },
    {
      id: 2,
      symbol: 'Φ',
      name: 'State Φ',
      description: 'Paradox / Unknown / Undecidable',
      color: '#FFFFFF',
      example: 'Fact requires external verification'
    }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto">
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        {states.map((state) => (
          <motion.button
            key={state.id}
            onClick={() => setActiveState(state.id as 0 | 1 | 2)}
            className={`p-6 border rounded-lg transition-all ${
              activeState === state.id
                ? 'border-cyan-400 bg-cyan-950/30'
                : 'border-white/10 bg-white/[0.02] hover:border-white/20'
            }`}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div 
              className="text-5xl mb-3" 
              style={{ color: state.color }}
            >
              {state.symbol}
            </div>
            <div className="text-sm font-mono text-white/90">{state.name}</div>
            <div className="text-xs text-gray-500 mt-1">{state.description}</div>
          </motion.button>
        ))}
      </div>

      <motion.div
        key={activeState}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="p-6 border border-cyan-500/30 rounded-lg bg-black/50"
      >
        <div className="flex items-start gap-4">
          <div 
            className="text-6xl flex-shrink-0" 
            style={{ color: states[activeState].color }}
          >
            {states[activeState].symbol}
          </div>
          <div className="flex-1">
            <h3 className="text-xl font-bold mb-2">{states[activeState].name}</h3>
            <p className="text-gray-400 mb-4">{states[activeState].description}</p>
            <div className="bg-[#0a0a0a] p-4 rounded border border-gray-800 font-mono text-sm">
              <div className="text-cyan-400 mb-2"># Example Use Case:</div>
              <div className="text-gray-300">{states[activeState].example}</div>
            </div>
          </div>
        </div>
      </motion.div>

      <div className="mt-8 p-6 border border-white/10 rounded-lg bg-white/[0.02]">
        <h4 className="text-sm font-bold text-cyan-400 mb-3 font-mono">WHY TRINARY?</h4>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-gray-400">
          <div>
            <div className="font-bold text-white mb-1">Binary Limitation:</div>
            <div>Traditional systems force true/false decisions, losing nuance in uncertainty.</div>
          </div>
          <div>
            <div className="font-bold text-white mb-1">Trinary Advantage:</div>
            <div>State Φ preserves epistemic uncertainty, enabling smarter decision-making.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
