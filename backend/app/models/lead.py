"""Lead — a scored, actionable opportunity tied to an account."""
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import LeadStatus

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.contact import Contact


class Lead(Base, TimestampMixin):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    # Primary contact to engage for this lead (optional).
    contact_id: Mapped[int | None] = mapped_column(
        ForeignKey("contacts.id", ondelete="SET NULL")
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text)

    # 0..100. Assigned by the scoring stage of the pipeline.
    score: Mapped[float] = mapped_column(Float, default=0.0, index=True)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, index=True
    )

    account: Mapped["Account"] = relationship(back_populates="leads")
    contact: Mapped["Contact | None"] = relationship()
