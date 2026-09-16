import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { ScorePill, Rating } from "../components/ui";

export default function LeadDetailPage() {
  const { id } = useParams();
  const leadId = Number(id);

  const { data: lead, isLoading, error } = useQuery({
    queryKey: ["lead", leadId],
    queryFn: () => api.getLead(leadId),
    enabled: Number.isFinite(leadId),
  });

  if (isLoading) return <p className="muted">Loading…</p>;
  if (error || !lead)
    return <p className="error">Failed to load lead. {String(error ?? "")}</p>;

  const a = lead.account;
  const attrs = (a?.attributes ?? {}) as Record<string, unknown>;

  return (
    <section className="detail">
      <Link to="/leads" className="link small">
        ← Back to leads
      </Link>

      <div className="detail-head">
        <div>
          <h1>{a?.name ?? lead.title}</h1>
          <p className="muted">
            {a?.city ?? "—"}
            {a?.state ? `, ${a.state}` : ""} · <Rating rating={a?.rating} reviews={a?.review_count} />
          </p>
        </div>
        <div className="detail-score">
          <span className="muted small">Lead score</span>
          <ScorePill score={lead.score} />
        </div>
      </div>

      <div className="detail-cols">
        <div>
          <h2>Why this lead</h2>
          <div className="cards">
            {lead.insights.map((i) => (
              <article key={i.id} className="card">
                <span className={`tag tag-${i.type}`}>{i.type}</span>
                <h3>{i.title}</h3>
                {i.body && <p>{i.body}</p>}
                <span className="muted small">
                  confidence {(i.confidence * 100).toFixed(0)}%
                </span>
              </article>
            ))}
            {lead.insights.length === 0 && <p className="muted">No insights.</p>}
          </div>
        </div>

        <aside>
          <h2>Contact</h2>
          {lead.contacts.length === 0 && (
            <p className="muted">No contact on file.</p>
          )}
          {lead.contacts.map((c) => (
            <div key={c.id} className="fact">
              <strong>{c.full_name}</strong>
              <div className="muted small">{c.title}</div>
              {c.phone && <div>{c.phone}</div>}
              {!c.is_decision_maker && (
                <div className="muted small">Company line — no named decision maker yet</div>
              )}
            </div>
          ))}

          <h2>Account facts</h2>
          <ul className="facts">
            <li>
              Certification: {String(attrs["contractor_type"] ?? "—")}
            </li>
            <li>
              Distance: {attrs["distance_miles"] != null
                ? `${Number(attrs["distance_miles"]).toFixed(1)} mi`
                : "—"}
            </li>
            <li>Activity: {String(attrs["activity_band"] ?? "—")}</li>
            <li>Reviews: {a?.review_count ?? "—"}</li>
            {typeof attrs["gaf_profile_url"] === "string" && (
              <li>
                <a href={attrs["gaf_profile_url"] as string} target="_blank" rel="noreferrer">
                  GAF profile ↗
                </a>
              </li>
            )}
          </ul>
        </aside>
      </div>
    </section>
  );
}
