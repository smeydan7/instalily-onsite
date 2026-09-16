"""Account — a prospect company the roofing distributor may sell to."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.contact import Contact
    from app.models.insight import Insight
    from app.models.lead import Lead


class Account(Base, TimestampMixin):
    __tablename__ = "accounts"
    # Source identity — dedup key for upserts across ingestion runs.
    # For GAF, (source_key, external_id) = ("gaf_contractors", gaf_contractor_id).
    __table_args__ = (
        UniqueConstraint("source_key", "external_id", name="uq_account_source_identity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    source_key: Mapped[str | None] = mapped_column(String(120), index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    domain: Mapped[str | None] = mapped_column(String(255), index=True)
    industry: Mapped[str | None] = mapped_column(String(120))

    # Location — coarse for now; refine once a source dictates shape.
    city: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(64), index=True)
    country: Mapped[str | None] = mapped_column(String(64))

    # ZIP whose search surfaced this contractor (last-write-wins across searches).
    # Lets the UI scope the lead list to the ZIP a rep just entered.
    origin_zip: Mapped[str | None] = mapped_column(String(10), index=True)

    # Position in GAF's recommended ordering for its origin_zip search (0-based).
    # We preserve GAF's order so the list matches the public site exactly.
    gaf_rank: Mapped[int | None] = mapped_column(Integer, index=True)

    # Consumer review metrics (GAF signals) — indexed for sort/filter.
    rating: Mapped[float | None] = mapped_column(Float, index=True)
    review_count: Mapped[int | None] = mapped_column(Integer, index=True)

    employee_count: Mapped[int | None] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(Text)

    # Firmographics / raw source attributes that don't yet have columns.
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)

    contacts: Mapped[list[Contact]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    leads: Mapped[list[Lead]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    insights: Mapped[list[Insight]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
