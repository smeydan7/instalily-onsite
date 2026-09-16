from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import LeadStatus
from app.schemas.common import ORMModel


class LeadBase(BaseModel):
    account_id: int
    contact_id: int | None = None
    title: str
    summary: str | None = None
    score: float = 0.0
    status: LeadStatus = LeadStatus.NEW


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    contact_id: int | None = None
    title: str | None = None
    summary: str | None = None
    score: float | None = None
    status: LeadStatus | None = None


class LeadRead(ORMModel, LeadBase):
    id: int
