from __future__ import annotations

from pydantic import BaseModel

from app.models.enums import InsightType
from app.schemas.common import ORMModel


class InsightBase(BaseModel):
    account_id: int
    type: InsightType
    title: str
    body: str | None = None
    confidence: float = 0.0
    evidence: dict = {}


class InsightCreate(InsightBase):
    pass


class InsightRead(ORMModel, InsightBase):
    id: int
