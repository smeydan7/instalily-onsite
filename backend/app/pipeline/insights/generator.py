"""Generate account-planning insights from a scored candidate.

Rule-based stub. Real generation may add an LLM step to phrase recommendations and
talking points for reps — keep the output shape (list of insight dicts) stable so the
orchestrator and persistence layer are unaffected.
"""
from __future__ import annotations

from app.models.enums import InsightType
from app.pipeline.types import AccountCandidate


def generate_insights(candidate: AccountCandidate) -> list[dict]:
    insights: list[dict] = []

    if candidate.score >= 70:
        insights.append(
            {
                "type": InsightType.OPPORTUNITY.value,
                "title": "High-fit account",
                "body": (
                    f"{candidate.name} scores {candidate.score:.0f}/100 on fit. "
                    "Prioritize for outreach this planning cycle."
                ),
                "confidence": 0.6,
                "evidence": {"score": candidate.score, "provenance": candidate.provenance},
            }
        )

    if not candidate.contacts:
        insights.append(
            {
                "type": InsightType.ENGAGEMENT.value,
                "title": "No decision maker identified",
                "body": "Enrich contacts before outreach — no decision maker on file yet.",
                "confidence": 0.9,
                "evidence": {},
            }
        )

    return insights
