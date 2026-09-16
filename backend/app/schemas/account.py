from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AccountBase(BaseModel):
    name: str
    domain: str | None = None
    industry: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    rating: float | None = None
    review_count: int | None = None
    employee_count: int | None = None
    description: str | None = None
    attributes: dict = {}


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None
    industry: str | None = None
    city: str | None = None
    state: str | None = None
    country: str | None = None
    employee_count: int | None = None
    description: str | None = None
    attributes: dict | None = None


class AccountRead(ORMModel, AccountBase):
    id: int
    source_key: str | None = None
    external_id: str | None = None


class AccountSummary(ORMModel):
    """Compact account view embedded in a lead row."""

    id: int
    name: str
    city: str | None = None
    state: str | None = None
    rating: float | None = None
    review_count: int | None = None
