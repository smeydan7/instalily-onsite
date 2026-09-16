from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.insight import Insight
from app.schemas.common import Page
from app.schemas.insight import InsightRead

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=Page[InsightRead])
def list_insights(
    account_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[InsightRead]:
    stmt = select(Insight)
    if account_id is not None:
        stmt = stmt.where(Insight.account_id == account_id)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = db.scalars(
        stmt.order_by(Insight.confidence.desc()).limit(limit).offset(offset)
    ).all()
    return Page(items=list(items), total=total, limit=limit, offset=offset)
