"""LLM-generated sales insights via OpenAI.

Given a contractor (our prospect account), produce a few concise, actionable insights
that help a roofing *distributor's* sales rep identify, understand, and engage the
decision maker — i.e. how to sell roofing materials/supplies to this contractor.

Kept dependency-light: a direct HTTPS call to OpenAI's chat completions API with JSON
output. Any failure returns [] so the caller falls back to rule-based insights.
"""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import httpx

from app.core.config import settings
from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.models.account import Account

logger = get_logger(__name__)

_ALLOWED_TYPES = {"opportunity", "risk", "engagement", "firmographic"}

_SYSTEM_PROMPT = (
    "You are a B2B sales intelligence assistant for a roofing distributor. The distributor "
    "sells roofing materials and supplies to roofing contractors. Given one GAF-certified "
    "contractor (a prospect), write concise, concrete insights that help a sales rep "
    "identify, understand, and engage the decision maker at that contractor. Focus on "
    "why-now signals, how to open the conversation, and product/volume angles. Be specific "
    "to the data provided; never invent facts (e.g. do not invent a person's name if none "
    "is given). Keep each insight to 1-2 sentences a rep can act on."
)


def _context(account: Account) -> dict[str, Any]:
    attrs = account.attributes or {}
    return {
        "company": account.name,
        "city": account.city,
        "state": account.state,
        "consumer_rating": account.rating,
        "number_of_ratings": account.review_count,
        "distance_miles_from_search": attrs.get("distance_miles"),
        "gaf_certification_type": attrs.get("contractor_type"),
        "review_activity_band": attrs.get("activity_band"),
    }


def _build_messages(account: Account) -> list[dict[str, str]]:
    ctx = json.dumps(_context(account), default=str)
    user = (
        f"Contractor data:\n{ctx}\n\n"
        "Return JSON of the form "
        '{"insights": [{"type": "...", "title": "...", "body": "..."}]}. '
        "Provide 3 insights. `type` must be one of: opportunity, risk, engagement, "
        "firmographic. `title` is a short label (max ~6 words). `body` is 1-2 actionable "
        "sentences for the rep."
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]


def generate_llm_insights(account: Account) -> list[dict]:
    """Call OpenAI and return a list of insight dicts, or [] on any failure."""
    if not settings.openai_api_key:
        return []

    payload = {
        "model": settings.openai_model,
        "messages": _build_messages(account),
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
    }
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }

    try:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=settings.openai_timeout_seconds,
        )
        if resp.status_code != 200:
            logger.warning("OpenAI request failed: %s %s", resp.status_code, resp.text[:300])
            return []
        content = resp.json()["choices"][0]["message"]["content"]
        raw = json.loads(content).get("insights", [])
    except Exception:  # noqa: BLE001 — any failure → fall back to rule-based
        logger.exception("OpenAI insight generation failed for %s", account.name)
        return []

    insights: list[dict] = []
    for item in raw:
        if not isinstance(item, dict) or not item.get("title") or not item.get("body"):
            continue
        itype = str(item.get("type", "engagement")).lower()
        if itype not in _ALLOWED_TYPES:
            itype = "engagement"
        insights.append(
            {
                "type": itype,
                "title": str(item["title"])[:255],
                "body": str(item["body"]),
                "confidence": 0.8,
                "evidence": {
                    "generated_by": "llm",
                    "model": settings.openai_model,
                    "signals": _context(account),
                },
            }
        )
    return insights
