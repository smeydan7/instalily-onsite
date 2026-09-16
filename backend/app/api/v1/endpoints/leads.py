from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.common import Page
from app.schemas.lead import LeadCreate, LeadDetail, LeadRead
from app.services import insight_service, lead_service

router = APIRouter(prefix="/leads", tags=["leads"])


@router.get("", response_model=Page[LeadRead])
def list_leads(
    min_score: float | None = Query(None, ge=0, le=100),
    state: str | None = Query(None, description="2-letter state code"),
    min_reviews: int | None = Query(None, ge=0, description="Min number of ratings"),
    origin_zip: str | None = Query(None, description="Scope to a searched ZIP"),
    search: str | None = Query(None, description="Match account name"),
    sort: str = Query("rank", pattern="^(rank|score|name|rating)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Page[LeadRead]:
    items, total = lead_service.list_leads(
        db,
        min_score=min_score,
        state=state,
        min_reviews=min_reviews,
        origin_zip=origin_zip,
        search=search,
        sort=sort,
        order=order,
        limit=limit,
        offset=offset,
    )
    return Page(items=items, total=total, limit=limit, offset=offset)


@router.post("", response_model=LeadRead, status_code=status.HTTP_201_CREATED)
def create_lead(data: LeadCreate, db: Session = Depends(get_db)) -> LeadRead:
    return lead_service.create_lead(db, data)


@router.get("/{lead_id}", response_model=LeadDetail)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadDetail:
    lead = lead_service.get_lead_detail(db, lead_id)
    if lead is None:
        raise HTTPException(status_code=404, detail="Lead not found")
    # Generate rich LLM insights on first view (cached thereafter); falls back to the
    # rule-based insights if the LLM is unconfigured or the call fails.
    if lead.account and insight_service.ensure_llm_insights(db, lead.account):
        lead = lead_service.get_lead_detail(db, lead_id)
    account = lead.account
    return LeadDetail(
        id=lead.id,
        account_id=lead.account_id,
        contact_id=lead.contact_id,
        title=lead.title,
        summary=lead.summary,
        score=lead.score,
        account=account,
        contacts=account.contacts if account else [],
        insights=account.insights if account else [],
    )
