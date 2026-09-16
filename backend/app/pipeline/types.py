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
    domain: str | None = None
    industry: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    employee_count: int | None = None
    description: str | None = None
    attributes: dict = field(default_factory=dict)

    # Populated by later stages.
    contacts: list[dict] = field(default_factory=list)
    score: float = 0.0
    insights: list[dict] = field(default_factory=list)

    # Provenance: source_key -> external_id(s) that fed this candidate.
    provenance: dict = field(default_factory=dict)
