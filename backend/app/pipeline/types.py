"""Shared data-transfer shapes passed between pipeline stages.

These are plain dataclasses (not ORM models) so stages stay decoupled from
persistence. The orchestrator maps them onto ORM models at the end.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RawRecord:
    """One record as pulled from a source, before normalization."""

    source_key: str
    external_id: str
    payload: dict


@dataclass
class AccountCandidate:
    """A normalized prospect the pipeline is building up across stages."""

    name: str

    # Source identity — the upsert key (e.g. gaf_contractors / gaf_contractor_id).
    source_key: str | None = None
    external_id: str | None = None

    domain: str | None = None
    industry: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    employee_count: int | None = None
    description: str | None = None

    # Consumer review signals (GAF) used by scoring/insights.
    rating: float | None = None
    review_count: int | None = None
    distance_miles: float | None = None

    # ZIP whose search surfaced this candidate (for scoping the lead list).
    origin_zip: str | None = None
    # Position in the source's returned order (preserves GAF's recommended ranking).
    rank: int | None = None

    attributes: dict = field(default_factory=dict)

    # Populated by later stages.
    contacts: list[dict] = field(default_factory=list)
    score: float = 0.0
    insights: list[dict] = field(default_factory=list)

    # Provenance: source_key -> external_id(s) that fed this candidate.
    provenance: dict = field(default_factory=dict)
