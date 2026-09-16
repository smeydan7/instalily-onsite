"""Pipeline control endpoints — trigger and inspect ingestion runs."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.data_source import IngestionRun
from app.models.enums import IngestionStatus
from app.pipeline.orchestrator import run_source_background
from app.pipeline.sources import SOURCE_REGISTRY
from app.schemas.common import ORMModel

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class RunRequest(BaseModel):
    source_key: str = "gaf_contractors"
    # Optional per-run overrides, e.g. {"zips": ["90210"], "radius": 25}.
    config: dict = {}


class IngestionRunRead(ORMModel):
    id: int
    source_id: int
    status: IngestionStatus
    records_ingested: int
    error: str | None = None


@router.get("/sources")
def list_sources() -> dict[str, list[dict[str, str]]]:
    return {
        "sources": [
            {"key": cls.key, "name": cls.name} for cls in SOURCE_REGISTRY.values()
        ]
    }


@router.post("/run", status_code=202)
def trigger_run(req: RunRequest, background: BackgroundTasks) -> dict[str, str]:
    if req.source_key not in SOURCE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown source: {req.source_key}")
    # Runs after the response returns, in its own DB session. Swap BackgroundTasks for a
    # real task queue (Celery/RQ/Arq) at scale — the orchestrator entry point is ready.
    background.add_task(run_source_background, req.source_key, req.config)
    return {"status": "accepted", "source_key": req.source_key}


@router.get("/runs", response_model=list[IngestionRunRead])
def list_runs(
    limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)
) -> list[IngestionRun]:
    return list(
        db.scalars(select(IngestionRun).order_by(IngestionRun.id.desc()).limit(limit))
    )
