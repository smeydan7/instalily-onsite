import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import AccountsPage from "./pages/AccountsPage";
import LeadsPage from "./pages/LeadsPage";
import InsightsPage from "./pages/InsightsPage";

const nav = [
  { to: "/leads", label: "Leads" },
  { to: "/accounts", label: "Accounts" },
  { to: "/insights", label: "Insights" },
];

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">Roofing Sales Intelligence</span>
        <nav>
          {nav.map((n) => (
            <NavLink key={n.to} to={n.to} className="navlink">
              {n.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/leads" replace />} />
          <Route path="/leads" element={<LeadsPage />} />
          <Route path="/accounts" element={<AccountsPage />} />
          <Route path="/insights" element={<InsightsPage />} />
        </Routes>
      </main>
    </div>
  );
}
