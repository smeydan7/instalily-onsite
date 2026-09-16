// Minimal typed API client. Swap fetch for a richer layer if needed.
import type { Account, Insight, Lead, Page } from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const V1 = `${BASE}/api/v1`;

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${V1}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listAccounts: (limit = 50, offset = 0) =>
    get<Page<Account>>(`/accounts?limit=${limit}&offset=${offset}`),
  listLeads: (limit = 50, offset = 0) =>
    get<Page<Lead>>(`/leads?limit=${limit}&offset=${offset}`),
  listInsights: (accountId?: number) =>
    get<Page<Insight>>(`/insights${accountId ? `?account_id=${accountId}` : ""}`),
};
