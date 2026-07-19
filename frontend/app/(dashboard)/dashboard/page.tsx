"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/auth-context";
import { motion, AnimatePresence } from "motion/react";
import { Plus, Search, MoreVertical, LayoutGrid, Clock, Shield, Database, ChevronRight, Copy, Check } from "lucide-react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Project } from "@/lib/db";

export default function ProjectsPage() {
  const queryClient = useQueryClient();
  const { activeWorkspace } = useAuth();
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "recent">("recent");
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newProjectDesc, setNewProjectDesc] = useState("");
  const [newProjectEnv, setNewProjectEnv] = useState<"development" | "production">("development");

  // State to hold and display the default API key generated on project creation
  const [createdProject, setCreatedProject] = useState<{ name: string, id: string } | null>(null);
  const [createdApiKey, setCreatedApiKey] = useState<string | null>(null);
  const [copiedProjectKey, setCopiedProjectKey] = useState(false);

  const { data: projects = [], isLoading } = useQuery<Project[]>({
    queryKey: ["projects", activeWorkspace?.workspace_id],
    queryFn: async () => {
      const { data } = await api.get("/projects", {
        params: { workspace_id: activeWorkspace?.workspace_id }
      });
      return data.map((p: any) => ({
        ...p,
        id: p.project_id || p._id || p.id,
        requestCount: p.requestCount || 0,
      }));
    },
    enabled: !!activeWorkspace?.workspace_id
  });

  const createProject = useMutation({
    mutationFn: async () => {
      const { data } = await api.post("/projects", { 
        workspace_id: activeWorkspace?.workspace_id,
        name: newProjectName, 
        description: newProjectDesc,
        environment: newProjectEnv 
      });
      return data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["projects", activeWorkspace?.workspace_id] });
      setIsCreateModalOpen(false);
      
      const projId = data.project?.project_id || data.project?._id || data.project?.id || "";
      setCreatedProject({
        name: data.project?.name || newProjectName,
        id: projId
      });
      setCreatedApiKey(data.default_api_key);
      
      setNewProjectName("");
      setNewProjectDesc("");
      setNewProjectEnv("development");
    }
  });

  const handleCopyProjectKey = () => {
    if (createdApiKey) {
      navigator.clipboard.writeText(createdApiKey);
      setCopiedProjectKey(true);
      setTimeout(() => setCopiedProjectKey(false), 2000);
    }
  };

  const filteredProjects = projects
    .filter(p => p.name.toLowerCase().includes(search.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === "name") {
        return a.name.localeCompare(b.name);
      }
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
    });

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-bold mb-1 text-slate-50">Projects</h1>
          <p className="text-slate-400">Manage your application environments and API keys.</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)} className="rounded-full bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold shadow-[0_0_15px_rgba(56,189,248,0.3)] hover:shadow-[0_0_25px_rgba(56,189,248,0.5)] transition-all">
          <Plus className="w-4 h-4 mr-2" />
          Create Project
        </Button>
      </div>

      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <Input 
            placeholder="Search projects..." 
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 bg-slate-900/50 border-slate-800/60 focus-visible:ring-sky-500/50 rounded-xl w-full"
          />
        </div>
        <div className="flex bg-slate-900/50 border border-slate-800/60 rounded-xl p-1 shrink-0">
          <button 
            onClick={() => setSortBy("recent")}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${sortBy === 'recent' ? 'bg-slate-800 text-slate-200' : 'text-slate-400 hover:text-slate-300'}`}
          >
            Recent
          </button>
          <button 
            onClick={() => setSortBy("name")}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${sortBy === 'name' ? 'bg-slate-800 text-slate-200' : 'text-slate-400 hover:text-slate-300'}`}
          >
            Name
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {isLoading ? (
          [1, 2, 3].map(i => (
            <div key={i} className="h-48 rounded-2xl border border-slate-800/60 bg-slate-900/40 p-6 animate-pulse backdrop-blur-xl">
              <div className="h-6 w-3/4 bg-slate-800/80 rounded mb-4" />
              <div className="h-4 w-1/2 bg-slate-800/80 rounded mb-8" />
              <div className="flex gap-2">
                <div className="h-6 w-20 bg-slate-800/80 rounded-full" />
                <div className="h-6 w-20 bg-slate-800/80 rounded-full" />
              </div>
            </div>
          ))
        ) : filteredProjects.length === 0 ? (
          <div className="col-span-full py-20 text-center border border-slate-800/50 border-dashed rounded-2xl bg-slate-900/20 backdrop-blur-sm">
            <LayoutGrid className="w-12 h-12 text-slate-600 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-slate-300 mb-2">No projects found</h3>
            <p className="text-slate-500 max-w-sm mx-auto mb-6">
              {search ? "No projects match your search criteria." : "Get started by creating your first project."}
            </p>
            {!search && (
              <Button onClick={() => setIsCreateModalOpen(true)} variant="outline" className="rounded-full">
                Create your first project
              </Button>
            )}
          </div>
        ) : (
          filteredProjects.map((project) => (
            <Link key={project.id} href={`/dashboard/projects/${project.id}`}>
              <motion.div 
                whileHover={{ y: -4, scale: 1.01 }}
                className="group relative h-full rounded-2xl border border-slate-800/60 bg-slate-900/40 p-6 shadow-xl backdrop-blur-xl hover:border-sky-500/30 hover:shadow-[0_8px_30px_rgba(56,189,248,0.1)] transition-all overflow-hidden"
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-sky-500 to-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity" />
                <div className="flex justify-between items-start mb-4">
                  <h3 className="text-xl font-bold text-slate-100 group-hover:text-sky-400 transition-colors">{project.name}</h3>
                  <div className="p-1.5 rounded-full bg-slate-800/50 text-slate-400 group-hover:bg-sky-500/10 group-hover:text-sky-400 transition-colors">
                    <ChevronRight className="w-4 h-4" />
                  </div>
                </div>
                
                <p className="text-sm text-slate-400 mb-6 line-clamp-2 min-h-[40px]">
                  {project.description || "No description provided."}
                </p>

                <div className="flex flex-wrap items-center gap-2 mb-6">
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 ${
                    project.status === 'active' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
                    'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}>
                    <span className={`w-1.5 h-1.5 rounded-full ${project.status === 'active' ? 'bg-emerald-400 animate-pulse' : 'bg-slate-400'}`} />
                    {project.status.toUpperCase()}
                  </span>
                  
                  <span className={`px-2.5 py-1 rounded-full text-xs font-semibold flex items-center gap-1.5 ${
                    project.environment === 'production' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 
                    'bg-sky-500/10 text-sky-400 border border-sky-500/20'
                  }`}>
                    {project.environment === 'production' ? <Shield className="w-3 h-3" /> : <Database className="w-3 h-3" />}
                    {project.environment.charAt(0).toUpperCase() + project.environment.slice(1)}
                  </span>
                </div>

                <div className="pt-4 border-t border-slate-800/50 flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Updated {new Date(project.updatedAt).toLocaleDateString()}</span>
                  </div>
                  <div className="font-mono text-slate-400">
                    {project.requestCount.toLocaleString()} reqs
                  </div>
                </div>
              </motion.div>
            </Link>
          ))
        )}
      </div>

      {/* Create Project Drawer */}
      <AnimatePresence>
        {isCreateModalOpen && (
          <div className="fixed inset-0 z-50 flex justify-end">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
              onClick={() => setIsCreateModalOpen(false)}
            />
            <motion.div 
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col"
            >
              <div className="p-6 border-b border-slate-800">
                <h2 className="text-xl font-bold text-white mb-1">Create Project</h2>
                <p className="text-slate-400 text-sm">Create a new isolated environment.</p>
              </div>
              
              <div className="p-6 flex-1 overflow-y-auto space-y-6">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Project Name</label>
                  <Input 
                    placeholder="e.g. Acme Corp Support" 
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="bg-slate-950/50 border-slate-800"
                    autoFocus
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Description</label>
                  <Input 
                    placeholder="e.g. Production LLM router for Zendesk" 
                    value={newProjectDesc}
                    onChange={(e) => setNewProjectDesc(e.target.value)}
                    className="bg-slate-950/50 border-slate-800"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Environment</label>
                  <div className="grid grid-cols-2 gap-3">
                    <button 
                      onClick={() => setNewProjectEnv("development")}
                      className={`flex flex-col items-start p-4 rounded-xl border transition-all ${newProjectEnv === 'development' ? 'bg-sky-500/10 border-sky-500/30 text-sky-400' : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:bg-slate-800'}`}
                    >
                      <Database className="w-5 h-5 mb-2 opacity-80" />
                      <span className="font-medium text-sm">Development</span>
                      <span className="text-xs opacity-60 mt-1 text-left">For testing and staging</span>
                    </button>
                    <button 
                      onClick={() => setNewProjectEnv("production")}
                      className={`flex flex-col items-start p-4 rounded-xl border transition-all ${newProjectEnv === 'production' ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:bg-slate-800'}`}
                    >
                      <Shield className="w-5 h-5 mb-2 opacity-80" />
                      <span className="font-medium text-sm">Production</span>
                      <span className="text-xs opacity-60 mt-1 text-left">Live environment</span>
                    </button>
                  </div>
                </div>
              </div>
              
              <div className="p-6 border-t border-slate-800 bg-slate-900/50 flex gap-3 justify-end">
                <Button variant="ghost" onClick={() => setIsCreateModalOpen(false)} className="rounded-full hover:bg-slate-800 text-slate-300">
                  Cancel
                </Button>
                <Button 
                  onClick={() => createProject.mutate()} 
                  disabled={!newProjectName.trim() || createProject.isPending}
                  className="rounded-full bg-sky-500 hover:bg-sky-400 text-slate-950"
                >
                  {createProject.isPending ? "Creating..." : "Create Project"}
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Created Project API Key Drawer/Modal */}
      <AnimatePresence>
        {createdApiKey && createdProject && (
          <div className="fixed inset-0 z-50 flex justify-end">
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm"
              onClick={() => {
                setCreatedApiKey(null);
                setCreatedProject(null);
              }}
            />
            <motion.div 
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="relative w-full max-w-md bg-slate-900 border-l border-slate-800 shadow-2xl h-full flex flex-col"
            >
              <div className="flex flex-col h-full justify-center p-8">
                <div className="w-16 h-16 rounded-full bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center mx-auto mb-6">
                  <Check className="w-8 h-8 text-emerald-400" />
                </div>
                <h2 className="text-2xl font-bold text-white mb-1 text-center">Project Created</h2>
                <p className="text-sky-400 text-sm mb-4 text-center font-medium">&quot;{createdProject.name}&quot;</p>
                <p className="text-slate-400 text-xs mb-8 text-center leading-relaxed">
                  A default API key has been auto-generated for this project. Please copy it now. For your safety, you won&apos;t be able to inspect this key again.
                </p>
                
                <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 mb-8 flex flex-col gap-4">
                  <code className="text-sky-300 font-mono text-sm break-all text-center">{createdApiKey}</code>
                  <Button 
                    variant="outline" 
                    onClick={handleCopyProjectKey}
                    className="w-full bg-slate-900 border-slate-800 text-slate-300 hover:text-white"
                  >
                    {copiedProjectKey ? (
                      <><Check className="w-4 h-4 mr-2 text-emerald-400" /> Copied!</>
                    ) : (
                      <><Copy className="w-4 h-4 mr-2" /> Copy to clipboard</>
                    )}
                  </Button>
                </div>

                <Button 
                  onClick={() => {
                    setCreatedApiKey(null);
                    setCreatedProject(null);
                  }} 
                  className="w-full rounded-full bg-slate-100 text-slate-900 hover:bg-slate-200 py-6"
                >
                  I have saved this key safely
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
