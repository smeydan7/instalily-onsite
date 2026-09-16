"""GAF contractor directory as a pipeline source.

Reuses the shared Coveo integration to ingest certified contractors across the
distributor's territory ZIPs. Each contractor becomes an AccountCandidate; the
orchestrator upserts it on (source_key, external_id) so overlapping ZIP radii don't
create duplicates.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.integrations import gaf_coveo
from app.pipeline.sources.base import BaseSource
from app.pipeline.types import AccountCandidate, RawRecord

logger = get_logger(__name__)


def _first(value: Any) -> Any:
    """Coveo raw fields are sometimes single-element lists; unwrap them."""
    if isinstance(value, list):
        return value[0] if value else None
    return value


def _to_float(value: Any) -> float | None:
    value = _first(value)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    f = _to_float(value)
    return int(f) if f is not None else None


class GafContractorSource(BaseSource):
    key = "gaf_contractors"
    name = "GAF Contractor Directory"

    def fetch(self) -> Iterable[RawRecord]:
        zips = self.config.get("zips") or settings.gaf_territory_zips
        radius = int(self.config.get("radius") or settings.coveo_default_radius_miles)

        for zip_code in zips:
            try:
                data = gaf_coveo.search_sync(zip_code, radius)
            except gaf_coveo.InvalidZipError:
                logger.warning("skipping invalid territory ZIP: %s", zip_code)
                continue
            except gaf_coveo.CoveoError:
                logger.exception("Coveo fetch failed for ZIP %s", zip_code)
                continue

            for rank, result in enumerate(data.get("results", [])):
                raw = result.get("raw", {})
                external_id = _first(raw.get("gaf_contractor_id"))
                if not external_id:
                    continue
                yield RawRecord(
                    source_key=self.key,
                    external_id=str(external_id),
                    payload={"result": result, "origin_zip": zip_code, "rank": rank},
                )

    def normalize(self, record: RawRecord) -> AccountCandidate | None:
        result = record.payload["result"]
        raw = result.get("raw", {})

        # The company name lives in the result title / gaf_navigation_title;
        # gaf_contractor_dba is frequently null in this index.
        name = (
            result.get("title")
            or _first(raw.get("gaf_navigation_title"))
            or _first(raw.get("gaf_contractor_dba"))
        )
        if not name:
            return None

        phone = _first(raw.get("gaf_phone"))
        uri = result.get("uri") or _first(raw.get("uri"))
        rating = _to_float(raw.get("gaf_rating"))
        review_count = _to_int(raw.get("gaf_number_of_reviews"))
        distance = _to_float(raw.get("distanceinmiles"))

        contacts: list[dict] = []
        if phone:
            # Source gives no named decision maker — only the company line.
            # Named contacts are a future enrichment step (see PLAN.md 4.5).
            contacts.append(
                {
                    "full_name": str(name),
                    "title": "Main line",
                    "phone": str(phone),
                    "is_decision_maker": False,
                }
            )

        return AccountCandidate(
            name=str(name),
            source_key=self.key,
            external_id=record.external_id,
            industry="roofing",
            city=_first(raw.get("gaf_f_city")),
            state=_first(raw.get("gaf_f_state_code")),
            country="USA",
            rating=rating,
            review_count=review_count,
            distance_miles=distance,
            origin_zip=record.payload.get("origin_zip"),
            rank=record.payload.get("rank"),
            attributes={
                "contractor_type": _first(raw.get("gaf_contractor_type")),
                "postal_code": _first(raw.get("gaf_postal_code")),
                "latitude": _to_float(raw.get("gaf_latitude")),
                "longitude": _to_float(raw.get("gaf_longitude")),
                "distance_miles": distance,
                "gaf_profile_url": uri,
                "origin_zip": record.payload.get("origin_zip"),
            },
            contacts=contacts,
            provenance={self.key: [record.external_id], "gaf_profile_url": uri},
        )
