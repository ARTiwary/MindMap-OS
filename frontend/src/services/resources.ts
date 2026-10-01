import { api } from "@/services/api";
import type {
  DashboardStats,
  KnowledgeNode,
  NodeDetail,
  PaginatedNodes,
  Relationship,
  Tag,
  User,
} from "@/types";

// --- Auth ---
export const authApi = {
  register: (payload: { email: string; username: string; password: string; full_name?: string }) =>
    api.post<User>("/auth/register", payload),
  login: (payload: { email: string; password: string }) =>
    api.post<{ access_token: string; refresh_token: string }>("/auth/login", payload),
  me: () => api.get<User>("/auth/me"),
  logout: (refreshToken?: string) => api.post("/auth/logout", refreshToken ? { refresh_token: refreshToken } : {}),
};

// --- Nodes ---
export const nodesApi = {
  list: (params: Record<string, string | number | boolean | undefined>) =>
    api.get<PaginatedNodes>("/nodes", { params }),
  get: (id: string) => api.get<NodeDetail>(`/nodes/${id}`),
  create: (payload: Partial<KnowledgeNode> & { title: string; tag_ids?: string[] }) =>
    api.post<KnowledgeNode>("/nodes", payload),
  update: (id: string, payload: Partial<KnowledgeNode> & { tag_ids?: string[] }) =>
    api.patch<KnowledgeNode>(`/nodes/${id}`, payload),
  remove: (id: string) => api.delete(`/nodes/${id}`),
};

// --- Tags ---
export const tagsApi = {
  list: () => api.get<Tag[]>("/tags"),
  create: (payload: { name: string; color?: string }) => api.post<Tag>("/tags", payload),
  remove: (id: string) => api.delete(`/tags/${id}`),
};

// --- Relationships ---
export const relationshipsApi = {
  create: (payload: {
    source_node_id: string;
    target_node_id: string;
    relationship_type?: string;
    label?: string;
    strength?: number;
  }) => api.post<Relationship>("/relationships", payload),
  remove: (id: string) => api.delete(`/relationships/${id}`),
};

// --- Graph ---
export const graphApi = {
  get: () => api.get<{ nodes: any[]; edges: any[] }>("/graph"),
  savePositions: (positions: { node_id: string; x: number; y: number }[]) =>
    api.post("/graph/positions", { positions }),
};

// --- Search ---
export const searchApi = {
  search: (q: string, page = 1, limit = 20) =>
    api.get<PaginatedNodes>("/search", { params: { q, page, limit } }),
};

// --- Dashboard ---
export const dashboardApi = {
  get: () => api.get<DashboardStats>("/dashboard"),
};

// --- Analytics ---
export const analyticsApi = {
  mostConnected: () => api.get("/analytics/most-connected"),
  tagStats: () => api.get("/analytics/tags"),
  growth: (interval: "day" | "week" | "month" = "day") =>
    api.get("/analytics/growth", { params: { interval } }),
};

// --- Suggestions ---
export const suggestionsApi = {
  connections: () => api.get("/suggestions/connections"),
};

// --- Activity ---
export const activityApi = {
  list: (page = 1) => api.get("/activity", { params: { page } }),
};
