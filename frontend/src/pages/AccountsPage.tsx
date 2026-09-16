import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";

export default function AccountsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["accounts"],
    queryFn: () => api.listAccounts(),
  });

  if (isLoading) return <p>Loading accounts…</p>;
  if (error) return <p className="error">Failed to load accounts. Is the API running?</p>;

  const accounts = data?.items ?? [];

  return (
    <section>
      <h1>Accounts</h1>
      <p className="muted">Prospect companies in the pipeline.</p>
      <table className="grid">
        <thead>
          <tr>
            <th>Name</th>
            <th>State</th>
            <th>Employees</th>
          </tr>
        </thead>
        <tbody>
          {accounts.map((a) => (
            <tr key={a.id}>
              <td>{a.name}</td>
              <td>{a.state ?? "—"}</td>
              <td>{a.employee_count ?? "—"}</td>
            </tr>
          ))}
          {accounts.length === 0 && (
            <tr>
              <td colSpan={3} className="muted">
                No accounts yet.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}
