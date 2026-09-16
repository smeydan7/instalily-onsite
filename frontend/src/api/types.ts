// Mirror of backend Pydantic schemas. Keep in sync with backend/app/schemas.

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Account {
  id: number;
  name: string;
  domain?: string | null;
  industry?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  employee_count?: number | null;
  description?: string | null;
  attributes: Record<string, unknown>;
}

export type LeadStatus =
  | "new"
  | "reviewing"
  | "qualified"
  | "engaged"
  | "won"
  | "lost"
  | "dismissed";

export interface Lead {
  id: number;
  account_id: number;
  contact_id?: number | null;
  title: string;
  summary?: string | null;
  score: number;
  status: LeadStatus;
}

export type InsightType = "opportunity" | "risk" | "engagement" | "firmographic";

export interface Insight {
  id: number;
  account_id: number;
  type: InsightType;
  title: string;
  body?: string | null;
  confidence: number;
  evidence: Record<string, unknown>;
}
