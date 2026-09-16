from __future__ import annotations

from pydantic import BaseModel

from app.schemas.account import AccountRead, AccountSummary
from app.schemas.common import ORMModel
from app.schemas.contact import ContactRead
from app.schemas.insight import InsightRead


class LeadBase(BaseModel):
    account_id: int
    contact_id: int | None = None
    title: str
    summary: str | None = None
    score: float = 0.0


class LeadCreate(LeadBase):
    pass


class LeadRead(ORMModel, LeadBase):
    id: int
    account: AccountSummary | None = None


class LeadDetail(ORMModel, LeadBase):
    """Full lead view for the detail page: lead + account + contacts + insights."""

    id: int
    account: AccountRead | None = None
    contacts: list[ContactRead] = []
    insights: list[InsightRead] = []
