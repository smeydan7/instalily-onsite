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
