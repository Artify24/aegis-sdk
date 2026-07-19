"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { motion, AnimatePresence } from "motion/react";
import { 
  Search, Terminal, Activity, ShieldAlert, CheckCircle2, XCircle, Clock, 
  ChevronRight, ArrowRight, Layers, FileJson, Filter, SlidersHorizontal, AlertCircle
} from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Project, ExecutionRequest } from "@/lib/db";
import { cn } from "@/lib/utils";

export default function RequestsPage() {
  const { activeWorkspace } = useAuth();
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [page, setPage] = useState(1);
  const limit = 10;
  const offset = (page - 1) * limit;

  // Load projects to filter by
  const { data: projects = [] } = useQuery<Project[]>({
    queryKey: ["projects", activeWorkspace?.workspace_id],
    queryFn: async () => {
      const { data } = await api.get("/projects", {
        params: { workspace_id: activeWorkspace?.workspace_id }
      });
      return data.map((p: any) => ({
        ...p,
        id: p.project_id || p._id || p.id,
      }));
    },
    enabled: !!activeWorkspace?.workspace_id
  });

  // Set default selected project ID
  useEffect(() => {
    if (projects.length > 0 && !selectedProjectId) {
      setSelectedProjectId(projects[0].id);
    }
  }, [projects, selectedProjectId]);

  const { data, isLoading } = useQuery<{data: ExecutionRequest[], total: number}>({
    queryKey: ["requests", selectedProjectId, search, statusFilter, page],
    queryFn: async () => {
      if (!selectedProjectId) return { data: [], total: 0 };
      
      const params = new URLSearchParams();
      params.append("project_id", selectedProjectId);
      params.append("page", page.toString());
      params.append("limit", limit.toString());
      
      if (statusFilter !== "all") {
        // Map UI filter to backend status (lowercase to uppercase)
        const backendStatusMap: Record<string, string> = {
          success: "SUCCESS",
          blocked: "BLOCKED",
          error: "FAILED" // backend uses FAILED
        };
        params.append("filter_status", backendStatusMap[statusFilter] || "SUCCESS");
      }
      
      const { data } = await api.get(`/executions?${params.toString()}`);
      
      const statusMap: Record<string, "success" | "blocked" | "error"> = {
        SUCCESS: "success",
        BLOCKED: "blocked",
        FAILED: "error",
        CANCELLED: "error"
      };

      const mappedData = (data.data || []).map((item: any) => ({
        id: item.execution_id,
        projectId: selectedProjectId,
        timestamp: item.created_at || new Date().toISOString(),
        status: statusMap[item.status] || "success",
        model: item.model || "GPT-4o",
        durationMs: item.duration_ms || 0,
        tokensTotal: item.tokens_used || 0,
        tokensPrompt: 0,
        tokensCompletion: 0,
        riskScore: item.risk_level || "low",
        governanceScore: item.governance || 100,
        summary: item.summary || `Execution: ${item.execution_id.substring(0, 8)}`,
      }));

      return {
        data: mappedData,
        total: data.meta?.total || 0
      };
    },
    enabled: !!selectedProjectId
  });

  const requests = data?.data || [];
  const total = data?.total || 0;
  const totalPages = Math.ceil(total / limit);

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-20">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold mb-1 text-slate-50 flex items-center gap-3">
            <Terminal className="w-8 h-8 text-sky-400" />
            Request Explorer
          </h1>
          <p className="text-slate-400">Inspect and debug AI executions across your infrastructure.</p>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-4">
        {projects.length > 0 && (
          <div className="flex bg-slate-900/50 border border-slate-800/60 rounded-xl p-1.5 shrink-0 items-center px-3">
            <span className="text-xs text-slate-400 mr-2 font-medium">Project:</span>
            <select
              value={selectedProjectId}
              onChange={(e) => { setSelectedProjectId(e.target.value); setPage(1); }}
              className="bg-transparent text-sm text-slate-200 border-none outline-none focus:ring-0 cursor-pointer"
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id} className="bg-slate-950 text-slate-200">
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input 
            placeholder="Search by ID or summary..." 
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="pl-9 bg-slate-900/50 border-slate-800/60 focus-visible:ring-sky-500/50 rounded-xl w-full"
          />
        </div>
        
        <div className="flex bg-slate-900/50 border border-slate-800/60 rounded-xl p-1 shrink-0">
          {["all", "success", "blocked", "error"].map((s) => (
            <button 
              key={s}
              onClick={() => { setStatusFilter(s); setPage(1); }}
              className={cn(
                "px-4 py-1.5 text-sm font-medium rounded-lg transition-all capitalize flex items-center gap-2",
                statusFilter === s 
                  ? "bg-slate-800 text-slate-100 shadow-sm" 
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/30"
              )}
            >
              {s === 'success' && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />}
              {s === 'blocked' && <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />}
              {s === 'error' && <XCircle className="w-3.5 h-3.5 text-red-400" />}
              {s}
            </button>
          ))}
        </div>
      </div>

      <div className="rounded-2xl border border-slate-800/60 bg-slate-900/40 backdrop-blur-xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800/60 bg-slate-900/60 text-xs uppercase tracking-wider font-semibold text-slate-400">
                <th className="px-6 py-4">Status</th>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Request ID</th>
                <th className="px-6 py-4">Summary</th>
                <th className="px-6 py-4">Model</th>
                <th className="px-6 py-4">Metrics</th>
                <th className="px-6 py-4 text-right"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/40 text-sm">
              {isLoading ? (
                Array.from({ length: 5 }).map((_, i) => (
                  <tr key={i} className="animate-pulse">
                    <td className="px-6 py-5"><div className="h-6 w-20 bg-slate-800/50 rounded-full" /></td>
                    <td className="px-6 py-5"><div className="h-4 w-24 bg-slate-800/50 rounded" /></td>
                    <td className="px-6 py-5"><div className="h-4 w-32 bg-slate-800/50 rounded font-mono" /></td>
                    <td className="px-6 py-5"><div className="h-4 w-48 bg-slate-800/50 rounded" /></td>
                    <td className="px-6 py-5"><div className="h-4 w-24 bg-slate-800/50 rounded" /></td>
                    <td className="px-6 py-5"><div className="h-4 w-20 bg-slate-800/50 rounded" /></td>
                    <td className="px-6 py-5"></td>
                  </tr>
                ))
              ) : requests.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-20 text-center text-slate-500">
                    <Terminal className="w-12 h-12 mx-auto mb-4 text-slate-600" />
                    <p className="text-lg font-medium text-slate-300">No requests found</p>
                    <p className="text-sm mt-1">Try adjusting your search or filters.</p>
                  </td>
                </tr>
              ) : (
                requests.map(req => (
                  <tr key={req.id} className="group hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-5">
                      <span className={cn(
                        "px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 w-fit",
                        req.status === 'success' ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                        req.status === 'blocked' ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                        "bg-red-500/10 text-red-400 border border-red-500/20"
                      )}>
                        {req.status === 'success' && <CheckCircle2 className="w-3.5 h-3.5" />}
                        {req.status === 'blocked' && <ShieldAlert className="w-3.5 h-3.5" />}
                        {req.status === 'error' && <XCircle className="w-3.5 h-3.5" />}
                        <span className="capitalize">{req.status}</span>
                      </span>
                    </td>
                    <td className="px-6 py-5 text-slate-400 text-xs">
                      <div className="flex flex-col">
                        <span>{new Date(req.timestamp).toLocaleDateString()}</span>
                        <span>{new Date(req.timestamp).toLocaleTimeString()}</span>
                      </div>
                    </td>
                    <td className="px-6 py-5">
                      <code className="font-mono text-xs text-sky-400/80 bg-sky-400/10 px-2 py-1 rounded">
                        {req.id.substring(0, 12)}
                      </code>
                    </td>
                    <td className="px-6 py-5 font-medium text-slate-300">
                      {req.summary}
                    </td>
                    <td className="px-6 py-5">
                      <span className="text-xs px-2 py-1 bg-slate-800 text-slate-300 rounded-md border border-slate-700">
                        {req.model}
                      </span>
                    </td>
                    <td className="px-6 py-5 text-xs text-slate-400">
                      <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1" title="Duration">
                          <Clock className="w-3.5 h-3.5 text-slate-500" />
                          {req.durationMs}ms
                        </span>
                        <span className="flex items-center gap-1" title="Tokens">
                          <Activity className="w-3.5 h-3.5 text-slate-500" />
                          {req.tokensTotal}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-5 text-right">
                      <Link href={`/dashboard/requests/${req.id}`}>
                        <Button variant="ghost" size="sm" className="text-sky-400 hover:text-sky-300 hover:bg-sky-400/10">
                          Inspect <ArrowRight className="w-4 h-4 ml-2" />
                        </Button>
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-slate-800/60 pt-4">
          <p className="text-sm text-slate-400">
            Showing <span className="font-medium text-slate-200">{offset + 1}</span> to <span className="font-medium text-slate-200">{Math.min(offset + limit, total)}</span> of <span className="font-medium text-slate-200">{total}</span> results
          </p>
          <div className="flex gap-2">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
            >
              Previous
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="bg-slate-900 border-slate-800 text-slate-300 hover:bg-slate-800 hover:text-slate-100"
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
