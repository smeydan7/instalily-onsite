from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel


class ContactBase(BaseModel):
    account_id: int
    full_name: str
    title: str | None = None
    seniority: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    is_decision_maker: bool = False
    attributes: dict = {}


class ContactRead(ORMModel, ContactBase):
    id: int
