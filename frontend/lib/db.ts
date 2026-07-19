import { randomUUID } from "crypto";

export interface Project {
  id: string;
  name: string;
  description: string;
  status: "active" | "inactive" | "error";
  environment: "production" | "development" | "staging";
  createdAt: string;
  updatedAt: string;
  requestCount: number;
}

export interface ApiKey {
  id: string;
  projectId: string;
  name: string;
  key: string;
  maskedKey: string;
  createdAt: string;
  lastUsedAt: string | null;
  status: "active" | "revoked";
}

export interface ExecutionRequest {
  id: string;
  projectId: string;
  timestamp: string;
  status: "success" | "blocked" | "error";
  model: string;
  durationMs: number;
  tokensTotal: number;
  tokensPrompt: number;
  tokensCompletion: number;
  riskScore: string;
  governanceScore: number;
  summary: string;
}

export interface ExecutionDetail extends ExecutionRequest {
  prompt: string;
  response: string;
  layer1Analysis: {
    intent: string;
    entities: string[];
    sentiment: string;
    language: string;
    isSafe?: boolean;
    safetyReason?: string;
  };
  layer2Governance: {
    piiDetected: boolean;
    toxicContent: boolean;
    dataLossPrevention: string;
    policyViolations: string[];
    validators?: Array<{ name: string; status: string; reason?: string | null }>;
  };
  planner: {
    strategy: string;
    steps: string[];
    totalLlmCalls?: number;
    iterations?: number;
  };
  governanceScoreBreakdown?: Record<string, number>;
  toolCalls: {
    id: string;
    tool: string;
    input: string;
    output: string;
    durationMs: number;
  }[];
  timeline: {
    event: string;
    timestamp: string;
    durationMs: number;
  }[];
}

let projects: Project[] = [
  {
    id: "proj_1",
    name: "Customer Support Agent",
    description: "Production LLM router for Zendesk",
    status: "active",
    environment: "production",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
    updatedAt: new Date().toISOString(),
    requestCount: 1254300,
  },
  {
    id: "proj_2",
    name: "Internal Knowledge Base",
    description: "RAG pipeline for employee handbook",
    status: "active",
    environment: "development",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 5).toISOString(),
    updatedAt: new Date().toISOString(),
    requestCount: 450,
  },
];

let apiKeys: ApiKey[] = [
  {
    id: "key_1",
    projectId: "proj_1",
    name: "Production API Key",
    key: "aegis_live_1234567890abcdef1234567890abcdef",
    maskedKey: "aegis_live_••••••••••••••••••••••••cdef",
    createdAt: new Date(Date.now() - 1000 * 60 * 60 * 24 * 30).toISOString(),
    lastUsedAt: new Date().toISOString(),
    status: "active",
  }
];

let executions: ExecutionDetail[] = Array.from({ length: 50 }).map((_, i) => {
  const isBlocked = i % 15 === 0;
  const isError = i % 25 === 0;
  const status = (isBlocked ? "blocked" : isError ? "error" : "success") as "success" | "blocked" | "error";
  
  const models = ["gpt-4-turbo", "gpt-3.5-turbo", "claude-3-opus-20240229", "gemini-1.5-pro"];
  const model = models[i % models.length];

  return {
    id: `req_${randomUUID().substring(0, 12)}`,
    projectId: "proj_1",
    timestamp: new Date(Date.now() - Math.random() * 1000 * 60 * 60 * 24 * 7).toISOString(),
    status,
    model,
    durationMs: Math.floor(Math.random() * 5000) + 200,
    tokensTotal: Math.floor(Math.random() * 4000) + 100,
    tokensPrompt: Math.floor(Math.random() * 2000) + 50,
    tokensCompletion: Math.floor(Math.random() * 2000) + 50,
    riskScore: (isBlocked ? "high" : i % 5 === 0 ? "medium" : "low") as "low" | "medium" | "high",
    governanceScore: isBlocked ? 25 : Math.floor(Math.random() * 20) + 80,
    summary: isBlocked ? "Blocked due to PII leak" : "Customer inquiry about refund policy",
    prompt: "I bought a coffee machine last week but it arrived broken. Can I get a refund?",
    response: isBlocked ? "" : "I'm sorry to hear your coffee machine arrived broken. Yes, you can absolutely get a refund. Let me help you with that right now.",
    layer1Analysis: {
      intent: "Refund Request",
      entities: ["coffee machine", "last week"],
      sentiment: "Negative",
      language: "en-US",
    },
    layer2Governance: {
      piiDetected: isBlocked,
      toxicContent: false,
      dataLossPrevention: isBlocked ? "Triggered (Credit Card number)" : "Pass",
      policyViolations: isBlocked ? ["PII Sharing"] : [],
    },
    planner: {
      strategy: "Handle customer refund request according to standard policy.",
      steps: ["Acknowledge issue", "Confirm refund eligibility", "Provide next steps"],
    },
    toolCalls: [
      {
        id: "call_1",
        tool: "lookupOrder",
        input: '{"orderId": "ORD-123"}',
        output: '{"status": "delivered", "date": "2023-10-25"}',
        durationMs: 350,
      }
    ],
    timeline: [
      { event: "Request Received", timestamp: new Date().toISOString(), durationMs: 0 },
      { event: "Layer 1 Analysis", timestamp: new Date().toISOString(), durationMs: 120 },
      { event: "Layer 2 Governance", timestamp: new Date().toISOString(), durationMs: 250 },
      { event: "Planner", timestamp: new Date().toISOString(), durationMs: 400 },
      { event: "Tool Call: lookupOrder", timestamp: new Date().toISOString(), durationMs: 350 },
      { event: "Model Generation", timestamp: new Date().toISOString(), durationMs: 1200 },
      { event: "Response Sent", timestamp: new Date().toISOString(), durationMs: 15 },
    ]
  };
}).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

export const db = {
  projects: {
    findMany: async () => [...projects],
    findById: async (id: string) => projects.find((p) => p.id === id),
    create: async (data: Partial<Project>) => {
      const newProj: Project = {
        id: `proj_${randomUUID().substring(0, 8)}`,
        name: data.name || "Untitled",
        description: data.description || "",
        status: "active",
        environment: data.environment || "development",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        requestCount: 0,
      };
      projects.push(newProj);
      return newProj;
    },
    delete: async (id: string) => {
      projects = projects.filter((p) => p.id !== id);
    },
  },
  apiKeys: {
    findManyByProjectId: async (projectId: string) => apiKeys.filter((k) => k.projectId === projectId),
    create: async (projectId: string, name: string) => {
      const rawKey = `sk_${randomUUID().replace(/-/g, "")}`;
      const newKey: ApiKey = {
        id: `key_${randomUUID().substring(0, 8)}`,
        projectId,
        name,
        key: rawKey,
        maskedKey: `sk_••••••••••••••••••••••••${rawKey.slice(-4)}`,
        createdAt: new Date().toISOString(),
        lastUsedAt: null,
        status: "active",
      };
      apiKeys.push(newKey);
      return newKey; // returns full key only once
    },
    update: async (id: string, data: Partial<ApiKey>) => {
      const idx = apiKeys.findIndex((k) => k.id === id);
      if (idx !== -1) {
        apiKeys[idx] = { ...apiKeys[idx], ...data };
        return apiKeys[idx];
      }
      return null;
    },
    delete: async (id: string) => {
      apiKeys = apiKeys.filter((k) => k.id !== id);
    }
  },
  executions: {
    findMany: async (options?: { limit?: number; offset?: number; status?: string; search?: string }) => {
      let filtered = [...executions];
      if (options?.status) {
        filtered = filtered.filter(e => e.status === options.status);
      }
      if (options?.search) {
        const lowerSearch = options.search.toLowerCase();
        filtered = filtered.filter(e => e.summary.toLowerCase().includes(lowerSearch) || e.id.toLowerCase().includes(lowerSearch));
      }
      const total = filtered.length;
      if (options?.offset !== undefined && options?.limit !== undefined) {
        filtered = filtered.slice(options.offset, options.offset + options.limit);
      }
      return { data: filtered, total };
    },
    findById: async (id: string) => executions.find((e) => e.id === id)
  }
};
