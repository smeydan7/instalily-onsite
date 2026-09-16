import { Navigate, Route, Routes } from "react-router-dom";
import LeadsPage from "./pages/LeadsPage";
import LeadDetailPage from "./pages/LeadDetailPage";

export default function App() {
  return (
    <div className="app">
      <header className="topbar">
        <span className="brand">InstaLILY Roofing Sales Intelligence</span>
      </header>
      <main className="content">
        <Routes>
          <Route path="/" element={<Navigate to="/leads" replace />} />
          <Route path="/leads" element={<LeadsPage />} />
          <Route path="/leads/:id" element={<LeadDetailPage />} />
          <Route path="*" element={<Navigate to="/leads" replace />} />
        </Routes>
      </main>
    </div>
  );
}
