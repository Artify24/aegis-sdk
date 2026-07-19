"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import Link from "next/link";
import { Shield, Loader2, ArrowRight } from "lucide-react";
import { useAuth } from "@/contexts/auth-context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "motion/react";

const loginSchema = z.object({
  email: z.string().email({ message: "Invalid email address" }),
  password: z.string().min(1, { message: "Password is required" }),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (data: LoginFormValues) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await api.post("/auth/login", data);
      const userToStore = {
        id: response.data.user?.user_id || "unknown",
        email: response.data.user?.email || data.email,
        name: response.data.user?.username || "User",
      };
      login(response.data.access_token, response.data.refresh_token, userToStore);
    } catch (err: any) {
      setError(err.response?.data?.message || err.response?.data?.detail || "An error occurred during login.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="relative w-full max-w-md mx-auto"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-sky-500/10 via-transparent to-indigo-500/10 blur-3xl -z-10 rounded-[3rem]" />
      
      <div className="flex justify-center mb-8">
        <Link href="/" className="flex flex-col items-center gap-3 group">
          <div className="w-12 h-12 bg-gradient-to-br from-sky-400 to-indigo-600 rounded-2xl flex items-center justify-center shadow-[0_0_20px_rgba(56,189,248,0.5)] group-hover:shadow-[0_0_35px_rgba(56,189,248,0.8)] group-hover:-translate-y-0.5 transition-all duration-300">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <span className="text-lg font-display font-bold tracking-wide text-white group-hover:text-sky-400 transition-colors">Aegis Cloud</span>
        </Link>
      </div>

      <Card className="border-white/10 bg-slate-950/60 backdrop-blur-3xl shadow-[0_0_40px_rgba(0,0,0,0.5)] overflow-hidden">
        <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-sky-500/50 to-transparent" />
        
        <CardHeader className="space-y-3 text-center pb-8 pt-8">
          <CardTitle className="text-3xl font-display tracking-tight text-white">Welcome back</CardTitle>
          <CardDescription className="text-slate-400 text-sm">Enter your credentials to access your workspace</CardDescription>
        </CardHeader>
        
        <CardContent className="px-8 pb-8">
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-slate-300 text-xs uppercase tracking-wider font-semibold">Email Address</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@company.com"
                {...form.register("email")}
                className={`bg-slate-900/50 border-white/5 text-white placeholder:text-slate-600 h-11 transition-all ${form.formState.errors.email ? "border-destructive focus-visible:ring-destructive" : "focus-visible:ring-sky-500 focus-visible:border-sky-500"}`}
              />
              {form.formState.errors.email && (
                <p className="text-xs text-destructive mt-1">{form.formState.errors.email.message}</p>
              )}
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-slate-300 text-xs uppercase tracking-wider font-semibold">Password</Label>
                <Link href="/forgot-password" className="text-xs text-sky-400 hover:text-sky-300 transition-colors">
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                {...form.register("password")}
                className={`bg-slate-900/50 border-white/5 text-white h-11 transition-all ${form.formState.errors.password ? "border-destructive focus-visible:ring-destructive" : "focus-visible:ring-sky-500 focus-visible:border-sky-500"}`}
              />
              {form.formState.errors.password && (
                <p className="text-xs text-destructive mt-1">{form.formState.errors.password.message}</p>
              )}
            </div>

            {error && (
              <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-start gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-destructive mt-1.5 shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}

            <Button type="submit" className="w-full h-12 bg-gradient-to-r from-sky-500 to-indigo-600 hover:from-sky-400 hover:to-indigo-500 text-white font-semibold text-base shadow-[0_0_20px_rgba(56,189,248,0.3)] hover:shadow-[0_0_25px_rgba(56,189,248,0.5)] transition-all mt-6" disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              ) : (
                <>
                  Sign In
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex justify-center border-t border-white/5 bg-slate-900/20 py-5 text-sm text-slate-400">
          Don&apos;t have an account?{" "}
          <Link href="/register" className="text-sky-400 hover:text-sky-300 font-medium ml-1.5 transition-colors">
            Sign up for free
          </Link>
        </CardFooter>
      </Card>
      
      <div className="mt-8 text-center text-xs font-mono text-slate-500/70 bg-slate-900/40 py-2 rounded-lg border border-white/5 backdrop-blur-sm">
        Demo credentials: demo@aegis.cloud / password123
      </div>
    </motion.div>
  );
}
