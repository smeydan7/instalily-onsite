"""Pipeline control endpoints — trigger and inspect ingestion runs."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.pipeline.orchestrator import run_source
from app.pipeline.sources import SOURCE_REGISTRY

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class RunRequest(BaseModel):
    source_key: str
    config: dict = {}


@router.get("/sources")
def list_sources() -> dict[str, list[dict[str, str]]]:
    return {
        "sources": [
            {"key": cls.key, "name": cls.name} for cls in SOURCE_REGISTRY.values()
        ]
    }


@router.post("/run", status_code=202)
def trigger_run(
    req: RunRequest, background: BackgroundTasks, db: Session = Depends(get_db)
) -> dict[str, str]:
    if req.source_key not in SOURCE_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown source: {req.source_key}")
    # Runs after the response returns. Swap for a real task queue at scale.
    background.add_task(run_source, db, req.source_key, config=req.config)
    return {"status": "accepted", "source_key": req.source_key}
