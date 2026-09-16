"""Enricher functions. Each takes and returns an AccountCandidate.

Stubs for now — real enrichers might resolve domains, join firmographic data, infer
company size bands, or match decision-maker contacts.
"""
from __future__ import annotations

from collections.abc import Callable

from app.pipeline.types import AccountCandidate

Enricher = Callable[[AccountCandidate], AccountCandidate]


def infer_size_band(candidate: AccountCandidate) -> AccountCandidate:
    """Bucket employee_count into a coarse size band for downstream scoring."""
    n = candidate.employee_count
    band = None
    if n is not None:
        if n < 10:
            band = "micro"
        elif n < 50:
            band = "small"
        elif n < 250:
            band = "mid"
        else:
            band = "large"
    candidate.attributes["size_band"] = band
    return candidate


# Applied in order by the orchestrator.
ENRICHERS: list[Enricher] = [
    infer_size_band,
]
