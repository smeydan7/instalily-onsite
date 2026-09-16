"""Lead business logic."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.account import Account
from app.models.lead import Lead
from app.schemas.lead import LeadCreate


def list_leads(
    db: Session,
    *,
    min_score: float | None = None,
    state: str | None = None,
    min_reviews: int | None = None,
    origin_zip: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Lead], int]:
    # Join Account so we can order by GAF's recommended rank (matches the public site).
    stmt = select(Lead).join(Account)
    if min_score is not None:
        stmt = stmt.where(Lead.score >= min_score)
    if state:
        stmt = stmt.where(Account.state == state)
    if min_reviews is not None:
        stmt = stmt.where(Account.review_count >= min_reviews)
    if origin_zip:
        stmt = stmt.where(Account.origin_zip == origin_zip)
    if search:
        stmt = stmt.where(Account.name.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.options(selectinload(Lead.account))
        # GAF recommended order (nulls last), then a stable tiebreak.
        .order_by(Account.gaf_rank.asc().nulls_last(), Lead.id.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(rows), total


def get_lead(db: Session, lead_id: int) -> Lead | None:
    return db.get(Lead, lead_id)


def get_lead_detail(db: Session, lead_id: int) -> Lead | None:
    """Lead with account, account contacts, and account insights eager-loaded."""
    return db.scalar(
        select(Lead)
        .where(Lead.id == lead_id)
        .options(
            selectinload(Lead.account).selectinload(Account.contacts),
            selectinload(Lead.account).selectinload(Account.insights),
        )
    )


def create_lead(db: Session, data: LeadCreate) -> Lead:
    lead = Lead(**data.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
