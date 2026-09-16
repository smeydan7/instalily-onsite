import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";

// Pulls a new territory of contractors from GAF into the lead pipeline.
// This is how a rep (or ops) seeds/refreshes leads for a branch ZIP.
export default function IngestPanel() {
  const [zip, setZip] = useState("90210");
  const [radius, setRadius] = useState(25);
  const qc = useQueryClient();

  const mutation = useMutation({
    mutationFn: () => api.triggerIngest([zip], radius),
    onSuccess: () => {
      // Ingest runs in the background; give it a moment, then refresh.
      setTimeout(() => qc.invalidateQueries({ queryKey: ["leads"] }), 4000);
    },
  });

  return (
    <div className="ingest">
      <div className="ingest-row">
        <label>
          ZIP
          <input
            value={zip}
            onChange={(e) => setZip(e.target.value)}
            maxLength={5}
            inputMode="numeric"
          />
        </label>
        <label>
          Radius (mi)
          <input
            type="number"
            value={radius}
            min={1}
            max={100}
            onChange={(e) => setRadius(Number(e.target.value))}
          />
        </label>
        <button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          {mutation.isPending ? "Starting…" : "Pull contractors"}
        </button>
      </div>
      {mutation.isSuccess && (
        <p className="muted small">
          Ingestion started for {zip}. Leads refresh shortly — or reload in a few seconds.
        </p>
      )}
      {mutation.isError && <p className="error small">{String(mutation.error)}</p>}
    </div>
  );
}
