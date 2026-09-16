import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import type { LeadFilters, LeadStatus } from "../api/types";
import { LEAD_STATUSES } from "../api/types";
import { ScorePill, StatusBadge, Rating, StateBlock } from "../components/ui";
import IngestPanel from "../components/IngestPanel";

export default function LeadsPage() {
  const [filters, setFilters] = useState<LeadFilters>({});

  const { data, isLoading, error } = useQuery({
    queryKey: ["leads", filters],
    queryFn: () => api.listLeads(filters, 100),
  });

  const leads = data?.items ?? [];
  const set = (patch: Partial<LeadFilters>) => setFilters((f) => ({ ...f, ...patch }));

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Leads</h1>
          <p className="muted">
            GAF-certified contractors, scored and ranked. Highest-fit first.
          </p>
        </div>
      </div>

      <IngestPanel />

      <div className="filters">
        <input
          placeholder="Search company…"
          value={filters.search ?? ""}
          onChange={(e) => set({ search: e.target.value || undefined })}
        />
        <select
          value={filters.status ?? ""}
          onChange={(e) =>
            set({ status: (e.target.value || undefined) as LeadStatus | undefined })
          }
        >
          <option value="">All statuses</option>
          {LEAD_STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <input
          placeholder="State (e.g. CA)"
          maxLength={2}
          value={filters.state ?? ""}
          onChange={(e) => set({ state: e.target.value.toUpperCase() || undefined })}
        />
        <label className="range">
          Min score {filters.min_score ?? 0}
          <input
            type="range"
            min={0}
            max={100}
            value={filters.min_score ?? 0}
            onChange={(e) => set({ min_score: Number(e.target.value) || undefined })}
          />
        </label>
        <label className="range">
          Min rating {filters.min_rating ?? 0}
          <input
            type="range"
            min={0}
            max={5}
            step={0.5}
            value={filters.min_rating ?? 0}
            onChange={(e) => set({ min_rating: Number(e.target.value) || undefined })}
          />
        </label>
      </div>

      <p className="muted small">{data ? `${data.total} leads` : ""}</p>

      <StateBlock
        loading={isLoading}
        error={error}
        empty={leads.length === 0}
        emptyText="No leads yet. Pull a territory above to generate some."
      >
        <table className="grid">
          <thead>
            <tr>
              <th>Score</th>
              <th>Company</th>
              <th>Rating</th>
              <th>Location</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((l) => (
              <tr key={l.id}>
                <td>
                  <ScorePill score={l.score} />
                </td>
                <td>
                  <Link to={`/leads/${l.id}`} className="link">
                    {l.account?.name ?? l.title}
                  </Link>
                </td>
                <td>
                  <Rating rating={l.account?.rating} reviews={l.account?.review_count} />
                </td>
                <td>
                  {l.account?.city ?? "—"}
                  {l.account?.state ? `, ${l.account.state}` : ""}
                </td>
                <td>
                  <StatusBadge status={l.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </StateBlock>
    </section>
  );
}
