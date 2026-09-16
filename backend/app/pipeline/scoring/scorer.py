"""Lead scoring.

Placeholder heuristic: a transparent weighted sum over a few signals, clamped to
0..100. Swap for a model or a richer rule set later; keep the 0..100 contract so the
API and UI don't change.
"""
from __future__ import annotations

from app.pipeline.types import AccountCandidate

# signal -> weight (points).
_SIZE_BAND_POINTS = {"micro": 5, "small": 25, "mid": 40, "large": 30}


def score_candidate(candidate: AccountCandidate) -> float:
    score = 0.0

    band = candidate.attributes.get("size_band")
    score += _SIZE_BAND_POINTS.get(band, 0)

    if candidate.industry == "roofing":
        score += 30
    if candidate.domain:
        score += 10
    if candidate.contacts:
        score += 20

    return float(max(0.0, min(100.0, score)))
