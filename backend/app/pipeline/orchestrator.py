"""Top-level pipeline flow: ingest -> enrich -> score -> generate -> persist.

`run_source` executes one full pass for a single source and records the run. Kept
synchronous; at scale this runs inside a task-queue worker (see PLAN.md §3), which is
why source I/O here is blocking rather than async.

Persistence is **upsert on (source_key, external_id)** so repeated runs (e.g. overlapping
ZIP radii) update contractors in place instead of duplicating them. A rep's lead status
is preserved across re-ingests; derived insights are regenerated each run.
"""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.models.account import Account
from app.models.contact import Contact
from app.models.data_source import DataSource, IngestionRun
from app.models.enums import IngestionStatus
from app.models.insight import Insight
from app.models.lead import Lead
from app.pipeline.enrichment import ENRICHERS
from app.pipeline.insights import generate_insights
from app.pipeline.scoring import score_candidate
from app.pipeline.sources import SOURCE_REGISTRY
from app.pipeline.types import AccountCandidate

logger = get_logger(__name__)


def _now() -> datetime:
    return datetime.now(UTC)


def _process(candidate: AccountCandidate) -> AccountCandidate:
    """Run the pure stages (no I/O) on one candidate."""
    for enrich in ENRICHERS:
        candidate = enrich(candidate)
    candidate.score = score_candidate(candidate)
    candidate.insights = generate_insights(candidate)
    return candidate


def _get_or_create_source(db: Session, key: str, name: str) -> DataSource:
    ds = db.scalar(select(DataSource).where(DataSource.key == key))
    if ds is None:
        ds = DataSource(key=key, name=name)
        db.add(ds)
        db.flush()
    return ds


def _upsert_account(db: Session, candidate: AccountCandidate) -> Account:
    account: Account | None = None
    if candidate.source_key and candidate.external_id:
        account = db.scalar(
            select(Account).where(
                Account.source_key == candidate.source_key,
                Account.external_id == candidate.external_id,
            )
        )

    fields = dict(
        name=candidate.name,
        domain=candidate.domain,
        industry=candidate.industry,
        city=candidate.city,
        state=candidate.state,
        country=candidate.country,
        origin_zip=candidate.origin_zip,
        gaf_rank=candidate.rank,
        rating=candidate.rating,
        review_count=candidate.review_count,
        employee_count=candidate.employee_count,
        description=candidate.description,
        attributes=candidate.attributes,
    )

    if account is None:
        account = Account(
            source_key=candidate.source_key,
            external_id=candidate.external_id,
            **fields,
        )
        db.add(account)
        db.flush()
    else:
        for k, v in fields.items():
            setattr(account, k, v)
    return account


def _sync_contacts(db: Session, account: Account, candidate: AccountCandidate) -> None:
    existing_phones = {
        c.phone for c in db.scalars(
            select(Contact).where(Contact.account_id == account.id)
        )
    }
    for c in candidate.contacts:
        if c.get("phone") and c["phone"] in existing_phones:
            continue
        db.add(Contact(account_id=account.id, **c))


def _upsert_primary_lead(db: Session, account: Account, candidate: AccountCandidate) -> None:
    lead = db.scalar(select(Lead).where(Lead.account_id == account.id).limit(1))
    if lead is None:
        db.add(
            Lead(
                account_id=account.id,
                title=candidate.name,
                summary=candidate.description,
                score=candidate.score,
            )
        )
    else:
        lead.score = candidate.score
        lead.title = candidate.name


def _regenerate_insights(db: Session, account: Account, candidate: AccountCandidate) -> None:
    for old in db.scalars(select(Insight).where(Insight.account_id == account.id)):
        db.delete(old)
    for ins in candidate.insights:
        db.add(Insight(account_id=account.id, **ins))


def _persist(db: Session, candidate: AccountCandidate) -> None:
    account = _upsert_account(db, candidate)
    _sync_contacts(db, account, candidate)
    _upsert_primary_lead(db, account, candidate)
    _regenerate_insights(db, account, candidate)


def run_source(db: Session, source_key: str, *, config: dict | None = None) -> IngestionRun:
    """Run the full pipeline for one registered source and record the run."""
    source_cls = SOURCE_REGISTRY.get(source_key)
    if source_cls is None:
        raise ValueError(f"Unknown source: {source_key!r}")

    ds = _get_or_create_source(db, source_key, source_cls.name)
    run = IngestionRun(source_id=ds.id, status=IngestionStatus.RUNNING, started_at=_now())
    db.add(run)
    db.commit()
    db.refresh(run)

    source = source_cls(config=config)
    count = 0
    try:
        for record in source.fetch():
            candidate = source.normalize(record)
            if candidate is None:
                continue
            candidate = _process(candidate)
            _persist(db, candidate)
            count += 1
            db.commit()  # commit per record → idempotent, restart-safe
        run.status = IngestionStatus.SUCCEEDED
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        run.status = IngestionStatus.FAILED
        run.error = str(exc)
        logger.exception("pipeline run failed for source %s", source_key)
    finally:
        run.records_ingested = count
        run.finished_at = _now()
        db.add(run)
        db.commit()
        db.refresh(run)

    return run


def run_source_background(source_key: str, config: dict | None = None) -> None:
    """Entry point for background execution — owns its own DB session.

    The request-scoped session is closed once the HTTP response returns, so a background
    task must not reuse it. This opens (and closes) a dedicated session.
    """
    db = SessionLocal()
    try:
        run_source(db, source_key, config=config)
    finally:
        db.close()
