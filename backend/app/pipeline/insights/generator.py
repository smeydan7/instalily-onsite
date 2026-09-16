"""Generate account-planning insights from a scored candidate.

Rule-based over GAF signals. A future version may add an LLM step to phrase
recommendations and rep talking points — keep the output shape (list of insight dicts)
stable so the orchestrator and persistence are unaffected.
"""
from __future__ import annotations

from app.models.enums import InsightType
from app.pipeline.types import AccountCandidate


def _evidence(candidate: AccountCandidate) -> dict:
    return {
        "rating": candidate.rating,
        "review_count": candidate.review_count,
        "distance_miles": candidate.distance_miles,
        "score": candidate.score,
        "provenance": candidate.provenance,
    }


def generate_insights(candidate: AccountCandidate) -> list[dict]:
    insights: list[dict] = []
    ev = _evidence(candidate)

    # High-fit: strong rating + real review volume.
    if (candidate.rating or 0) >= 4.5 and (candidate.review_count or 0) >= 25:
        insights.append(
            {
                "type": InsightType.OPPORTUNITY.value,
                "title": "High-fit, well-reviewed contractor",
                "body": (
                    f"{candidate.name} holds a {candidate.rating}★ rating across "
                    f"{candidate.review_count} reviews — an established, active contractor. "
                    "Prioritize for outreach this planning cycle."
                ),
                "confidence": 0.7,
                "evidence": ev,
            }
        )

    # Territory: close to a branch.
    if candidate.distance_miles is not None and candidate.distance_miles <= 10:
        insights.append(
            {
                "type": InsightType.ENGAGEMENT.value,
                "title": "In-territory — assign to nearest branch",
                "body": (
                    f"Only {candidate.distance_miles:.1f} miles out. Route to the local "
                    "branch rep for fast, in-person engagement."
                ),
                "confidence": 0.8,
                "evidence": ev,
            }
        )

    # Low signal: few or no reviews — verify before investing time.
    if (candidate.review_count or 0) < 5:
        insights.append(
            {
                "type": InsightType.RISK.value,
                "title": "Thin review signal",
                "body": (
                    "Few consumer reviews on file — confirm the contractor is active and "
                    "sized right before heavy outreach."
                ),
                "confidence": 0.5,
                "evidence": ev,
            }
        )

    # Always: a firmographic summary line for account planning.
    insights.append(
        {
            "type": InsightType.FIRMOGRAPHIC.value,
            "title": "Contractor profile",
            "body": (
                f"{candidate.name} — {candidate.city or '?'}, {candidate.state or '?'}. "
                f"Rating {candidate.rating if candidate.rating is not None else 'n/a'}, "
                f"{candidate.review_count or 0} reviews. "
                "Contact: company main line (no named decision maker from source yet)."
            ),
            "confidence": 0.9,
            "evidence": ev,
        }
    )

    return insights
