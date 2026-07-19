"use client";

import { motion } from "motion/react";
import { 
  MessageSquare, Box, Brain, Shield, Network, 
  Wrench, Database, Sparkles, FileText, LayoutDashboard 
} from "lucide-react";
import { useEffect, useState } from "react";

const STEPS = [
  { id: 'prompt', label: 'User Prompt', icon: MessageSquare, color: 'from-sky-400 to-blue-600', shadow: 'shadow-sky-500/20', pos: [0, 0] },
  { id: 'sdk', label: 'Aegis SDK', icon: Box, color: 'from-blue-400 to-indigo-600', shadow: 'shadow-blue-500/20', pos: [1, 0] },
  { id: 'l1', label: 'Layer 1 (Request Intel)', icon: Brain, color: 'from-indigo-400 to-violet-600', shadow: 'shadow-indigo-500/20', pos: [2, 0] },
  { id: 'l2', label: 'Layer 2 (Governance)', icon: Shield, color: 'from-violet-400 to-purple-600', shadow: 'shadow-violet-500/20', pos: [2, 1] },
  { id: 'planner', label: 'Planner', icon: Network, color: 'from-purple-400 to-fuchsia-600', shadow: 'shadow-purple-500/20', pos: [2, 2] },
  { id: 'tool', label: 'Tool Execution', icon: Wrench, color: 'from-fuchsia-400 to-pink-600', shadow: 'shadow-fuchsia-500/20', pos: [1, 2] },
  { id: 'memory', label: 'Memory Update', icon: Database, color: 'from-pink-400 to-rose-600', shadow: 'shadow-pink-500/20', pos: [0, 2] },
  { id: 'exec', label: 'Execution Intel', icon: Sparkles, color: 'from-rose-400 to-orange-600', shadow: 'shadow-rose-500/20', pos: [0, 3] },
  { id: 'report', label: 'Store Report', icon: FileText, color: 'from-orange-400 to-amber-600', shadow: 'shadow-orange-500/20', pos: [1, 3] },
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, color: 'from-emerald-400 to-teal-600', shadow: 'shadow-emerald-500/20', pos: [2, 3] },
];

const CELL_W = 260;
const CELL_H = 160;
const NODE_W = 200;
const NODE_H = 100;

export function ArchitectureFlow() {
  const [activeStep, setActiveStep] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % STEPS.length);
    }, 1500);
    return () => clearInterval(interval);
  }, []);

  const currentX = STEPS[activeStep].pos[0] * CELL_W + (NODE_W / 2);
  const currentY = STEPS[activeStep].pos[1] * CELL_H + (NODE_H / 2);

  return (
    <div className="relative w-full h-[600px] md:h-[800px] flex items-center justify-center overflow-hidden" style={{ perspective: '1500px' }}>
      <motion.div 
        className="relative w-[760px] h-[580px]"
        initial={{ rotateX: 55, rotateZ: -35, scale: 0.8 }}
        animate={{ rotateX: 55, rotateZ: -35, scale: 0.8 }}
        style={{ transformStyle: 'preserve-3d' }}
      >
        {/* Isometric Grid Background */}
        <div 
          className="absolute inset-[-400px] border border-slate-800/30 bg-[linear-gradient(rgba(30,41,59,0.3)_1px,transparent_1px),linear-gradient(90deg,rgba(30,41,59,0.3)_1px,transparent_1px)] bg-[size:40px_40px] rounded-3xl"
          style={{ transform: 'translateZ(-50px)' }}
        />

        {/* Connection Lines (SVG) */}
        <svg className="absolute inset-0 overflow-visible" style={{ width: '100%', height: '100%', transform: 'translateZ(-10px)' }}>
          {/* Base lines */}
          {STEPS.map((step, idx) => {
            if (idx === STEPS.length - 1) return null;
            const next = STEPS[idx + 1];
            const x1 = step.pos[0] * CELL_W + (NODE_W / 2);
            const y1 = step.pos[1] * CELL_H + (NODE_H / 2);
            const x2 = next.pos[0] * CELL_W + (NODE_W / 2);
            const y2 = next.pos[1] * CELL_H + (NODE_H / 2);
            return (
              <line 
                key={`line-base-${idx}`}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#1e293b" // slate-800
                strokeWidth="4"
                strokeLinecap="round"
              />
            );
          })}
          
          {/* Active path lines */}
          {STEPS.map((step, idx) => {
            if (idx === STEPS.length - 1) return null;
            const next = STEPS[idx + 1];
            const x1 = step.pos[0] * CELL_W + (NODE_W / 2);
            const y1 = step.pos[1] * CELL_H + (NODE_H / 2);
            const x2 = next.pos[0] * CELL_W + (NODE_W / 2);
            const y2 = next.pos[1] * CELL_H + (NODE_H / 2);
            const isPassed = activeStep > idx;
            
            return (
              <motion.line 
                key={`line-active-${idx}`}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#38bdf8"
                strokeWidth="4"
                strokeLinecap="round"
                initial={{ pathLength: 0 }}
                animate={{ pathLength: isPassed ? 1 : 0 }}
                transition={{ duration: 0.5 }}
              />
            );
          })}
        </svg>

        {/* Nodes */}
        {STEPS.map((step, idx) => {
          const isActive = idx === activeStep;
          const isPassed = idx < activeStep;
          const Icon = step.icon;

          return (
            <div
              key={step.id}
              className={`absolute flex flex-col items-center justify-center p-4 rounded-xl border transition-all duration-700 w-[200px] h-[100px]`}
              style={{
                left: step.pos[0] * CELL_W,
                top: step.pos[1] * CELL_H,
                transform: isActive ? 'translateZ(40px) scale(1.1)' : 'translateZ(0px)',
                backgroundColor: isActive ? 'rgba(15, 23, 42, 0.95)' : isPassed ? 'rgba(15, 23, 42, 0.7)' : 'rgba(15, 23, 42, 0.4)',
                borderColor: isActive ? 'rgba(56,189,248,0.6)' : isPassed ? 'rgba(56,189,248,0.2)' : 'rgba(30,41,59,0.8)',
                boxShadow: isActive ? '0 20px 40px rgba(0,0,0,0.5), 0 0 30px rgba(56,189,248,0.2)' : '0 10px 30px rgba(0,0,0,0.5)',
                backdropFilter: 'blur(12px)',
              }}
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-2 transition-colors duration-700 ${isActive || isPassed ? `bg-gradient-to-br ${step.color}` : 'bg-slate-800'}`}>
                <Icon className={`w-6 h-6 transition-colors duration-700 ${isActive || isPassed ? 'text-white' : 'text-slate-500'}`} />
              </div>
              <h3 className={`font-bold text-sm text-center leading-tight transition-colors duration-700 ${isActive ? 'text-white' : isPassed ? 'text-slate-300' : 'text-slate-500'}`}>
                {step.label}
              </h3>
            </div>
          );
        })}

        {/* Moving Token Packet */}
        <motion.div
          className="absolute w-12 h-12 -ml-6 -mt-6 bg-sky-400 rounded-full blur-xl opacity-60 z-20"
          animate={{ x: currentX, y: currentY }}
          transition={{ type: "spring", stiffness: 60, damping: 20 }}
          style={{ transform: 'translateZ(20px)' }}
        />
        <motion.div
          className="absolute w-4 h-4 -ml-2 -mt-2 bg-white rounded-full shadow-[0_0_20px_rgba(56,189,248,1)] z-30"
          animate={{ x: currentX, y: currentY }}
          transition={{ type: "spring", stiffness: 60, damping: 20 }}
          style={{ transform: 'translateZ(20px)' }}
        />
      </motion.div>
    </div>
  );
}
