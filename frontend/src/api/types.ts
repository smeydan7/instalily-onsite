// Mirror of backend Pydantic schemas. Keep in sync with backend/app/schemas.

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Account {
  id: number;
  source_key?: string | null;
  external_id?: string | null;
  name: string;
  domain?: string | null;
  industry?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  rating?: number | null;
  review_count?: number | null;
  employee_count?: number | null;
  description?: string | null;
  attributes: Record<string, unknown>;
}

export interface AccountSummary {
  id: number;
  name: string;
  city?: string | null;
  state?: string | null;
  rating?: number | null;
  review_count?: number | null;
}

export type LeadStatus =
  | "new"
  | "reviewing"
  | "qualified"
  | "engaged"
  | "won"
  | "lost"
  | "dismissed";

export const LEAD_STATUSES: LeadStatus[] = [
  "new",
  "reviewing",
  "qualified",
  "engaged",
  "won",
  "lost",
  "dismissed",
];

export interface Lead {
  id: number;
  account_id: number;
  contact_id?: number | null;
  title: string;
  summary?: string | null;
  score: number;
  status: LeadStatus;
  account?: AccountSummary | null;
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

export interface Contact {
  id: number;
  account_id: number;
  full_name: string;
  title?: string | null;
  seniority?: string | null;
  email?: string | null;
  phone?: string | null;
  linkedin_url?: string | null;
  is_decision_maker: boolean;
}

export interface LeadDetail extends Lead {
  account?: Account | null;
  contacts: Contact[];
  insights: Insight[];
}

export interface IngestionRun {
  id: number;
  source_id: number;
  status: "pending" | "running" | "succeeded" | "failed";
  records_ingested: number;
  error?: string | null;
}

export interface LeadFilters {
  status?: LeadStatus;
  min_score?: number;
  min_rating?: number;
  state?: string;
  search?: string;
}
