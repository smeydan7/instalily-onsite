export function ScorePill({ score }: { score: number }) {
  const tier = score >= 70 ? "high" : score >= 40 ? "mid" : "low";
  return <span className={`score score-${tier}`}>{score.toFixed(0)}</span>;
}

export function Rating({
  rating,
  reviews,
}: {
  rating?: number | null;
  reviews?: number | null;
}) {
  if (rating == null) return <span className="muted">—</span>;
  return (
    <span className="rating">
      <span className="star">★</span> {rating.toFixed(1)}
      {reviews != null && <span className="muted"> ({reviews})</span>}
    </span>
  );
}

export function StateBlock({
  loading,
  error,
  empty,
  emptyText,
  children,
}: {
  loading: boolean;
  error: unknown;
  empty: boolean;
  emptyText: string;
  children: React.ReactNode;
}) {
  if (loading) return <p className="muted">Loading…</p>;
  if (error)
    return <p className="error">Failed to load. Is the API running? {String(error)}</p>;
  if (empty) return <p className="muted">{emptyText}</p>;
  return <>{children}</>;
}
