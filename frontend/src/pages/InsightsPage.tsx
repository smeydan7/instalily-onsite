import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export default function InsightsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["insights"],
    queryFn: () => api.listInsights(),
  });

  if (isLoading) return <p>Loading insights…</p>;
  if (error) return <p className="error">Failed to load insights. Is the API running?</p>;

  const insights = data?.items ?? [];

  return (
    <section>
      <h1>Insights</h1>
      <p className="muted">Generated recommendations for account planning.</p>
      <div className="cards">
        {insights.map((i) => (
          <article key={i.id} className="card">
            <span className={`tag tag-${i.type}`}>{i.type}</span>
            <h3>{i.title}</h3>
            {i.body && <p>{i.body}</p>}
            <span className="muted">confidence {(i.confidence * 100).toFixed(0)}%</span>
          </article>
        ))}
        {insights.length === 0 && <p className="muted">No insights yet.</p>}
      </div>
    </section>
  );
}
