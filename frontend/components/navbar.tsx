"use client";

import Link from "next/link";
import { useAuth } from "@/contexts/auth-context";
import { Button } from "@/components/ui/button";
import { Shield } from "lucide-react";

export function Navbar() {
  const { user, logout } = useAuth();

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 w-full max-w-5xl z-50 px-4">
      <nav className="flex items-center justify-between px-6 h-16 border border-slate-800/60 backdrop-blur-xl bg-slate-950/70 rounded-full shadow-2xl shadow-sky-900/10">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-sky-400 to-indigo-600 rounded-full flex items-center justify-center shadow-[0_0_15px_rgba(56,189,248,0.4)]">
            <Shield className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-lg tracking-tight text-white">Aegis <span className="text-sky-400">Cloud</span></span>
        </Link>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
          <Link href="#the-problem" className="hover:text-slate-200 transition-colors">The Problem</Link>
          <Link href="#how-it-works" className="hover:text-slate-200 transition-colors">How it Works</Link>
          <Link href="#features" className="hover:text-slate-200 transition-colors">Features</Link>
        </div>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <Link href="/dashboard">
                <Button variant="ghost" className="hidden sm:inline-flex rounded-full">Dashboard</Button>
              </Link>
              <Button variant="outline" onClick={logout} className="rounded-full">Sign Out</Button>
            </>
          ) : (
            <>
              <Link href="/login">
                <Button variant="ghost" className="rounded-full">Sign In</Button>
              </Link>
              <Link href="/register">
                <Button className="rounded-full px-6">Get Started</Button>
              </Link>
            </>
          )}
        </div>
      </nav>
    </div>
  );
}
