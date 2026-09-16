"""Top-level pipeline flow: ingest -> enrich -> score -> generate -> persist.

`run_source` executes one full pass for a single source and writes results to the DB.
Kept synchronous and simple; move to a task queue (e.g. Celery/RQ/Arq) when volume or
scheduling demands it — the stage boundaries here make that swap local.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.account import Account
from app.models.contact import Contact
from app.models.data_source import IngestionRun
from app.models.enums import IngestionStatus
from app.models.insight import Insight
from app.models.lead import Lead
from app.pipeline.enrichment import ENRICHERS
from app.pipeline.insights import generate_insights
from app.pipeline.scoring import score_candidate
from app.pipeline.sources import SOURCE_REGISTRY
from app.pipeline.types import AccountCandidate

logger = get_logger(__name__)


def _process(candidate: AccountCandidate) -> AccountCandidate:
    """Run the pure stages (no I/O) on one candidate."""
    for enrich in ENRICHERS:
        candidate = enrich(candidate)
    candidate.score = score_candidate(candidate)
    candidate.insights = generate_insights(candidate)
    return candidate


def _persist(db: Session, candidate: AccountCandidate) -> None:
    """Map a finished candidate onto ORM rows.

    Naive create-only for the skeleton. Add upsert/dedup keyed on domain or an
    external id once a real source defines identity.
    """
    account = Account(
        name=candidate.name,
        domain=candidate.domain,
        industry=candidate.industry,
        city=candidate.city,
        state=candidate.state,
        country=candidate.country,
        employee_count=candidate.employee_count,
        description=candidate.description,
        attributes=candidate.attributes,
    )
    db.add(account)
    db.flush()  # assign account.id

    for c in candidate.contacts:
        db.add(Contact(account_id=account.id, **c))

    db.add(
        Lead(
            account_id=account.id,
            title=f"Lead: {candidate.name}",
            summary=candidate.description,
            score=candidate.score,
        )
    )

    for ins in candidate.insights:
        db.add(Insight(account_id=account.id, **ins))


def run_source(db: Session, source_key: str, *, config: dict | None = None) -> IngestionRun:
    """Run the full pipeline for one registered source and record the run."""
    source_cls = SOURCE_REGISTRY.get(source_key)
    if source_cls is None:
        raise ValueError(f"Unknown source: {source_key!r}")

    run = IngestionRun(
        source_id=config.get("source_id") if config else None,  # optional link
        status=IngestionStatus.RUNNING,
        started_at=datetime.now(timezone.utc),
    )

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
        db.commit()
        run.status = IngestionStatus.SUCCEEDED
    except Exception as exc:  # noqa: BLE001 — record and re-raise-free for now
        db.rollback()
        run.status = IngestionStatus.FAILED
        run.error = str(exc)
        logger.exception("pipeline run failed for source %s", source_key)
    finally:
        run.records_ingested = count
        run.finished_at = datetime.now(timezone.utc)

    return run
