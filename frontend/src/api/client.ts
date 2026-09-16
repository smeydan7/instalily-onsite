// Minimal typed API client. Swap fetch for a richer layer if needed.
import type {
  Account,
  IngestionRun,
  Insight,
  Lead,
  LeadDetail,
  LeadFilters,
  LeadStatus,
  Page,
} from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const V1 = `${BASE}/api/v1`;

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${V1}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status} ${text}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function leadQuery(filters: LeadFilters, limit: number, offset: number): string {
  const p = new URLSearchParams();
  p.set("limit", String(limit));
  p.set("offset", String(offset));
  if (filters.status) p.set("status", filters.status);
  if (filters.min_score != null) p.set("min_score", String(filters.min_score));
  if (filters.min_rating != null) p.set("min_rating", String(filters.min_rating));
  if (filters.state) p.set("state", filters.state);
  if (filters.search) p.set("search", filters.search);
  return p.toString();
}

export const api = {
  listLeads: (filters: LeadFilters = {}, limit = 50, offset = 0) =>
    request<Page<Lead>>(`/leads?${leadQuery(filters, limit, offset)}`),

  getLead: (id: number) => request<LeadDetail>(`/leads/${id}`),

  updateLeadStatus: (id: number, status: LeadStatus) =>
    request<Lead>(`/leads/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),

  listAccounts: (limit = 50, offset = 0) =>
    request<Page<Account>>(`/accounts?limit=${limit}&offset=${offset}`),

  listInsights: (accountId?: number) =>
    request<Page<Insight>>(`/insights${accountId ? `?account_id=${accountId}` : ""}`),

  // Pipeline
  triggerIngest: (zips: string[], radius: number) =>
    request<{ status: string; source_key: string }>(`/pipeline/run`, {
      method: "POST",
      body: JSON.stringify({
        source_key: "gaf_contractors",
        config: { zips, radius },
      }),
    }),

  listRuns: () => request<IngestionRun[]>(`/pipeline/runs`),
};
