"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api } from "@/lib/api";

interface User {
  id: string; // The backend uses user_id, we can map it here or leave it as id
  email: string;
  name: string; // backend uses username
  avatar?: string;
}

export interface Workspace {
  workspace_id: string;
  name: string;
  slug: string;
  plan: string;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  workspaces: Workspace[];
  activeWorkspace: Workspace | null;
  setActiveWorkspace: (ws: Workspace) => void;
  login: (accessToken: string, refreshToken: string, user: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<Workspace | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Check session on mount
    const token = localStorage.getItem("aegis_access_token");
    const storedUser = localStorage.getItem("aegis_user");
    
    if (token && storedUser) {
      try {
        setUser(JSON.parse(storedUser));
      } catch (e) {
        console.error("Failed to parse user from local storage");
        localStorage.removeItem("aegis_access_token");
        localStorage.removeItem("aegis_refresh_token");
        localStorage.removeItem("aegis_user");
      }
    }
    
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (user) {
      api.get("/workspaces")
        .then(res => {
          setWorkspaces(res.data);
          if (res.data.length > 0) {
            setActiveWorkspace(res.data[0]);
          }
        })
        .catch(err => {
          console.error("Failed to fetch workspaces", err);
        });
    } else {
      setWorkspaces([]);
      setActiveWorkspace(null);
    }
  }, [user]);

  const login = (accessToken: string, refreshToken: string, user: User) => {
    localStorage.setItem("aegis_access_token", accessToken);
    localStorage.setItem("aegis_refresh_token", refreshToken);
    localStorage.setItem("aegis_user", JSON.stringify(user));
    setUser(user);
  };

  const logout = () => {
    localStorage.removeItem("aegis_access_token");
    localStorage.removeItem("aegis_refresh_token");
    localStorage.removeItem("aegis_user");
    setUser(null);
    setWorkspaces([]);
    setActiveWorkspace(null);
    router.push("/login");
  };

  // Protected route logic
  useEffect(() => {
    if (!isLoading) {
      const isAuthRoute = pathname?.startsWith("/login") || pathname?.startsWith("/register") || pathname?.startsWith("/forgot-password");
      const isProtectedRoute = pathname?.startsWith("/dashboard");

      if (isProtectedRoute && !user) {
        router.push("/login");
      } else if (isAuthRoute && user) {
        router.push("/dashboard");
      }
    }
  }, [user, isLoading, pathname, router]);

  return (
    <AuthContext.Provider value={{ user, isLoading, workspaces, activeWorkspace, setActiveWorkspace, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
