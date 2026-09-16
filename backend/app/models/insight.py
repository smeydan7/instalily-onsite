"""Insight — a generated recommendation/finding for account planning."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import InsightType

if TYPE_CHECKING:
    from app.models.account import Account


class Insight(Base, TimestampMixin):
    __tablename__ = "insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )

    type: Mapped[InsightType] = mapped_column(Enum(InsightType), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)  # human-readable recommendation

    # Model/heuristic confidence, 0..1.
    confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Provenance — which source(s)/records this was derived from, for traceability.
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)

    account: Mapped[Account] = relationship(back_populates="insights")
