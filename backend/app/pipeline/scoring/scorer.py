"""Lead scoring.

Transparent weighted sum over GAF signals, clamped to 0..100. Swap for a model later;
keep the 0..100 contract so the API and UI don't change.

Weights (max points):
  rating        40   consumer review rating, 0..5 → linear
  review_count  30   activity/volume proxy, saturates at 50 reviews
  proximity     20   closer to a branch = easier to serve
  base          10   in-directory (GAF-certified) baseline
"""
from __future__ import annotations

from app.pipeline.types import AccountCandidate

_REVIEW_SATURATION = 50  # reviews at/above this get full review points


def score_candidate(candidate: AccountCandidate) -> float:
    score = 10.0  # GAF-certified baseline

    if candidate.rating is not None:
        score += max(0.0, min(candidate.rating, 5.0)) / 5.0 * 40.0

    if candidate.review_count is not None:
        score += min(candidate.review_count, _REVIEW_SATURATION) / _REVIEW_SATURATION * 30.0

    d = candidate.distance_miles
    if d is not None:
        if d <= 10:
            score += 20.0
        elif d <= 25:
            score += 10.0
        elif d <= 50:
            score += 5.0

    return float(max(0.0, min(100.0, round(score, 1))))
