"use client";

import { useEffect } from "react";
import { AlertCircle, RefreshCcw } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-6 text-center relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(239,68,68,0.05)_0%,rgba(2,6,23,1)_70%)] pointer-events-none" />
      
      <div className="relative z-10 space-y-6 max-w-md animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="w-20 h-20 bg-slate-900/80 rounded-2xl border border-red-900/30 flex items-center justify-center mx-auto mb-8 shadow-2xl backdrop-blur-xl">
          <AlertCircle className="w-10 h-10 text-red-400" />
        </div>
        
        <h1 className="text-2xl font-display font-bold text-slate-100 tracking-tight">Something went wrong</h1>
        <p className="text-slate-400 text-sm leading-relaxed">
          An unexpected error occurred while processing your request. Our team has been notified.
        </p>
        
        <div className="pt-6">
          <Button onClick={() => reset()} className="rounded-full bg-slate-100 text-slate-950 hover:bg-slate-200 px-8">
            <RefreshCcw className="w-4 h-4 mr-2" /> Try again
          </Button>
        </div>
      </div>
    </div>
  );
}
