"""Enricher functions. Each takes and returns an AccountCandidate.

Derive/augment fields before scoring. Real enrichers might later resolve named
decision-maker contacts (the current source gap) or join external firmographics.
"""
from __future__ import annotations

from collections.abc import Callable

from app.pipeline.types import AccountCandidate

Enricher = Callable[[AccountCandidate], AccountCandidate]


def activity_band(candidate: AccountCandidate) -> AccountCandidate:
    """Bucket review volume into a coarse activity band for quick scanning."""
    n = candidate.review_count
    band = None
    if n is not None:
        if n < 5:
            band = "low"
        elif n < 25:
            band = "moderate"
        elif n < 100:
            band = "high"
        else:
            band = "very_high"
    candidate.attributes["activity_band"] = band
    return candidate


# Applied in order by the orchestrator.
ENRICHERS: list[Enricher] = [
    activity_band,
]
