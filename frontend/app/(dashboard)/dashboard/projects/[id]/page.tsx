"use client";

import { useState, use } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { motion, AnimatePresence } from "motion/react";
import { ArrowLeft, Copy, Plus, Trash2, KeyRound, Shield, AlertTriangle, Eye, Check, Clock, ChevronRight, Database } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Project, ApiKey } from "@/lib/db";
import { cn } from "@/lib/utils";

export default function ProjectDetailsPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const projectId = resolvedParams.id;
  const queryClient = useQueryClient();
  const router = useRouter();
  
  const [activeTab, setActiveTab] = useState<"overview" | "apikeys" | "settings">("apikeys");
  const [isCreateKeyModalOpen, setIsCreateKeyModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [newlyCreatedKey, setNewlyCreatedKey] = useState<ApiKey | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const [keyToRevoke, setKeyToRevoke] = useState<string | null>(null);

  const { data: project, isLoading: isProjectLoading } = useQuery<Project>({
    queryKey: ["project", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}`);
      return {
        ...data,
        id: data.project_id || data._id || data.id,
        requestCount: data.requestCount || 0
      };
    }
  });

  const { data: apiKeys = [], isLoading: isKeysLoading } = useQuery<ApiKey[]>({
    queryKey: ["apikeys", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}/keys`);
      return data.map((k: any) => ({
        id: k.key_id || k._id || k.id,
        projectId: k.project_id || projectId,
        name: k.name || "API Key",
        key: k.key || "",
        maskedKey: k.key_prefix ? `${k.key_prefix}...` : (k.masked_key || k.maskedKey || ""),
        createdAt: k.created_at || k.createdAt,
        lastUsedAt: k.last_used_at || k.lastUsedAt || null,
        status: k.is_active ? "active" : "revoked"
      }));
    },
    enabled: !!project
  });

  const createKey = useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/projects/${projectId}/keys`, { name: newKeyName });
      return {
        id: data.key_id || data._id || data.id,
        projectId: data.project_id || projectId,
        name: data.name || newKeyName,
        key: data.raw_key || data.key || "",
        maskedKey: data.key_prefix ? `${data.key_prefix}...` : (data.masked_key || data.maskedKey || ""),
        createdAt: data.created_at || data.createdAt,
        lastUsedAt: data.last_used_at || data.lastUsedAt || null,
        status: data.is_active ? "active" : "revoked"
      } as ApiKey;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["apikeys", projectId] });
      setNewlyCreatedKey(data);
      setNewKeyName("");
    }
  });

  const revokeKey = useMutation({
    mutationFn: async (keyId: string) => {
      const { data } = await api.put(`/projects/${projectId}/keys/${keyId}/disable`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apikeys", projectId] });
      setKeyToRevoke(null);
    }
  });

  const deleteKey = useMutation({
    mutationFn: async (keyId: string) => {
      await api.delete(`/projects/${projectId}/keys/${keyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["apikeys", projectId] });
    }
  });

  const deleteProject = useMutation({
    mutationFn: async () => {
      await api.delete(`/projects/${projectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      router.push("/dashboard");
    }
  });

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(id);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  if (isProjectLoading) {
    return (
      <div className="max-w-5xl mx-auto space-y-8 animate-pulse">
        <div className="h-8 w-24 bg-slate-800/50 rounded mb-8" />
        <div className="h-12 w-64 bg-slate-800/50 rounded mb-4" />
        <div className="h-10 w-full bg-slate-800/50 rounded-lg mb-8" />
        <div className="h-64 w-full bg-slate-900/40 border border-slate-800/50 rounded-2xl" />
      </div>
    );
  }

  if (!project) {
    return <div className="text-center py-20 text-slate-400">Project not found</div>;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-20">
      <div className="flex items-center gap-2 text-sm text-slate-400 mb-8">
        <Link href="/dashboard" className="hover:text-sky-400 transition-colors flex items-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Projects
        </Link>
        <ChevronRight className="w-4 h-4 text-slate-600" />
        <span className="text-slate-200">{project.name}</span>
      </div>

      <div className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-3xl font-display font-bold text-slate-50">{project.name}</h1>
            <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 ${
              project.environment === 'production' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 
              'bg-sky-500/10 text-sky-400 border border-sky-500/20'
            }`}>
              {project.environment === 'production' ? <Shield className="w-3 h-3" /> : <Database className="w-3 h-3" />}
              {project.environment.charAt(0).toUpperCase() + project.environment.slice(1)}
            </span>
          </div>
          <p className="text-slate-400">{project.description || "No description provided."}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-800/60 pb-px">
        {[
          { id: "overview", label: "Overview" },
          { id: "apikeys", label: "API Keys" },
          { id: "settings", label: "Settings" }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`px-4 py-2.5 text-sm font-medium transition-all relative ${activeTab === tab.id ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'}`}
          >
            {tab.label}
            {activeTab === tab.id && (
              <motion.div layoutId="activeTab" className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400 rounded-t-full" />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.2 }}
        >
          {activeTab === "overview" && (
            <div className="grid md:grid-cols-2 gap-6">
              <div className="p-6 rounded-2xl border border-slate-800/60 bg-slate-900/40 backdrop-blur-xl">
                <h3 className="text-lg font-semibold text-slate-200 mb-1">Project ID</h3>
                <p className="font-mono text-sm text-slate-500 mb-6">{project.id}</p>
                
                <h3 className="text-lg font-semibold text-slate-200 mb-1">Created</h3>
                <p className="text-sm text-slate-500 mb-6">{new Date(project.createdAt).toLocaleDateString()}</p>
                
                <h3 className="text-lg font-semibold text-slate-200 mb-1">Total Requests</h3>
                <p className="font-mono text-2xl text-slate-100">{project.requestCount.toLocaleString()}</p>
              </div>
            </div>
          )}

          {activeTab === "apikeys" && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-slate-200 mb-1">API Keys</h2>
                  <p className="text-sm text-slate-400">Manage keys used to authenticate API requests.</p>
                </div>
                <Button onClick={() => setIsCreateKeyModalOpen(true)} className="rounded-full bg-slate-100 text-slate-900 hover:bg-slate-200 transition-colors">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Key
                </Button>
              </div>

              <div className="rounded-2xl border border-slate-800/60 bg-slate-900/40 backdrop-blur-xl overflow-hidden shadow-2xl">
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-slate-800/60 bg-slate-900/60 text-xs uppercase tracking-wider font-semibold text-slate-400">
                        <th className="px-6 py-4">Name</th>
                        <th className="px-6 py-4">Key</th>
                        <th className="px-6 py-4">Created</th>
                        <th className="px-6 py-4">Last Used</th>
                        <th className="px-6 py-4 text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/40 text-sm">
                      {isKeysLoading ? (
                        [1,2].map(i => (
                          <tr key={i} className="animate-pulse">
                            <td className="px-6 py-5"><div className="h-4 w-24 bg-slate-800/50 rounded" /></td>
                            <td className="px-6 py-5"><div className="h-4 w-48 bg-slate-800/50 rounded font-mono" /></td>
                            <td className="px-6 py-5"><div className="h-4 w-20 bg-slate-800/50 rounded" /></td>
                            <td className="px-6 py-5"><div className="h-4 w-20 bg-slate-800/50 rounded" /></td>
                            <td className="px-6 py-5"><div className="h-8 w-8 bg-slate-800/50 rounded-full ml-auto" /></td>
                          </tr>
                        ))
                      ) : apiKeys.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-6 py-12 text-center text-slate-500">
                            <KeyRound className="w-8 h-8 mx-auto mb-3 text-slate-600" />
                            <p>No API keys found. Create one to get started.</p>
                          </td>
                        </tr>
                      ) : (
                        apiKeys.map(key => (
                          <tr key={key.id} className="group hover:bg-slate-800/20 transition-colors">
                            <td className="px-6 py-5">
                              <div className="flex items-center gap-2">
                                <span className={cn("font-medium", key.status === 'revoked' ? "text-slate-500 line-through" : "text-slate-200")}>{key.name}</span>
                                {key.status === 'revoked' && (
                                  <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-red-500/10 text-red-400 border border-red-500/20">Revoked</span>
                                )}
                              </div>
                            </td>
                            <td className="px-6 py-5">
                              <div className="flex items-center gap-3">
                                <code className={cn("font-mono text-xs px-2 py-1 rounded bg-slate-950/50 border", key.status === 'revoked' ? "text-slate-600 border-slate-800" : "text-sky-300 border-sky-900/30")}>
                                  {key.maskedKey}
                                </code>
                              </div>
                            </td>
                            <td className="px-6 py-5 text-slate-400 text-xs">
                              {new Date(key.createdAt).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-5 text-slate-400 text-xs">
                              {key.lastUsedAt ? new Date(key.lastUsedAt).toLocaleDateString() : 'Never'}
                            </td>
                            <td className="px-6 py-5 text-right">
                              <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                {key.status === 'active' && (
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-8 px-2 text-slate-400 hover:text-amber-400 hover:bg-amber-400/10"
                                    onClick={() => setKeyToRevoke(key.id)}
                                  >
                                    Revoke
                                  </Button>
                                )}
                                {key.status === 'revoked' && (
                                  <Button 
                                    variant="ghost" 
                                    size="sm" 
                                    className="h-8 px-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10"
                                    onClick={() => deleteKey.mutate(key.id)}
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </Button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === "settings" && (
            <div className="max-w-2xl space-y-8">
              <div className="p-6 rounded-2xl border border-red-900/30 bg-red-950/10 backdrop-blur-xl">
                <h3 className="text-lg font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" /> Danger Zone
                </h3>
                <p className="text-sm text-slate-400 mb-6">Once you delete a project, there is no going back. Please be certain.</p>
                <Button 
                  onClick={() => setIsDeleteModalOpen(true)}
                  variant="destructive" 
                  className="bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20 rounded-full"
                >
                  Delete Project
                </Button>
              </div>
            </div>
          )}
        </motion.div>
      </AnimatePresence>

      {/* Create Key Drawer/Modal */}
      <AnimatePresence>
        {(isCreateKeyModalOpen || newlyCreatedKey) && (
          <div className="fixed inset-0 z-50 flex justify-end">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
              onClick={() => !newlyCreatedKey && setIsCreateKeyModalOpen(false)}
            />
            <motion.div 
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col"
            >
              {!newlyCreatedKey ? (
                <>
                  <div className="p-6 border-b border-slate-800">
                    <h2 className="text-xl font-bold text-white mb-1">Create API Key</h2>
                    <p className="text-slate-400 text-sm">Create a new key to authenticate requests from your application.</p>
                  </div>
                  
                  <div className="p-6 flex-1 overflow-y-auto space-y-6">
                    <div>
                      <label className="block text-sm font-medium text-slate-300 mb-2">Key Name</label>
                      <Input 
                        placeholder="e.g. Production Worker" 
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        className="bg-slate-950/50 border-slate-800"
                        autoFocus
                      />
                    </div>
                  </div>
                  
                  <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex gap-3 justify-end">
                    <Button variant="ghost" onClick={() => setIsCreateKeyModalOpen(false)} className="rounded-full hover:bg-slate-800 text-slate-300">
                      Cancel
                    </Button>
                    <Button 
                      onClick={() => createKey.mutate()} 
                      disabled={!newKeyName.trim() || createKey.isPending}
                      className="rounded-full bg-slate-100 text-slate-900 hover:bg-slate-200"
                    >
                      {createKey.isPending ? "Creating..." : "Create Key"}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex flex-col h-full justify-center p-8">
                  <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                    <Check className="w-8 h-8 text-emerald-400" />
                  </div>
                  <h2 className="text-2xl font-bold text-white mb-2 text-center">API Key Created</h2>
                  <p className="text-slate-400 text-sm mb-8 text-center leading-relaxed">Please copy this key now. For your security, you won&apos;t be able to see it again after closing this drawer.</p>
                  
                  <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 mb-8 flex flex-col gap-4">
                    <code className="text-sky-300 font-mono text-sm break-all text-center">{newlyCreatedKey.key}</code>
                    <Button 
                      variant="outline" 
                      onClick={() => handleCopy(newlyCreatedKey.key, newlyCreatedKey.id)}
                      className="w-full bg-slate-900 border-slate-800 text-slate-300 hover:text-white"
                    >
                      {copiedKey === newlyCreatedKey.id ? (
                        <><Check className="w-4 h-4 mr-2 text-emerald-400" /> Copied!</>
                      ) : (
                        <><Copy className="w-4 h-4 mr-2" /> Copy to clipboard</>
                      )}
                    </Button>
                  </div>

                  <Button 
                    onClick={() => {
                      setNewlyCreatedKey(null);
                      setIsCreateKeyModalOpen(false);
                    }} 
                    className="w-full rounded-full bg-slate-100 text-slate-900 hover:bg-slate-200 py-6"
                  >
                    I have saved this key safely
                  </Button>
                </div>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Revoke Key Modal */}
      <AnimatePresence>
        {keyToRevoke && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
              onClick={() => setKeyToRevoke(null)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-sm bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6 text-center"
            >
              <div className="w-12 h-12 rounded-full bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Revoke API Key?</h2>
              <p className="text-slate-400 text-sm mb-6">Any application using this key will immediately be denied access. This action cannot be undone.</p>
              
              <div className="flex gap-3 justify-center">
                <Button variant="ghost" onClick={() => setKeyToRevoke(null)} className="rounded-full hover:bg-slate-800 text-slate-300 w-full">
                  Cancel
                </Button>
                <Button 
                  onClick={() => revokeKey.mutate(keyToRevoke)} 
                  disabled={revokeKey.isPending}
                  variant="destructive"
                  className="rounded-full bg-amber-500/10 text-amber-500 hover:bg-amber-500/20 border border-amber-500/20 w-full"
                >
                  {revokeKey.isPending ? "Revoking..." : "Revoke Key"}
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Delete Project Modal */}
      <AnimatePresence>
        {isDeleteModalOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm"
              onClick={() => setIsDeleteModalOpen(false)}
            />
            <motion.div 
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="relative w-full max-w-sm bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden p-6 text-center"
            >
              <div className="w-12 h-12 rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-4">
                <AlertTriangle className="w-6 h-6 text-red-500" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Delete Project?</h2>
              <p className="text-slate-400 text-sm mb-6">This will delete &quot;{project.name}&quot; and all of its associated API keys. This action cannot be undone.</p>
              
              <div className="flex gap-3 justify-center">
                <Button variant="ghost" onClick={() => setIsDeleteModalOpen(false)} className="rounded-full hover:bg-slate-800 text-slate-300 w-full">
                  Cancel
                </Button>
                <Button 
                  onClick={() => deleteProject.mutate()} 
                  disabled={deleteProject.isPending}
                  variant="destructive"
                  className="rounded-full bg-red-500/10 text-red-500 hover:bg-red-500/20 border border-red-500/20 w-full"
                >
                  {deleteProject.isPending ? "Deleting..." : "Delete Project"}
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
