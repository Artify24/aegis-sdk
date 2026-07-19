"use client";

import { useAuth } from "@/contexts/auth-context";
import { Shield, LayoutDashboard, Terminal, Settings, LogOut } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "motion/react";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout, workspaces, activeWorkspace, setActiveWorkspace } = useAuth();
  const pathname = usePathname();

  const navItems = [
    { name: "Projects", href: "/dashboard", icon: LayoutDashboard },
    { name: "Requests", href: "/dashboard/requests", icon: Terminal },
    { name: "Settings", href: "/dashboard/settings", icon: Settings },
  ];

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-950 flex text-slate-50 selection:bg-sky-500/20">
      {/* Sidebar */}
      <aside className="w-64 border-r border-slate-800/50 flex flex-col bg-[#0A0E17]/80 backdrop-blur-2xl fixed inset-y-0 z-20 shadow-2xl">
        <div className="h-16 flex items-center px-6 border-b border-slate-800/50">
          <Link href="/dashboard" className="flex items-center gap-2 group">
            <div className="w-7 h-7 bg-gradient-to-br from-sky-400 to-indigo-600 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(56,189,248,0.4)] group-hover:shadow-[0_0_20px_rgba(56,189,248,0.6)] transition-all">
              <Shield className="w-4 h-4 text-white" />
            </div>
            <span className="font-display font-bold tracking-tight text-white group-hover:text-slate-200 transition-colors">Aegis <span className="text-sky-400">Cloud</span></span>
          </Link>
        </div>
        
        <div className="px-4 py-6">
          <div className="flex items-center gap-3 px-3 py-3 rounded-xl bg-slate-900/50 border border-slate-800/80 mb-8 shadow-inner">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center font-semibold text-xs border border-slate-600 text-slate-200 shadow-sm shrink-0">
              {user.name.substring(0, 2).toUpperCase()}
            </div>
            <div className="flex flex-col flex-1 overflow-hidden">
              <span className="text-sm font-medium text-slate-200 truncate leading-tight">{user.name}</span>
              {workspaces.length > 1 ? (
                <select
                  value={activeWorkspace?.workspace_id || ""}
                  onChange={(e) => {
                    const ws = workspaces.find(w => w.workspace_id === e.target.value);
                    if (ws) setActiveWorkspace(ws);
                  }}
                  className="text-xs text-sky-400 bg-transparent border-none outline-none p-0 cursor-pointer w-full"
                >
                  {workspaces.map(w => (
                    <option key={w.workspace_id} value={w.workspace_id} className="bg-slate-950 text-slate-200">
                      {w.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-xs text-slate-400 truncate leading-tight">{activeWorkspace?.name || "Personal Workspace"}</span>
              )}
            </div>
          </div>
          
          <nav className="space-y-1.5">
            {navItems.map((item) => {
              const isActive = pathname === item.href;
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 group relative",
                    isActive 
                      ? "bg-sky-500/10 text-sky-400 font-medium border border-sky-500/20 shadow-[inset_0_1px_0_rgba(255,255,255,0.05)]" 
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent"
                  )}
                >
                  {isActive && (
                    <motion.div 
                      layoutId="activeNavIndicator" 
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-5 bg-sky-500 rounded-r-full"
                    />
                  )}
                  <Icon className={cn("w-4 h-4 transition-colors", isActive ? "text-sky-400" : "group-hover:text-slate-300")} />
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>
        
        <div className="mt-auto p-4 border-t border-slate-800/50">
          <button 
            onClick={logout}
            className="flex items-center gap-3 px-3 py-2.5 w-full rounded-lg text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors group"
          >
            <LogOut className="w-4 h-4 group-hover:text-red-400 transition-colors" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 ml-64 relative min-h-screen flex flex-col">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-sky-900/10 via-slate-950 to-slate-950 pointer-events-none" />
        <div className="absolute inset-0 bg-grid-pattern opacity-[0.02] pointer-events-none" />
        <div className="p-8 relative z-10 flex-1 overflow-x-hidden">
          <AnimatePresence mode="wait">
            <motion.div
              key={pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
