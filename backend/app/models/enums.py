"""Shared enums for domain models."""
from __future__ import annotations

import enum


class InsightType(str, enum.Enum):
    OPPORTUNITY = "opportunity"       # e.g. a signal the account is expanding
    RISK = "risk"                     # e.g. churn / competitor signal
    ENGAGEMENT = "engagement"         # e.g. recommended outreach / talking point
    FIRMOGRAPHIC = "firmographic"     # e.g. company profile fact worth noting


class IngestionStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
