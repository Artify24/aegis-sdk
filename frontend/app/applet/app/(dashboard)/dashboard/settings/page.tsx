"use client";

import { motion } from "motion/react";
import { useAuth } from "@/contexts/auth-context";
import { User, Shield, Key, Bell, CreditCard, Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SettingsPage() {
  const { user } = useAuth();

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const item = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 }
  };

  return (
    <motion.div 
      initial="hidden"
      animate="show"
      variants={container}
      className="max-w-5xl mx-auto space-y-10"
    >
      <motion.div variants={item} className="flex flex-col gap-2 relative">
        <div className="absolute -inset-x-6 -inset-y-4 z-0 bg-gradient-to-r from-sky-500/10 via-transparent to-transparent opacity-50 blur-2xl" />
        <h1 className="text-4xl font-display font-bold tracking-tight text-white relative z-10">Settings</h1>
        <p className="text-slate-400 text-lg relative z-10">Manage your account settings and preferences.</p>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
        <motion.div variants={item} className="md:col-span-3 space-y-1">
          <div className="sticky top-8">
            <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium bg-sky-500/10 text-sky-400 border border-sky-500/20 shadow-[0_0_15px_rgba(56,189,248,0.1)]">
              <User className="w-4 h-4" />
              Profile
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent transition-all">
              <Shield className="w-4 h-4" />
              Security
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent transition-all">
              <Key className="w-4 h-4" />
              API Keys
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent transition-all">
              <CreditCard className="w-4 h-4" />
              Billing
            </button>
            <button className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm text-slate-400 hover:text-slate-200 hover:bg-slate-800/40 border border-transparent transition-all">
              <Bell className="w-4 h-4" />
              Notifications
            </button>
          </div>
        </motion.div>

        <motion.div variants={item} className="md:col-span-9 space-y-8">
          <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800/80 backdrop-blur-md shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-32 bg-sky-500/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 group-hover:bg-sky-500/10 transition-colors duration-700" />
            
            <div className="flex items-center gap-6 border-b border-slate-800/80 pb-8 relative z-10">
              <div className="relative group/avatar cursor-pointer">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center font-display font-bold text-2xl border-4 border-slate-900 shadow-xl text-slate-200 group-hover/avatar:border-slate-700 transition-colors">
                  {user?.name?.substring(0, 2).toUpperCase() || 'US'}
                </div>
                <div className="absolute inset-0 bg-black/60 rounded-full opacity-0 group-hover/avatar:opacity-100 flex items-center justify-center transition-opacity backdrop-blur-sm">
                  <Camera className="w-6 h-6 text-white" />
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-xl font-medium text-white tracking-tight">{user?.name}</h3>
                <p className="text-slate-400 mt-1">{user?.email}</p>
              </div>
              <Button variant="outline" className="bg-slate-900 border-slate-700 hover:bg-slate-800 text-slate-200 rounded-full px-6">
                Change Avatar
              </Button>
            </div>

            <div className="space-y-6 pt-8 relative z-10">
              <div className="grid gap-3">
                <Label htmlFor="name" className="text-slate-300 font-medium">Display Name</Label>
                <Input 
                  id="name" 
                  defaultValue={user?.name} 
                  className="bg-slate-950/50 border-slate-800 text-slate-200 h-12 rounded-xl focus-visible:ring-sky-500/50 focus-visible:border-sky-500/50" 
                />
                <p className="text-sm text-slate-500">This is your public display name. It can be your real name or a pseudonym.</p>
              </div>
              <div className="grid gap-3">
                <Label htmlFor="email" className="text-slate-300 font-medium">Email Address</Label>
                <Input 
                  id="email" 
                  defaultValue={user?.email} 
                  type="email"
                  className="bg-slate-950/50 border-slate-800 text-slate-200 h-12 rounded-xl focus-visible:ring-sky-500/50 focus-visible:border-sky-500/50" 
                />
              </div>
            </div>

            <div className="pt-8 mt-8 border-t border-slate-800/80 flex justify-end relative z-10">
              <Button className="bg-sky-500 hover:bg-sky-400 text-slate-950 font-medium rounded-full px-8 h-11 shadow-[0_0_20px_rgba(56,189,248,0.3)] transition-all">
                Save Changes
              </Button>
            </div>
          </div>

          <div className="p-8 rounded-2xl bg-red-950/10 border border-red-900/20 backdrop-blur-sm space-y-4">
            <h3 className="text-lg font-medium text-red-500">Danger Zone</h3>
            <p className="text-slate-400 leading-relaxed">
              Once you delete your account, there is no going back. All your projects, API keys, and request logs will be permanently removed.
            </p>
            <div className="pt-4">
              <Button variant="outline" className="bg-red-500/5 border-red-500/20 text-red-400 hover:bg-red-500/10 hover:text-red-300 rounded-xl px-6">
                Delete Account
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}
