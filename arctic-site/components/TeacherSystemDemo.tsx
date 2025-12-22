'use client';

import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, RefreshCw } from 'lucide-react';

export default function TeacherSystemDemo() {
  const [step, setStep] = useState(0);

  const pipeline = [
    {
      stage: 'Draft',
      description: 'Agent generates initial response',
      code: 'draft = agent.respond(query)',
      quality: 0.65,
      status: 'warning'
    },
    {
      stage: 'Critique',
      description: 'DeepSeek teacher evaluates quality',
      code: 'critique = teacher.critique(draft, evidence)',
      quality: 0.75,
      status: 'info'
    },
    {
      stage: 'Revise',
      description: 'Agent improves based on feedback',
      code: 'final = agent.revise(draft, critique)',
      quality: 0.92,
      status: 'success'
    }
  ];

  React.useEffect(() => {
    const interval = setInterval(() => {
      setStep((prev) => (prev + 1) % pipeline.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Pipeline Stages */}
      <div className="flex items-center justify-between mb-8">
        {pipeline.map((stage, idx) => (
          <React.Fragment key={idx}>
            <motion.div
              className={`flex-1 p-4 border rounded-lg transition-all ${
                step === idx
                  ? 'border-cyan-400 bg-cyan-950/30'
                  : 'border-white/10 bg-white/[0.02]'
              }`}
              animate={{
                scale: step === idx ? 1.05 : 1,
                opacity: step === idx ? 1 : 0.6
              }}
            >
              <div className="flex items-center gap-2 mb-2">
                {stage.status === 'success' && <CheckCircle className="text-green-400" size={16} />}
                {stage.status === 'warning' && <AlertCircle className="text-yellow-400" size={16} />}
                {stage.status === 'info' && <RefreshCw className="text-cyan-400" size={16} />}
                <span className="font-bold text-sm">{stage.stage}</span>
              </div>
              <div className="text-xs text-gray-500">{stage.description}</div>
              <div className="mt-2 text-xs font-mono text-cyan-400">
                Quality: {(stage.quality * 100).toFixed(0)}%
              </div>
            </motion.div>
            {idx < pipeline.length - 1 && (
              <div className="px-2 text-gray-600">→</div>
            )}
          </React.Fragment>
        ))}
      </div>

      {/* Current Stage Detail */}
      <motion.div
        key={step}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-[#0a0a0a] border border-gray-800 rounded-lg overflow-hidden"
      >
        <div className="bg-[#111] px-4 py-2 border-b border-gray-800 flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500/50"></div>
          <div className="w-3 h-3 rounded-full bg-yellow-500/50"></div>
          <div className="w-3 h-3 rounded-full bg-green-500/50"></div>
          <div className="text-xs text-gray-600 font-mono ml-2">teacher_pipeline.py</div>
        </div>
        <div className="p-6 font-mono text-sm">
          <div className="text-gray-500 mb-2"># {pipeline[step].description}</div>
          <div className="text-cyan-400">{pipeline[step].code}</div>
          <div className="mt-4 pt-4 border-t border-gray-800">
            <div className="flex items-center justify-between text-xs">
              <span className="text-gray-500">Quality Score:</span>
              <span className={`font-bold ${
                pipeline[step].quality >= 0.9 ? 'text-green-400' :
                pipeline[step].quality >= 0.7 ? 'text-yellow-400' : 'text-red-400'
              }`}>
                {(pipeline[step].quality * 100).toFixed(1)}%
              </span>
            </div>
            <div className="mt-2 h-2 bg-gray-800 rounded-full overflow-hidden">
              <motion.div
                className={`h-full ${
                  pipeline[step].quality >= 0.9 ? 'bg-green-400' :
                  pipeline[step].quality >= 0.7 ? 'bg-yellow-400' : 'bg-red-400'
                }`}
                initial={{ width: 0 }}
                animate={{ width: `${pipeline[step].quality * 100}%` }}
                transition={{ duration: 1 }}
              />
            </div>
          </div>
        </div>
      </motion.div>

      {/* Benefits Grid */}
      <div className="grid md:grid-cols-3 gap-4 mt-8">
        {[
          { title: 'Multi-Teacher', desc: 'DeepSeek R1 + Local models' },
          { title: 'Distillation', desc: 'Generate training pairs' },
          { title: 'Improvement', desc: 'Quality scores 0.917 avg' }
        ].map((item, idx) => (
          <div 
            key={idx}
            className="p-4 border border-white/10 rounded-lg bg-white/[0.02]"
          >
            <div className="text-sm font-bold text-cyan-400 mb-1">{item.title}</div>
            <div className="text-xs text-gray-500">{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
