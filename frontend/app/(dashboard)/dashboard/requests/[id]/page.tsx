"use client";

import { use, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { motion, AnimatePresence } from "motion/react";
import {
  ArrowLeft, Terminal, ShieldAlert, CheckCircle2, XCircle, Clock,
  Activity, Shield, ShieldCheck, ChevronRight, ChevronDown,
  Layers, FileJson, Cpu, Zap, ListTree, Code2, Brain
} from "lucide-react";
import Link from "next/link";
import { ExecutionDetail } from "@/lib/db";
import { cn } from "@/lib/utils";

const Section = ({ title, icon: Icon, children, defaultOpen = true }: { title: string, icon: any, children: React.ReactNode, defaultOpen?: boolean }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-slate-800/60 bg-slate-900/40 rounded-2xl overflow-hidden backdrop-blur-xl">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-slate-900/60 hover:bg-slate-800/40 transition-colors border-b border-slate-800/60"
      >
        <div className="flex items-center gap-3">
          <Icon className="w-5 h-5 text-sky-400" />
          <h3 className="font-semibold text-slate-200">{title}</h3>
        </div>
        {isOpen ? <ChevronDown className="w-5 h-5 text-slate-500" /> : <ChevronRight className="w-5 h-5 text-slate-500" />}
      </button>
      <AnimatePresence initial={false}>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="p-6">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default function RequestDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const { id } = resolvedParams;

  const { data: req, isLoading } = useQuery<ExecutionDetail>({
    queryKey: ["request", id],
    queryFn: async () => {
      const { data } = await api.get(`/executions/${id}`);

      const context = data.context || {};
      const summary = data.summary || {};
      const audit = data.audit || {};
      const metrics = data.metrics || {};
      const layer1 = data.layer1 || {};
      const planner = data.planner || {};
      const security = data.security || {};

      const statusMap: Record<string, "success" | "blocked" | "error"> = {
        SUCCESS: "success",
        BLOCKED: "blocked",
        FAILED: "error",
        CANCELLED: "error"
      };

      return {
        id: context.execution_id || "",
        projectId: context.project_id || "",
        timestamp: audit.created_at || new Date().toISOString(),
        status: statusMap[data.status || summary.status] || "success",
        model: planner.model || data.model || "GPT-4o",
        durationMs: metrics.performance?.total_latency_ms || summary.duration_ms || 0,
        tokensTotal: metrics.cost?.total_tokens || planner.total_tokens || summary.tokens_total || 0,
        tokensPrompt: metrics.cost?.input_tokens || planner.input_tokens || summary.tokens_prompt || 0,
        tokensCompletion: metrics.cost?.output_tokens || planner.output_tokens || summary.tokens_completion || 0,
        riskScore: security.risk_level || summary.risk_level || "LOW",
        governanceScore: data.governance_score?.score || 100,
        summary: typeof summary.summary === 'string' ? summary.summary : data.prompt ? data.prompt : `Execution report for ${context.execution_id?.substring(0, 8)}`,
        prompt: data.prompt || "",
        response: data.output || data.response || "",
        layer1Analysis: {
          intent: layer1.detected_intent || "General",
          entities: layer1.capability_detection || [],
          sentiment: layer1.task_category || "Neutral",
          language: "en",
          isSafe: layer1.validation_result?.is_safe,
          safetyReason: layer1.validation_result?.reason || "",
        },
        layer2Governance: {
          piiDetected: data.privacy?.contains_pii || false,
          toxicContent: false,
          dataLossPrevention: "None",
          policyViolations: security.policy_violations || [],
          validators: data.governance?.validators || [],
        },
        planner: {
          strategy: planner.provider || "Direct Execution",
          steps: (data.execution_plan || []).map((p: any) => p.purpose || p.tool || ""),
          totalLlmCalls: planner.total_llm_calls || 0,
          iterations: planner.planning_iterations || 0,
        },
        governanceScoreBreakdown: data.governance_score?.breakdown || {},
        toolCalls: (data.tool_calls || []).map((tc: any) => ({
          id: tc.tool_call_id || tc.id || "",
          tool: tc.tool || tc.name || "",
          input: tc.input_summary || tc.input || "",
          output: tc.output_summary || tc.output || "",
          durationMs: tc.duration_ms || 0,
        })),
        timeline: (data.timeline || []).map((t: any) => ({
          event: t.event || "",
          timestamp: t.timestamp || "",
          durationMs: t.metadata?.duration_ms || 0,
        }))
      } as any;
    }
  });

  const [activeTab, setActiveTab] = useState<"overview" | "tool_calls" | "timeline" | "policy">("overview");

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6 animate-pulse">
        <div className="h-8 w-24 bg-slate-800/50 rounded mb-8" />
        <div className="h-24 w-full bg-slate-800/30 rounded-2xl mb-6" />
        <div className="h-64 w-full bg-slate-800/30 rounded-2xl" />
      </div>
    );
  }

  if (!req) {
    return <div className="text-center py-20 text-slate-400">Request not found</div>;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-20">
      <div className="flex items-center gap-2 text-sm text-slate-400">
        <Link href="/dashboard/requests" className="hover:text-sky-400 transition-colors flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Explorer
        </Link>
        <ChevronRight className="w-4 h-4 text-slate-600" />
        <code className="text-slate-300 font-mono text-xs">{req.id}</code>
      </div>

      {/* Header Card */}
      <div className="relative rounded-3xl border border-slate-800/60 bg-slate-900/40 p-6 md:p-8 overflow-hidden backdrop-blur-xl shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-sky-500/10 rounded-full blur-[100px] -translate-y-1/2 translate-x-1/2 pointer-events-none" />

        <div className="flex flex-col md:flex-row gap-6 justify-between items-start">
          <div className="space-y-4 relative z-10">
            <div className="flex items-center gap-3">
              <span className={cn(
                "px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-2 border",
                req.status === 'success' ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" :
                  req.status === 'blocked' ? "bg-amber-500/10 text-amber-400 border-amber-500/20" :
                    "bg-red-500/10 text-red-400 border-red-500/20"
              )}>
                {req.status === 'success' && <CheckCircle2 className="w-4 h-4" />}
                {req.status === 'blocked' && <ShieldAlert className="w-4 h-4" />}
                {req.status === 'error' && <XCircle className="w-4 h-4" />}
                <span className="capitalize text-sm tracking-wide">{req.status}</span>
              </span>
              <span className="text-sm text-slate-400 font-mono">
                {new Date(req.timestamp).toLocaleString()}
              </span>
            </div>

            <h1 className="text-2xl font-bold text-slate-100">{req.summary}</h1>

            <div className="flex flex-wrap gap-4 text-sm">
              <div className="flex items-center gap-2 bg-slate-950/50 px-3 py-1.5 rounded-lg border border-slate-800">
                <Cpu className="w-4 h-4 text-slate-400" />
                <span className="text-slate-300 font-medium">{req.model}</span>
              </div>
              <div className="flex items-center gap-2 bg-slate-950/50 px-3 py-1.5 rounded-lg border border-slate-800">
                <Clock className="w-4 h-4 text-slate-400" />
                <span className="text-slate-300 font-medium">{req.durationMs}ms total</span>
              </div>
              <div className="flex items-center gap-2 bg-slate-950/50 px-3 py-1.5 rounded-lg border border-slate-800">
                <Zap className="w-4 h-4 text-slate-400" />
                <span className="text-slate-300 font-medium">{req.tokensTotal} tokens</span>
                <span className="text-slate-500 text-xs">({req.tokensPrompt} ↑ / {req.tokensCompletion} ↓)</span>
              </div>
            </div>
          </div>

          <div className="flex gap-4 relative z-10 w-full md:w-auto">
            <div className="flex-1 md:w-36 bg-slate-900/80 border border-slate-700/50 rounded-3xl p-5 text-center flex flex-col items-center justify-center shadow-inner relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-slate-400 text-[10px] font-bold mb-3 tracking-widest uppercase relative z-10">Risk Score</div>
              <div className={cn(
                "text-3xl font-black capitalize tracking-tighter relative z-10 drop-shadow-md transition-transform group-hover:scale-105",
                req.riskScore === 'low' || req.riskScore === 'LOW' ? "text-emerald-400" :
                  req.riskScore === 'medium' || req.riskScore === 'MEDIUM' ? "text-amber-400" : "text-red-400"
              )}>
                {req.riskScore}
              </div>
            </div>
            <div className="flex-1 md:w-36 bg-slate-900/80 border border-slate-700/50 rounded-3xl p-5 text-center flex flex-col items-center justify-center shadow-inner relative overflow-hidden group">
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
              <div className="text-slate-400 text-[10px] font-bold mb-2 tracking-widest uppercase relative z-10">Governance</div>
              <div className="relative w-16 h-16 flex items-center justify-center z-10">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-slate-800" />
                  <motion.circle
                    cx="50" cy="50" r="40"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={2 * Math.PI * 40}
                    initial={{ strokeDashoffset: 2 * Math.PI * 40 }}
                    animate={{ strokeDashoffset: (2 * Math.PI * 40) - (req.governanceScore / 100) * (2 * Math.PI * 40) }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    strokeLinecap="round"
                    className={cn(
                      req.governanceScore >= 80 ? "text-emerald-500 drop-shadow-[0_0_8px_rgba(16,185,129,0.5)]" :
                        req.governanceScore >= 50 ? "text-amber-500 drop-shadow-[0_0_8px_rgba(245,158,11,0.5)]" : "text-red-500 drop-shadow-[0_0_8px_rgba(239,68,68,0.5)]"
                    )}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-bold text-slate-200">{req.governanceScore}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-800/60 pb-px mb-6">
        {[
          { id: "overview", label: "Overview & Payload", icon: FileJson },
          { id: "tool_calls", label: "Tool Executions", count: req.toolCalls.length, icon: Code2 },
          { id: "timeline", label: "Execution Timeline", icon: ListTree },
          { id: "policy", label: "Security & Policy", icon: ShieldCheck }
        ].map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-3 text-sm font-medium transition-all relative flex items-center gap-2 ${activeTab === tab.id ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 rounded-t-lg'}`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
              {tab.count !== undefined && (
                <span className={`px-2 py-0.5 rounded-full text-xs font-mono ${activeTab === tab.id ? 'bg-sky-500/20 text-sky-400' : 'bg-slate-800 text-slate-400'}`}>
                  {tab.count}
                </span>
              )}
              {activeTab === tab.id && (
                <motion.div layoutId="requestActiveTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400 rounded-t-full" />
              )}
            </button>
          )
        })}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
          >
            {activeTab === "overview" && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                  <Section title="Payload" icon={FileJson}>
                    <div className="space-y-4">
                      <div>
                        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">User Prompt</h4>
                        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 text-slate-300 font-mono text-sm leading-relaxed overflow-x-auto whitespace-pre-wrap">
                          {req.prompt}
                        </div>
                      </div>
                      {req.response && (
                        <div>
                          <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-2 mt-6">Model Response</h4>
                          <div className="bg-sky-950/20 border border-sky-900/30 rounded-xl p-4 text-sky-100 font-mono text-sm leading-relaxed overflow-x-auto whitespace-pre-wrap">
                            {req.response}
                          </div>
                        </div>
                      )}
                    </div>
                  </Section>
                </div>

                <div className="space-y-6">
                  <Section title="Layer 1 Analysis" icon={Activity}>
                    <div className="space-y-4 text-sm">
                      <div>
                        <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">Intent</span>
                        <span className="text-slate-200 bg-slate-800/50 px-2.5 py-1 rounded-md inline-block">{req.layer1Analysis.intent}</span>
                      </div>
                      <div>
                        <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">Sentiment</span>
                        <span className={cn(
                          "px-2.5 py-1 rounded-md inline-block font-medium",
                          req.layer1Analysis.sentiment === 'Negative' ? "bg-red-500/10 text-red-400" :
                            req.layer1Analysis.sentiment === 'Positive' ? "bg-emerald-500/10 text-emerald-400" :
                              "bg-slate-800/50 text-slate-300"
                        )}>{req.layer1Analysis.sentiment}</span>
                      </div>
                      <div>
                        <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">Language</span>
                        <span className="text-slate-300">{req.layer1Analysis.language}</span>
                      </div>
                      <div>
                        <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">Safety Status</span>
                        {req.layer1Analysis.isSafe === undefined ? (
                          <span className="text-slate-400">Unknown</span>
                        ) : req.layer1Analysis.isSafe ? (
                          <span className="text-emerald-400 font-medium flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4" /> Passed Checks</span>
                        ) : (
                          <span className="text-red-400 font-medium flex items-center gap-1.5"><XCircle className="w-4 h-4" /> Blocked</span>
                        )}
                      </div>
                      {req.layer1Analysis.safetyReason && (
                        <div>
                          <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">Safety Reason</span>
                          <span className="text-slate-300 text-xs italic">{req.layer1Analysis.safetyReason}</span>
                        </div>
                      )}
                      <div>
                        <span className="block text-xs font-semibold text-slate-500 uppercase mb-1">Entities</span>
                        <div className="flex flex-wrap gap-2">
                          {req.layer1Analysis.entities.map((e, i) => (
                            <span key={i} className="bg-sky-500/10 text-sky-300 border border-sky-500/20 px-2 py-0.5 rounded text-xs">{e}</span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Section>
                </div>
              </div>
            )}

            {activeTab === "tool_calls" && (
              <div className="max-w-4xl mx-auto">
                <Section title="Tool Calls" icon={Code2} defaultOpen={true}>
                  {req.toolCalls.length === 0 ? (
                    <div className="text-center py-12 border border-slate-800/50 rounded-xl bg-slate-900/20">
                      <Code2 className="w-8 h-8 text-slate-600 mx-auto mb-3" />
                      <p className="text-slate-400">No tool calls were made during this execution.</p>
                    </div>
                  ) : (
                    <div className="space-y-6">
                      {req.toolCalls.map((call, idx) => (
                        <motion.div
                          key={call.id || idx}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1, duration: 0.3 }}
                          className="border border-slate-700/50 bg-[#0A0E17] rounded-xl overflow-hidden shadow-lg transition-all hover:border-slate-600 hover:shadow-sky-900/20 hover:shadow-2xl"
                        >
                          <div className="bg-slate-900/90 px-4 py-3 border-b border-slate-800 flex justify-between items-center backdrop-blur-md">
                            <div className="flex items-center gap-3">
                              <div className="flex items-center gap-1.5 mr-2">
                                <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
                                <div className="w-2.5 h-2.5 rounded-full bg-amber-500/80"></div>
                                <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></div>
                              </div>
                              <span className="flex items-center justify-center w-5 h-5 rounded bg-slate-800 text-slate-400 text-xs font-mono">
                                {idx + 1}
                              </span>
                              <span className="font-mono text-sm font-semibold text-sky-400 flex items-center gap-2">
                                <Terminal className="w-4 h-4 text-sky-500" />
                                {call.tool}
                              </span>
                            </div>
                            <span className="text-xs text-slate-500 flex items-center gap-1.5 font-mono bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800 shadow-inner">
                              <Clock className="w-3.5 h-3.5 text-slate-600" /> {call.durationMs}ms
                            </span>
                          </div>
                          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-800/80">
                            <div className="p-0">
                              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-slate-900/40 px-4 py-2 border-b border-slate-800/50 flex items-center gap-2">
                                <ArrowLeft className="w-3 h-3 text-amber-500" /> INPUT
                              </div>
                              <div className="p-4 overflow-x-auto">
                                <pre className="text-[13px] text-amber-200/90 font-mono leading-relaxed">
                                  {(() => {
                                    try {
                                      return typeof call.input === 'string'
                                        ? JSON.stringify(JSON.parse(call.input), null, 2)
                                        : JSON.stringify(call.input, null, 2);
                                    } catch {
                                      return String(call.input || "No input");
                                    }
                                  })()}
                                </pre>
                              </div>
                            </div>
                            <div className="p-0 bg-sky-950/5 relative">
                              <div className="absolute inset-0 bg-gradient-to-br from-sky-500/5 to-transparent pointer-events-none" />
                              <div className="text-[10px] font-bold text-slate-500 uppercase tracking-widest bg-slate-900/40 px-4 py-2 border-b border-slate-800/50 flex items-center gap-2 relative z-10">
                                OUTPUT <ChevronRight className="w-3 h-3 text-emerald-500" />
                              </div>
                              <div className="p-4 overflow-x-auto relative z-10">
                                <pre className="text-[13px] text-emerald-300/90 font-mono leading-relaxed">
                                  {(() => {
                                    try {
                                      return typeof call.output === 'string'
                                        ? JSON.stringify(JSON.parse(call.output), null, 2)
                                        : JSON.stringify(call.output, null, 2);
                                    } catch {
                                      return String(call.output || "No output");
                                    }
                                  })()}
                                </pre>
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  )}
                </Section>
              </div>
            )}

            {activeTab === "timeline" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <Section title="Execution Steps (Planner)" icon={Layers}>
                  <div className="space-y-4 text-sm">
                    <div>
                      <span className="block text-xs font-semibold text-slate-500 uppercase mb-1.5 flex items-center gap-2">
                        <Brain className="w-3.5 h-3.5 text-sky-400" /> Selected Strategy
                      </span>
                      <div className="relative overflow-hidden bg-slate-900/60 p-4 rounded-xl border border-sky-900/40 shadow-inner group transition-all hover:border-sky-500/50">
                        <div className="absolute inset-0 bg-gradient-to-r from-sky-500/10 via-transparent to-transparent opacity-50 group-hover:opacity-100 transition-opacity" />
                        <div className="flex justify-between items-start md:items-center relative z-10 flex-col md:flex-row gap-3">
                          <p className="text-slate-200 font-medium leading-relaxed">{req.planner.strategy}</p>
                          <span className="text-xs font-mono text-sky-300 bg-sky-950/50 border border-sky-900/50 px-2.5 py-1.5 rounded-lg whitespace-nowrap shadow-sm">
                            {req.planner.iterations} iterations • {req.planner.totalLlmCalls} calls
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div>
                    <span className="block text-xs font-semibold text-slate-500 uppercase mb-3">Execution Plan</span>
                    <div className="space-y-3">
                      {req.planner.steps.length > 0 ? (
                        req.planner.steps.map((step, idx) => (
                          <motion.div 
                            key={idx} 
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.1, duration: 0.3 }}
                            className="flex items-center gap-4 bg-slate-900/40 border border-slate-800/80 p-3.5 rounded-xl shadow-sm hover:border-sky-500/30 hover:bg-slate-800/50 transition-all"
                          >
                            <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-slate-800 text-sky-400 font-mono text-xs shadow-inner shrink-0">
                              {idx + 1}
                            </span>
                            <span className="text-sm text-slate-300 font-medium">
                              {step}
                            </span>
                          </motion.div>
                        ))
                      ) : (
                        <div className="flex flex-col items-center justify-center py-10 bg-slate-900/30 border border-dashed border-slate-800/60 rounded-2xl">
                          <Brain className="w-8 h-8 text-slate-700 mb-3" />
                          <p className="text-slate-500 text-sm font-medium">No execution plan generated.</p>
                          <p className="text-slate-600 text-xs mt-1">The request was terminated or blocked early.</p>
                        </div>
                      )}
                    </div>
                  </div>
                </Section>
                <Section title="Event Timeline" icon={ListTree}>
                  <div className="space-y-3">
                    {req.timeline.map((event, idx) => {
                      const isError = event.event.toLowerCase().includes('failed') || event.event.toLowerCase().includes('error');
                      const isSuccess = event.event.toLowerCase().includes('passed') || event.event.toLowerCase().includes('completed');
                      return (
                        <motion.div 
                          key={idx}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: idx * 0.1, duration: 0.3 }}
                          className={cn(
                            "flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-6 bg-slate-900/40 border p-4 rounded-xl transition-all relative overflow-hidden",
                            isError ? "border-red-900/50 hover:bg-red-950/20 hover:border-red-500/50" : 
                            isSuccess ? "border-emerald-900/30 hover:bg-emerald-950/10 hover:border-emerald-500/30" : 
                            "border-slate-800/80 hover:border-slate-700 hover:bg-slate-800/40"
                          )}
                        >
                          {isError && <div className="absolute left-0 top-0 bottom-0 w-1 bg-red-500/80" />}
                          {isSuccess && <div className="absolute left-0 top-0 bottom-0 w-1 bg-emerald-500/50" />}
                          <time className="text-[11px] text-slate-500 font-mono tracking-wider shrink-0 bg-slate-950 px-2.5 py-1 rounded-md border border-slate-800/60 w-fit pl-4 sm:pl-2.5 z-10">
                            {new Date(event.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', fractionalSecondDigits: 3 })}
                          </time>
                          <div className="flex-1 flex justify-between items-center z-10">
                            <h4 className={cn(
                              "font-medium text-sm flex items-center gap-2",
                              isError ? "text-red-400" : isSuccess ? "text-emerald-300" : "text-slate-200"
                            )}>
                              {isError && <XCircle className="w-4 h-4 shrink-0" />}
                              {isSuccess && <CheckCircle2 className="w-4 h-4 shrink-0" />}
                              {event.event}
                            </h4>
                            <span className="text-xs font-mono text-slate-400 bg-slate-950/50 border border-slate-800/80 px-2 py-0.5 rounded-md">
                              {event.durationMs > 0 ? `${event.durationMs.toFixed(1)}ms` : '0ms'}
                            </span>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </Section>
              </div>
            )}

            {activeTab === "policy" && (
              <div className="max-w-5xl mx-auto space-y-6">
                
                {/* Top Bento Grid */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                  
                  {/* Left Column: Overall Status (Spans 5 cols) */}
                  <div className="md:col-span-5 bg-slate-900/60 border border-slate-800/80 rounded-3xl p-8 relative overflow-hidden flex flex-col justify-between shadow-xl group">
                    <div className="absolute inset-0 bg-gradient-to-br from-sky-500/5 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
                    <div className="relative z-10 space-y-6">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                          <ShieldCheck className="w-4 h-4 text-sky-400" /> Security Assessment
                        </span>
                      </div>
                      
                      <div className="flex flex-col items-center justify-center text-center py-6">
                        <div className={cn(
                          "w-24 h-24 rounded-full flex items-center justify-center mb-6 shadow-2xl relative",
                          req.governanceScore >= 80 ? "bg-emerald-500/10 text-emerald-400 shadow-emerald-500/20" :
                          req.governanceScore >= 50 ? "bg-amber-500/10 text-amber-400 shadow-amber-500/20" : "bg-red-500/10 text-red-400 shadow-red-500/20"
                        )}>
                          <div className="absolute inset-0 rounded-full border border-current opacity-20 animate-ping duration-1000" />
                          <Shield className="w-10 h-10" />
                        </div>
                        <h2 className="text-4xl font-black text-slate-100 mb-2">{req.governanceScore}/100</h2>
                        <p className="text-slate-400 text-sm">Overall Governance Score</p>
                      </div>

                      {/* Active Validators inline */}
                      {(req.layer2Governance.validators?.length || 0) > 0 && (
                        <div className="pt-6 border-t border-slate-800/50">
                          <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4">Active Validators</span>
                          <div className="flex flex-wrap gap-2">
                            {(req.layer2Governance.validators || []).map((v: any, i: number) => (
                              <div key={i} className="flex items-center gap-1.5 bg-slate-950/50 border border-slate-800/80 px-2.5 py-1.5 rounded-lg">
                                {v.status === 'PASS' ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> : <XCircle className="w-3.5 h-3.5 text-red-400" />}
                                <span className="text-slate-300 text-xs font-medium">{v.name}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Right Column: Score Breakdown (Spans 7 cols) */}
                  <div className="md:col-span-7 bg-slate-900/40 border border-slate-800/80 rounded-3xl p-8 relative overflow-hidden shadow-xl">
                    <span className="block text-sm font-bold text-slate-400 uppercase tracking-widest mb-8 flex items-center gap-2">
                      <Activity className="w-4 h-4 text-sky-400" /> Category Breakdown
                    </span>
                    
                    {Object.keys(req.governanceScoreBreakdown || {}).length > 0 ? (
                      <div className="grid grid-cols-1 gap-6">
                        {Object.entries(req.governanceScoreBreakdown || {}).map(([key, value]: any, idx) => (
                          <motion.div 
                            key={key} 
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.1, duration: 0.4 }}
                            className="space-y-2 group/bar"
                          >
                            <div className="flex justify-between items-end text-sm">
                              <span className="text-slate-300 capitalize font-medium">{key.replace(/_/g, ' ')}</span>
                              <span className="text-slate-500 font-mono text-xs bg-slate-950 px-2 py-0.5 rounded border border-slate-800">{value} <span className="text-slate-600">/ 20</span></span>
                            </div>
                            <div className="h-2.5 w-full bg-slate-950 rounded-full overflow-hidden border border-slate-800/50 shadow-inner relative">
                              <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${(value / 20) * 100}%` }}
                                transition={{ duration: 1, delay: 0.2 + (idx * 0.1), ease: "easeOut" }}
                                className={cn(
                                  "h-full rounded-full relative overflow-hidden",
                                  value === 20 ? "bg-gradient-to-r from-emerald-600 to-emerald-400" :
                                  value >= 10 ? "bg-gradient-to-r from-sky-600 to-sky-400" :
                                  "bg-gradient-to-r from-amber-600 to-amber-400"
                                )}
                              >
                                <div className="absolute inset-0 bg-white/20 w-1/2 -skew-x-12 -translate-x-full group-hover/bar:translate-x-[250%] transition-transform duration-1000 ease-in-out" />
                              </motion.div>
                            </div>
                          </motion.div>
                        ))}
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center h-48 text-slate-500 text-sm">
                        No breakdown data available.
                      </div>
                    )}
                  </div>
                </div>

                {/* Bottom Bento Grid: Rule Checks */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* PII Card */}
                  <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors">
                    <span className="text-slate-400 font-bold text-[10px] uppercase tracking-widest mb-4">PII Detection</span>
                    {req.layer2Governance.piiDetected ? (
                      <div className="flex items-center justify-between">
                        <span className="text-red-400 font-semibold text-lg">Triggered</span>
                        <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center"><XCircle className="w-5 h-5 text-red-500" /></div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <span className="text-emerald-400 font-semibold text-lg">Passed</span>
                        <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center"><CheckCircle2 className="w-5 h-5 text-emerald-500" /></div>
                      </div>
                    )}
                  </div>

                  {/* Toxicity Card */}
                  <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors">
                    <span className="text-slate-400 font-bold text-[10px] uppercase tracking-widest mb-4">Toxicity Check</span>
                    {req.layer2Governance.toxicContent ? (
                      <div className="flex items-center justify-between">
                        <span className="text-red-400 font-semibold text-lg">Triggered</span>
                        <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center"><XCircle className="w-5 h-5 text-red-500" /></div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between">
                        <span className="text-emerald-400 font-semibold text-lg">Passed</span>
                        <div className="w-10 h-10 rounded-full bg-emerald-500/10 flex items-center justify-center"><CheckCircle2 className="w-5 h-5 text-emerald-500" /></div>
                      </div>
                    )}
                  </div>

                  {/* DLP Card */}
                  <div className="bg-slate-900/40 border border-slate-800/80 rounded-2xl p-6 flex flex-col justify-between hover:border-slate-700 transition-colors">
                    <span className="text-slate-400 font-bold text-[10px] uppercase tracking-widest mb-4">Data Loss Prevention</span>
                    <div className="flex items-center justify-between">
                      <span className={cn(
                        "font-semibold text-lg capitalize",
                        req.layer2Governance.dataLossPrevention === 'Pass' || req.layer2Governance.dataLossPrevention === 'None' ? "text-emerald-400" : "text-amber-400"
                      )}>{req.layer2Governance.dataLossPrevention}</span>
                      <div className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center",
                        req.layer2Governance.dataLossPrevention === 'Pass' || req.layer2Governance.dataLossPrevention === 'None' ? "bg-emerald-500/10" : "bg-amber-500/10"
                      )}>
                        {req.layer2Governance.dataLossPrevention === 'Pass' || req.layer2Governance.dataLossPrevention === 'None' ? <CheckCircle2 className="w-5 h-5 text-emerald-500" /> : <ShieldAlert className="w-5 h-5 text-amber-500" />}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Policy Violations (Only shows if there are violations) */}
                {req.layer2Governance.policyViolations.length > 0 && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="bg-red-950/20 border-2 border-red-900/50 rounded-3xl p-8 relative overflow-hidden"
                  >
                    <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-600 via-rose-500 to-red-600" />
                    <span className="block text-sm font-bold text-red-400 uppercase tracking-widest mb-6 flex items-center gap-2">
                      <ShieldAlert className="w-5 h-5" /> Policy Violations Detected
                    </span>
                    <div className="grid grid-cols-1 gap-3">
                      {req.layer2Governance.policyViolations.map((v, i) => (
                        <div key={i} className="flex items-start gap-4 bg-red-950/40 border border-red-900/40 p-4 rounded-xl">
                          <div className="w-8 h-8 rounded-full bg-red-500/20 flex items-center justify-center shrink-0 mt-0.5">
                            <XCircle className="w-4 h-4 text-red-400" />
                          </div>
                          <p className="text-red-200/90 text-sm font-medium leading-relaxed mt-1">
                            {v}
                          </p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
}
