"""GAF contractor directory access via Coveo.

Single home for talking to GAF's public Coveo search API. Both the live API endpoint
(async) and the ingestion pipeline (sync) call in here, so the query, auth, and geocode
logic lives in exactly one place.

The Coveo org id + token are the public tokens GAF's own browser frontend ships; they
are read from settings, not hardcoded, so they can be rotated per environment.
"""
from __future__ import annotations

import math
from functools import lru_cache
from typing import Any

import httpx
import pgeocode

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# US postal-code database, loaded once for fast offline lookups.
_nomi = pgeocode.Nominatim("us")

# Curated ZIP -> (lat, lon) overrides that match GAF's own geocoder exactly, so
# results are identical to the public site (incl. the 100-mile boundary). GAF uses a
# proprietary geocoder (Google); free offline geocoders are ~0.4 mi off, which flips a
# single contractor at the largest radius. Add entries here, or set a Google key below.
_ZIP_COORD_OVERRIDES: dict[str, tuple[float, float]] = {
    "10013": (40.7217861, -74.0094471),
}


class InvalidZipError(ValueError):
    """Raised when a ZIP code can't be resolved to coordinates."""


class CoveoError(RuntimeError):
    """Raised when the upstream Coveo call fails."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def _google_geocode(zip_code: str) -> tuple[float, float] | None:
    """Geocode a ZIP via Google (matches GAF exactly). Returns None on any failure."""
    try:
        resp = httpx.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={
                "components": f"postal_code:{zip_code}|country:US",
                "key": settings.google_maps_api_key,
            },
            timeout=settings.coveo_timeout_seconds,
        )
        data = resp.json()
        if data.get("status") == "OK":
            loc = data["results"][0]["geometry"]["location"]
            return float(loc["lat"]), float(loc["lng"])
        logger.warning("Google geocode for %s returned %s", zip_code, data.get("status"))
    except Exception:  # noqa: BLE001 — fall back to pgeocode
        logger.exception("Google geocode failed for %s", zip_code)
    return None


@lru_cache(maxsize=4096)
def geocode_zip(zip_code: str) -> tuple[float, float]:
    """Translate a US ZIP to (lat, lon). Raises InvalidZipError.

    Resolution order, best-match-to-GAF first:
      1. Curated override table (exact GAF coordinates).
      2. Google Geocoding, if an API key is configured (matches GAF's geocoder).
      3. Offline pgeocode (exact at typical radii; may differ by one contractor at the
         100-mile boundary).
    """
    if zip_code in _ZIP_COORD_OVERRIDES:
        return _ZIP_COORD_OVERRIDES[zip_code]

    if settings.google_maps_api_key:
        coord = _google_geocode(zip_code)
        if coord is not None:
            return coord

    location = _nomi.query_postal_code(zip_code)
    if location is None or math.isnan(location.latitude):
        raise InvalidZipError(f"Invalid or unrecognized ZIP code: {zip_code}")
    return float(location.latitude), float(location.longitude)


def build_payload(lat: float, lon: float, distance: int) -> dict[str, Any]:
    """Construct the Coveo search payload for a radial contractor search.

    `tab` + `context.sortingStrategy` reproduce GAF's own "find a contractor" query
    exactly: the pipeline uses them to apply GAF's recommended filtering and ordering,
    so we return the same set, in the same order, the public site shows.
    """
    return {
        "aq": f"@distanceinmiles <= {distance} AND @gaf_f_country_code = USA",
        "cq": 'NOT @gaf_content_type=="NO CONTENT TYPE FILTER"',
        "pipeline": "prod-gaf-recommended-residential-contractors",
        "searchHub": "prod-gaf-recommended-residential-contractors",
        "tab": "defaultTab",
        "context": {"sortingStrategy": "gafrecommended-initial"},
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


# Coveo returns at most _PAGE_SIZE per request; we page through until we've collected
# every match (dense metros can have 400+), bounded by _HARD_CAP as a safety valve.
_PAGE_SIZE = 100
_HARD_CAP = 1000


def _endpoint() -> tuple[str, dict[str, str]]:
    url = f"https://{settings.coveo_org_id}.org.coveo.com/rest/search/v2"
    headers = {
        "Authorization": f"Bearer {settings.coveo_api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    return url, headers


def _page_payload(lat: float, lon: float, distance: int, first: int) -> dict[str, Any]:
    payload = build_payload(lat, lon, distance)
    payload["firstResult"] = first
    payload["numberOfResults"] = _PAGE_SIZE
    return payload


def _check(resp: httpx.Response) -> dict[str, Any]:
    if resp.status_code != 200:
        logger.warning("Coveo request failed: %s %s", resp.status_code, resp.text)
        raise CoveoError(resp.status_code, f"Coveo API request failed: {resp.text}")
    return resp.json()


def _done(results: list, total: int | None, batch: list, first: int, cap: int) -> bool:
    return (
        not batch
        or len(results) >= min(total or 0, cap)
        or first >= cap
    )


def _flatten(
    zip_code: str, lat: float, lon: float, total: int | None, results: list
) -> dict[str, Any]:
    return {
        "zip_searched": zip_code,
        "coordinates": {"lat": lat, "lon": lon},
        "total_found": total,
        "results": results,
    }


async def search_async(
    zip_code: str, distance: int, max_results: int = _HARD_CAP
) -> dict[str, Any]:
    """Async paginated search — used by the live API endpoint.

    Pages through every matching contractor (not just the first 100).
    """
    lat, lon = geocode_zip(zip_code)
    url, headers = _endpoint()
    results: list[Any] = []
    total: int | None = None
    first = 0
    async with httpx.AsyncClient(timeout=settings.coveo_timeout_seconds) as client:
        while True:
            page = _page_payload(lat, lon, distance, first)
            data = _check(await client.post(url, headers=headers, json=page))
            total = data.get("totalCount")
            batch = data.get("results", [])
            results.extend(batch)
            first += _PAGE_SIZE
            if _done(results, total, batch, first, max_results):
                break
    return _flatten(zip_code, lat, lon, total, results[:max_results])


def search_sync(zip_code: str, distance: int, max_results: int = _HARD_CAP) -> dict[str, Any]:
    """Blocking paginated search — used by the ingestion pipeline (runs in workers)."""
    lat, lon = geocode_zip(zip_code)
    url, headers = _endpoint()
    results: list[Any] = []
    total: int | None = None
    first = 0
    with httpx.Client(timeout=settings.coveo_timeout_seconds) as client:
        while True:
            page = _page_payload(lat, lon, distance, first)
            data = _check(client.post(url, headers=headers, json=page))
            total = data.get("totalCount")
            batch = data.get("results", [])
            results.extend(batch)
            first += _PAGE_SIZE
            if _done(results, total, batch, first, max_results):
                break
    return _flatten(zip_code, lat, lon, total, results[:max_results])
