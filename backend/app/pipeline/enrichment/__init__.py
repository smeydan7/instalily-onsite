"""Enrichment stage — augment candidates with derived/joined attributes.

Add enrichers as callables `(AccountCandidate) -> AccountCandidate` and list them in
`ENRICHERS`; the orchestrator applies them in order.
"""
from app.pipeline.enrichment.enrichers import ENRICHERS

__all__ = ["ENRICHERS"]
