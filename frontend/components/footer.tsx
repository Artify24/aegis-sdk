"use client";

import { Shield } from "lucide-react";
import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-slate-800/50 bg-slate-950/40 backdrop-blur-lg py-12 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative z-10 flex flex-col md:flex-row justify-between items-center gap-6">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-slate-500" />
          <span className="font-display font-medium text-slate-500 tracking-tight">Aegis Cloud Platform</span>
        </div>
        
        <div className="flex items-center gap-6 text-sm text-slate-500">
          <Link href="#" className="hover:text-white transition-colors">Documentation</Link>
          <Link href="#" className="hover:text-white transition-colors">Terms</Link>
          <Link href="#" className="hover:text-white transition-colors">Privacy</Link>
          <Link href="#" className="hover:text-white transition-colors">Enterprise</Link>
        </div>
      </div>
    </footer>
  );
}
