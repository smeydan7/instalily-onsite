"""Insight generation orchestration.

LLM insights are generated **lazily, on first lead-detail view, and cached** — not for
every contractor at ingest time. This keeps ingest fast and cheap, and only spends an
LLM call on the leads a rep actually opens (which scales to thousands of reps).
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.integrations import openai_insights
from app.models.account import Account
from app.models.insight import Insight


def _already_llm(account: Account) -> bool:
    return any(
        (i.evidence or {}).get("generated_by") == "llm" for i in account.insights
    )


def ensure_llm_insights(db: Session, account: Account) -> bool:
    """Generate + cache LLM insights for an account if not already done.

    Returns True if insights were (re)generated. No-op (returns False) when the LLM is
    unconfigured, already generated, or the call fails — the existing rule-based
    insights stay in place as a fallback.
    """
    if _already_llm(account):
        return False

    new_insights = openai_insights.generate_llm_insights(account)
    if not new_insights:
        return False

    # Replace rule-based insights with the richer LLM ones.
    for old in list(account.insights):
        db.delete(old)
    for data in new_insights:
        db.add(Insight(account_id=account.id, **data))
    db.commit()
    return True
