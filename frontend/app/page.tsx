"use client";

import { motion } from "motion/react";
import { Navbar } from "@/components/navbar";
import { Footer } from "@/components/footer";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ActivitySquare, ArrowRight, BarChart3, BrainCircuit, Code2, Database, Key, LayoutTemplate, LineChart, Lock, Shield, Terminal, Workflow, Zap } from "lucide-react";
import Link from "next/link";
import { ArchitectureFlow } from "@/components/architecture-flow";
import { Activity } from "react";

const fadeIn = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 }
};

const stagger = {
  animate: {
    transition: {
      staggerChildren: 0.1
    }
  }
};

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col relative bg-slate-950 text-slate-50">
      <div className="absolute inset-0 bg-grid-pattern opacity-20 fixed pointer-events-none" />
      <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_50%_50%,_rgba(56,189,248,0.08),transparent_70%)] fixed pointer-events-none" />
      <Navbar />

      <main className="flex-1 pb-16">
        {/* Hero Section */}
        <section className="relative pt-17 pb-20 px-6 lg:px-16 xl:px-24 w-full flex flex-col lg:flex-row items-center text-left gap-12 lg:gap-16">
          <div className="glow-effect absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-2xl h-[400px] opacity-30 pointer-events-none" />

          <motion.div
            initial="initial"
            animate="animate"
            variants={stagger}
            className="relative z-10 w-full lg:w-[40%] shrink-0"
          >
            <motion.div variants={fadeIn} className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-sky-500/30 bg-sky-500/10 text-sky-400 text-xs font-semibold mb-6 uppercase tracking-widest">
              <Shield className="w-4 h-4" />
              <span>Enterprise AI Runtime Platform</span>
            </motion.div>

            <motion.h1 variants={fadeIn} className="text-5xl md:text-6xl font-display font-bold tracking-tight mb-6 leading-[1.1] bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
              Scale AI Infrastructure <br />
              <span className="text-sky-400">
                Without the Complexity
              </span>
            </motion.h1>

            <motion.p variants={fadeIn} className="text-lg md:text-xl text-slate-400 mb-10 leading-relaxed">
              Aegis Cloud provides the necessary runtime environment for enterprise AI applications. Provision API keys, manage rate limits, and inspect requests with zero overhead.
            </motion.p>

            <motion.div variants={fadeIn} className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
              <Link href="/register">
                <Button size="lg" className="h-12 px-8 text-base group">
                  Start Building
                  <ArrowRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="h-12 px-8 text-base">
                  View Documentation
                </Button>
              </Link>
            </motion.div>
          </motion.div>

          <div className="relative z-10 w-full lg:w-[60%] flex items-center justify-center min-h-[600px] -mt-12 lg:mt-0">
            <ArchitectureFlow />
          </div>
        </section>

        {/* The Problem Section */}
        <section
          id="the-problem"
          className="py-24 px-6 max-w-7xl mx-auto relative z-10 border-t border-slate-800/50 mt-12"
        >
          <div className="grid md:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl font-display font-bold mb-6 text-slate-50">
                Your AI agent works.
                <br />
                <span className="text-slate-400">
                  Production is where everything breaks.
                </span>
              </h2>

              <p className="text-slate-400 mb-6 text-lg leading-relaxed">
                Building an AI agent is easy. Running it safely at scale isn't.
              </p>

              <p className="text-slate-400 mb-8 text-lg leading-relaxed">
                Once your agent reaches production, you need governance, observability,
                security, and complete visibility into every decision it makes. Without
                them, debugging failures, investigating risky actions, and trusting AI
                becomes nearly impossible.
              </p>

              <div className="space-y-4">
                {[
                  "No visibility into what your AI agent actually did",
                  "No governance before sensitive tools are executed",
                  "Impossible to debug prompts after deployment",
                  "No audit trail for AI decisions and tool calls",
                  "No centralized runtime for monitoring every request",
                ].map((item, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-3 text-slate-300 bg-slate-900/50 p-4 rounded-xl border border-slate-800/50"
                  >
                    <div className="w-1.5 h-1.5 rounded-full bg-red-400" />
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="relative">
              <div className="absolute inset-0 bg-cyan-500/10 blur-[120px] rounded-full pointer-events-none" />

              <div className="rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl p-8 shadow-2xl relative overflow-hidden">

                <div className="space-y-6">

                  <div className="flex items-start gap-4 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-sm font-mono text-red-200">
                    <Terminal className="w-5 h-5 mt-0.5 shrink-0" />
                    <div>
                      <div>Execution Blocked</div>
                      <div className="text-red-400/70 mt-1">
                        Policy Engine denied database deletion request.
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-4 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-sm font-mono text-amber-200">
                    <Terminal className="w-5 h-5 mt-0.5 shrink-0" />
                    <div>
                      <div>High Risk Action Detected</div>
                      <div className="text-amber-400/70 mt-1">
                        Risk Score: 0.91 • Human approval required.
                      </div>
                    </div>
                  </div>

                  <div className="flex items-start gap-4 p-4 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-sm font-mono text-cyan-200">
                    <Terminal className="w-5 h-5 mt-0.5 shrink-0" />
                    <div>
                      <div>Execution Trace Available</div>
                      <div className="text-cyan-300/70 mt-1">
                        View Layer 1 → Governance → Planner → Tool Calls → Response
                      </div>
                    </div>
                  </div>

                </div>
              </div>
            </div>
          </div>
        </section>

        {/* SDK Integration Section */}
        <section
          id="sdk"
          className="py-24 px-6 max-w-7xl mx-auto relative z-10 border-t border-slate-800/50"
        >
          <div className="grid md:grid-cols-2 gap-16 items-center">

            <div>
              <h2 className="text-3xl font-display font-bold mb-6 text-slate-50">
                Integrate once.
                <br />
                Govern every AI request.
              </h2>

              <p className="text-slate-400 mb-8 text-lg leading-relaxed">
                Aegis integrates directly into your AI application, automatically adding
                request intelligence, execution governance, runtime control, and complete
                observability without changing the way you build AI agents.
              </p>

              <div className="space-y-6">
                {[
                  {
                    title: "Works With Your Existing Stack",
                    description:
                      "Compatible with LangGraph, CrewAI, OpenAI, Gemini, Claude, and custom AI workflows with minimal integration effort."
                  },
                  {
                    title: "Automatic Governance & Tracing",
                    description:
                      "Every request is analyzed, governed, executed, and traced automatically, giving your team complete visibility into production."
                  }
                ].map((item, i) => (
                  <div key={i} className="flex gap-4">
                    <div className="mt-1">
                      <div className="w-6 h-6 rounded-full bg-sky-500/20 flex items-center justify-center">
                        <div className="w-2 h-2 rounded-full bg-sky-400" />
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-lg mb-1 text-slate-200">
                        {item.title}
                      </h4>

                      <p className="text-slate-400">
                        {item.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 shadow-2xl relative overflow-hidden backdrop-blur-xl">

              <div className="absolute top-0 right-0 w-64 h-64 bg-sky-500/10 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />

              <div className="flex items-center gap-2 mb-4 text-sm text-slate-400 font-mono pb-4 border-b border-slate-800/50">
                <Terminal className="w-4 h-4 text-sky-400" />
                <span>quick-start.py</span>
              </div>

              <pre className="font-mono text-sm text-slate-300 overflow-x-auto leading-relaxed">
                <code>

                  <span className="text-sky-400">pip</span> install aegis-ai

                  {"\n\n"}

                  <span className="text-indigo-400">from</span>{" "}
                  <span className="text-emerald-400">aegis</span>{" "}
                  <span className="text-indigo-400">import</span>{" "}
                  Aegis

                  {"\n\n"}

                  aegis = Aegis({"{"}
                  {"\n"}
                  {"  "}api_key=<span className="text-amber-300">"ag_live_xxxxxxxxx"</span>
                  {"\n"}
                  {"}"})

                  {"\n\n"}

                  <span className="text-slate-500">
                    # Every request is automatically analyzed
                  </span>

                  {"\n"}

                  response = aegis.invoke({"{"}

                  {"\n"}

                  {"  "}prompt=<span className="text-emerald-400">
                    "Summarize this report"
                  </span>

                  {"\n"}

                  {"}"})

                  {"\n\n"}

                  <span className="text-slate-500">
                    # View the full execution inside Aegis Cloud
                  </span>

                </code>
              </pre>

            </div>

          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-24 px-6 max-w-7xl mx-auto relative z-10 border-t border-slate-800/50">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-display font-bold mb-4 text-slate-50">Enterprise Grade Infrastructure</h2>
            <p className="text-slate-400 max-w-2xl mx-auto">Everything you need to ship production AI applications safely and reliably.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: <Shield className="w-6 h-6 text-cyan-400" />,
                title: "Request Intelligence",
                description:
                  "Every AI request is analyzed before execution with intent detection, capability analysis, prompt validation, and risk assessment."
              },
              {
                icon: <Lock className="w-6 h-6 text-cyan-400" />,
                title: "Execution Governance",
                description:
                  "Enforce policies, authorize tools, apply least-privilege access, and block unsafe actions before they reach your AI agent."
              },
              {
                icon: <Workflow className="w-6 h-6 text-cyan-400" />,
                title: "Runtime Control",
                description:
                  "Centralized execution engine that orchestrates planning, tool execution, retries, streaming, and provider management."
              },
              {
                icon: <ActivitySquare className="w-6 h-6 text-cyan-400" />,
                title: "Execution Tracing",
                description:
                  "Visualize every request from prompt to response, including governance decisions, planner steps, timelines, and tool calls."
              },
              {
                icon: <BrainCircuit className="w-6 h-6 text-cyan-400" />,
                title: "Memory & Context",
                description:
                  "Maintain conversation state and long-term memory while validating context before every execution."
              },
              {
                icon: <BarChart3 className="w-6 h-6 text-cyan-400" />,
                title: "Execution Intelligence",
                description:
                  "Automatically generate governance scores, audit reports, security insights, performance metrics, and execution analytics."
              }
            ].map((feature, i) => (
              <Card key={i} className="bg-slate-900/40 border-slate-800 hover:border-slate-700 transition-colors shadow-none hover:shadow-2xl">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-xl">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-base text-slate-400">{feature.description}</CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </section>



      </main>

      <Footer />
    </div>
  );
}
