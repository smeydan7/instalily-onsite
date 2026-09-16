"""GAF contractor data source — live search endpoint.

Interfaces directly with Coveo, the enterprise search engine behind GAF's public
"find a certified contractor" frontend, instead of scraping HTML. Flow:

  1. Translate a US ZIP code to lat/lon offline with pgeocode (no external geocoder).
  2. Build a Coveo v2 search payload mimicking a browser request, with
     numberOfResults=100 to bypass the frontend's 10-item pagination.
  3. POST it to Coveo using the public authorization token from GAF's frontend.
  4. Return a flattened JSON object of contractor records.

Each contractor is a prospect *account* for the distributor. This module is the live
passthrough the UI calls directly; the pipeline reuses the same fetch logic to
pre-generate and persist leads (see PLAN.md / pipeline/sources).
"""
from __future__ import annotations

import math

import httpx
import pgeocode
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings
from app.core.logging import get_logger

router = APIRouter(tags=["data-source"])
logger = get_logger(__name__)

# US postal-code database, loaded once into memory for fast offline lookups.
_nomi = pgeocode.Nominatim("us")


def build_payload(lat: float, lon: float, distance: int) -> dict:
    """Construct the Coveo search payload for a radial contractor search."""
    return {
        "aq": f"@distanceinmiles <= {distance} AND @gaf_f_country_code = USA",
        "cq": 'NOT @gaf_content_type=="NO CONTENT TYPE FILTER"',
        "pipeline": "prod-gaf-recommended-residential-contractors",
        "searchHub": "prod-gaf-recommended-residential-contractors",
        "firstResult": 0,
        "numberOfResults": 100,  # bypasses the frontend's 10-item pagination
        "sortCriteria": "relevancy",
        "fieldsToInclude": [
            "gaf_contractor_id", "gaf_contractor_type", "gaf_contractor_dba",
            "gaf_navigation_title", "gaf_rating", "gaf_number_of_reviews",
            "gaf_f_city", "gaf_f_state_code", "gaf_phone", "uri",
            "gaf_latitude", "gaf_longitude", "distanceinmiles", "gaf_postal_code",
        ],
        "queryFunctions": [
            {
                "fieldName": "@distanceinmiles",
                "function": (
                    f"dist(@gaf_latitude, @gaf_longitude, {lat}, {lon})*0.000621371"
                ),
            }
        ],
    }


async def search_contractors(zip_code: str, distance: int) -> dict:
    """Geocode the ZIP, query Coveo, and return the flattened response.

    Raises HTTPException on an invalid ZIP or a failed upstream call. Shared by the
    HTTP route below and (later) by the pipeline source adapter.
    """
    location = _nomi.query_postal_code(zip_code)
    if math.isnan(location.latitude):
        raise HTTPException(
            status_code=400, detail=f"Invalid or unrecognized ZIP code: {zip_code}"
        )
    lat = float(location.latitude)
    lon = float(location.longitude)

    coveo_url = f"https://{settings.coveo_org_id}.org.coveo.com/rest/search/v2"
    headers = {
        "Authorization": f"Bearer {settings.coveo_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = build_payload(lat, lon, distance)

    async with httpx.AsyncClient(timeout=settings.coveo_timeout_seconds) as client:
        response = await client.post(coveo_url, headers=headers, json=payload)

    if response.status_code != 200:
        logger.warning("Coveo request failed: %s %s", response.status_code, response.text)
        raise HTTPException(
            status_code=response.status_code,
            detail=f"Coveo API request failed: {response.text}",
        )

    data = response.json()
    return {
        "zip_searched": zip_code,
        "coordinates": {"lat": lat, "lon": lon},
        "total_found": data.get("totalCount"),
        "results": data.get("results", []),
    }


@router.get("/gaf-contractors")
async def fetch_contractors(
    zip_code: str = Query(
        settings.coveo_default_zip, description="5-digit US ZIP code"
    ),
    distance: int = Query(
        settings.coveo_default_radius_miles, description="Search radius in miles"
    ),
) -> dict:
    """Live GAF contractor search near a ZIP code.

    GET /api/gaf-contractors?zip_code=90210&distance=25
    No headers, API keys, or body required from the client. Omitting `zip_code`
    defaults to the configured ZIP.
    """
    return await search_contractors(zip_code, distance)
