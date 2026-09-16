"""Live GAF contractor search endpoint.

Thin HTTP wrapper over `app.integrations.gaf_coveo`. All the real work — offline
geocoding, Coveo query, auth — lives in that integration module and is shared with the
ingestion pipeline. Each contractor returned is a prospect *account* for the distributor.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.integrations import gaf_coveo

router = APIRouter(tags=["data-source"])


@router.get("/gaf-contractors")
async def fetch_contractors(
    zip_code: str = Query(
        settings.coveo_default_zip, description="5-digit US ZIP code"
    ),
    distance: int = Query(
        settings.coveo_default_radius_miles, description="Search radius in miles"
    ),
) -> dict[str, Any]:
    """Live GAF contractor search near a ZIP code.

    GET /api/v1/gaf-contractors?zip_code=90210&distance=25
    No headers, API keys, or body required from the client. Omitting `zip_code`
    defaults to the configured ZIP.
    """
    try:
        return await gaf_coveo.search_async(zip_code, distance)
    except gaf_coveo.InvalidZipError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except gaf_coveo.CoveoError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
