import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export default function LeadsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["leads"],
    queryFn: () => api.listLeads(),
  });

  if (isLoading) return <p>Loading leads…</p>;
  if (error) return <p className="error">Failed to load leads. Is the API running?</p>;

  const leads = data?.items ?? [];

  return (
    <section>
      <h1>Leads</h1>
      <p className="muted">Scored opportunities, highest fit first.</p>
      <table className="grid">
        <thead>
          <tr>
            <th>Score</th>
            <th>Title</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((l) => (
            <tr key={l.id}>
              <td>{l.score.toFixed(0)}</td>
              <td>{l.title}</td>
              <td>{l.status}</td>
            </tr>
          ))}
          {leads.length === 0 && (
            <tr>
              <td colSpan={3} className="muted">
                No leads yet. Run the pipeline to generate some.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
