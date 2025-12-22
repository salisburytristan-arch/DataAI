'use client';

import React from 'react';
import { motion } from 'framer-motion';

interface LogoTrinityProps {
  size?: number;
  showLabel?: boolean;
  animated?: boolean;
}

export default function LogoTrinity({ 
  size = 120, 
  showLabel = true,
  animated = true 
}: LogoTrinityProps) {
  const nodeRadius = size * 0.075;
  const centerX = size / 2;
  const topY = size * 0.25;
  const bottomY = size * 0.75;
  const leftX = size * 0.25;
  const rightX = size * 0.75;

  const Line = ({ x1, y1, x2, y2, delay = 0 }: any) => (
    <motion.line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke="#00FF41"
      strokeWidth="2"
      opacity="0.5"
      initial={animated ? { pathLength: 0, opacity: 0 } : {}}
      animate={animated ? { pathLength: 1, opacity: 0.5 } : {}}
      transition={{ duration: 1, delay }}
    />
  );

  const NodeA = () => (
    <motion.g
      initial={animated ? { scale: 0, opacity: 0 } : {}}
      animate={animated ? { scale: 1, opacity: 1 } : {}}
      transition={{ duration: 0.5, delay: 0.5 }}
    >
      <circle cx={leftX} cy={bottomY} r={nodeRadius} stroke="#00FF41" strokeWidth="3" fill="#050505" />
      <circle cx={leftX} cy={bottomY} r={nodeRadius * 0.15} fill="#00FF41" />
      {showLabel && (
        <text 
          x={leftX} 
          y={bottomY + nodeRadius + 20} 
          textAnchor="middle" 
          fill="#00FF41" 
          fontSize="11"
          fontFamily="monospace"
        >
          State 0
        </text>
      )}
    </motion.g>
  );

  const NodeB = () => (
    <motion.g
      initial={animated ? { scale: 0, opacity: 0 } : {}}
      animate={animated ? { scale: 1, opacity: 1 } : {}}
      transition={{ duration: 0.5, delay: 0.6 }}
    >
      <circle cx={rightX} cy={bottomY} r={nodeRadius} stroke="#00FF41" strokeWidth="3" fill="#050505" />
      <line 
        x1={rightX - nodeRadius * 0.5} 
        y1={bottomY - nodeRadius * 0.5} 
        x2={rightX + nodeRadius * 0.5} 
        y2={bottomY + nodeRadius * 0.5} 
        stroke="#00FF41" 
        strokeWidth="3"
      />
      <line 
        x1={rightX + nodeRadius * 0.5} 
        y1={bottomY - nodeRadius * 0.5} 
        x2={rightX - nodeRadius * 0.5} 
        y2={bottomY + nodeRadius * 0.5} 
        stroke="#00FF41" 
        strokeWidth="3"
      />
      {showLabel && (
        <text 
          x={rightX} 
          y={bottomY + nodeRadius + 20} 
          textAnchor="middle" 
          fill="#00FF41" 
          fontSize="11"
          fontFamily="monospace"
        >
          State 1
        </text>
      )}
    </motion.g>
  );

  const NodeC = () => (
    <motion.g
      initial={animated ? { scale: 0, opacity: 0 } : {}}
      animate={animated ? { scale: 1, opacity: 1 } : {}}
      transition={{ duration: 0.5, delay: 0.7 }}
    >
      <circle cx={centerX} cy={topY} r={nodeRadius} stroke="#FFFFFF" strokeWidth="3" fill="#050505" />
      <line 
        x1={centerX} 
        y1={topY - nodeRadius * 0.75} 
        x2={centerX} 
        y2={topY + nodeRadius * 0.75} 
        stroke="#FFFFFF" 
        strokeWidth="3"
      />
      {showLabel && (
        <text 
          x={centerX} 
          y={topY - nodeRadius - 10} 
          textAnchor="middle" 
          fill="#FFFFFF" 
          fontSize="11"
          fontFamily="monospace"
        >
          State Φ
        </text>
      )}
    </motion.g>
  );

  return (
    <div className="flex flex-col items-center">
      <svg width={size} height={size} xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="transparent"/>
        
        {/* Triangle connections */}
        <g>
          <Line x1={leftX} y1={bottomY} x2={rightX} y2={bottomY} delay={0.2} />
          <Line x1={leftX} y1={bottomY} x2={centerX} y2={topY} delay={0.3} />
          <Line x1={rightX} y1={bottomY} x2={centerX} y2={topY} delay={0.4} />
        </g>

        {/* Nodes */}
        <NodeA />
        <NodeB />
        <NodeC />
      </svg>
      
      {showLabel && (
        <motion.div
          initial={animated ? { opacity: 0, y: 10 } : {}}
          animate={animated ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.5, delay: 1 }}
          className="mt-4 text-center font-mono"
        >
          <div className="text-lg font-bold tracking-widest text-[#00FF41]">
            FORGE NUMERICS
          </div>
          <div className="text-xs text-gray-500 mt-1">// trinary system</div>
        </motion.div>
      )}
    </div>
  );
}
