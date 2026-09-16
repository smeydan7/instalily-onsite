import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { LeadFilters } from "../api/types";
import { ScorePill, Rating, StateBlock } from "../components/ui";

// New York (10013) is the default territory shown on open.
const DEFAULT_ZIP = "10013";

export default function LeadsPage() {
  // ZIP search is the primary driver: entering a ZIP ingests that territory and
  // scopes the list to it. Secondary filters refine within the current scope.
  const [zip, setZip] = useState(DEFAULT_ZIP);
  // GAF's site offers these fixed radii; we mirror them so results match exactly.
  const [radius, setRadius] = useState(25);
  const [activeZip, setActiveZip] = useState<string | undefined>(DEFAULT_ZIP);
  const [refining, setRefining] = useState<Omit<LeadFilters, "origin_zip">>({});
  const [searching, setSearching] = useState(false);
  const didSeed = useRef(false);
  const qc = useQueryClient();

  const filters: LeadFilters = { ...refining, origin_zip: activeZip };

  const { data, isLoading, error } = useQuery({
    queryKey: ["leads", filters],
    queryFn: () => api.listLeads(filters, 100),
    refetchInterval: searching ? 1500 : false,
  });

  const ingest = useMutation({
    mutationFn: (target: { zip: string; radius: number }) =>
      api.triggerIngest([target.zip], target.radius),
    onSuccess: (_res, target) => {
      setActiveZip(target.zip);
      setSearching(true);
      // Ingest runs in the background and commits as it goes. Force a refetch now
      // and keep polling briefly so the list reflects the new radius even when the
      // ZIP (and therefore the query key) is unchanged.
      qc.invalidateQueries({ queryKey: ["leads"] });
      setTimeout(() => setSearching(false), 8000);
    },
  });

  // On first open, if the default territory has no leads yet, seed it once.
  useEffect(() => {
    if (
      !didSeed.current &&
      activeZip === DEFAULT_ZIP &&
      data &&
      data.total === 0 &&
      !searching &&
      !ingest.isPending
    ) {
      didSeed.current = true;
      ingest.mutate({ zip: DEFAULT_ZIP, radius: 25 });
    }
  }, [data, activeZip, searching, ingest]);

  const runSearch = () => {
    if (/^\d{5}$/.test(zip)) ingest.mutate({ zip, radius });
  };

  const set = (patch: Partial<LeadFilters>) => setRefining((f) => ({ ...f, ...patch }));
  const clearScope = () => {
    setActiveZip(undefined);
    setSearching(false);
    qc.invalidateQueries({ queryKey: ["leads"] });
  };

  const leads = data?.items ?? [];

  return (
    <section>
      <div className="page-head">
        <div>
          <h1>Leads</h1>
          <p className="muted">
            Enter a ZIP to pull GAF-certified contractors near it, scored and ranked.
          </p>
        </div>
      </div>

      {/* Primary: ZIP search */}
      <div className="ingest">
        <div className="ingest-row">
          <label>
            ZIP code
            <input
              value={zip}
              onChange={(e) => setZip(e.target.value.replace(/\D/g, ""))}
              onKeyDown={(e) => e.key === "Enter" && runSearch()}
              maxLength={5}
              inputMode="numeric"
              placeholder="e.g. 30301"
            />
          </label>
          <label>
            Radius (mi)
            <select value={radius} onChange={(e) => setRadius(Number(e.target.value))}>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </label>
          <button onClick={runSearch} disabled={ingest.isPending || zip.length !== 5}>
            {ingest.isPending ? "Starting…" : "Search"}
          </button>
        </div>
        {ingest.isError && <p className="error small">{String(ingest.error)}</p>}
      </div>

      {/* Scope indicator */}
      {activeZip && (
        <p className="scope">
          Showing contractors near <strong>{activeZip}</strong>
          {searching && <span className="muted"> · searching…</span>}
          <button className="linkbtn" onClick={clearScope}>
            show all territories
          </button>
        </p>
      )}

      {/* Secondary: refine within scope */}
      <div className="filters">
        <input
          placeholder="Search company…"
          value={refining.search ?? ""}
          onChange={(e) => set({ search: e.target.value || undefined })}
        />
        <label className="range">
          Min score {refining.min_score ?? 0}
          <input
            type="range"
            min={0}
            max={100}
            value={refining.min_score ?? 0}
            onChange={(e) => set({ min_score: Number(e.target.value) || undefined })}
          />
        </label>
        <label className="range">
          Min number of ratings {refining.min_reviews ?? 0}
          <input
            type="range"
            min={0}
            max={300}
            step={10}
            value={refining.min_reviews ?? 0}
            onChange={(e) => set({ min_reviews: Number(e.target.value) || undefined })}
          />
        </label>
      </div>

      <p className="muted small">{data ? `${data.total} leads` : ""}</p>

      <StateBlock
        loading={isLoading}
        error={error}
        empty={leads.length === 0}
        emptyText={
          searching
            ? "Searching that ZIP…"
            : activeZip
              ? `No contractors found near ${activeZip}.`
              : "Enter a ZIP above to find contractors."
        }
      >
        <table className="grid">
          <thead>
            <tr>
              <th>#</th>
              <th>Score</th>
              <th>Company</th>
              <th>Rating</th>
              <th>Location</th>
            </tr>
          </thead>
          <tbody>
            {leads.map((l, i) => (
              <tr key={l.id}>
                <td className="muted">{i + 1}</td>
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
              </tr>
            ))}
          </tbody>
        </table>
      </StateBlock>
    </section>
  );
}
