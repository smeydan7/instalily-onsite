"""Placeholder source adapter.

Demonstrates the BaseSource contract with fake data so the pipeline runs end-to-end
before a real public data source is chosen. Replace with a concrete adapter (permits,
business registries, etc.) once the source is known.
"""
from __future__ import annotations

from collections.abc import Iterable

from app.pipeline.sources.base import BaseSource
from app.pipeline.types import AccountCandidate, RawRecord

_FAKE = [
    {
        "id": "demo-1",
        "company": "Summit Roofing Contractors",
        "website": "summitroofing.example",
        "state": "TX",
        "employees": 45,
    },
    {
        "id": "demo-2",
        "company": "Cornerstone Builders LLC",
        "website": "cornerstonebuild.example",
        "state": "CO",
        "employees": 120,
    },
]


class ExampleSource(BaseSource):
    key = "example_source"
    name = "Example (demo) source"

    def fetch(self) -> Iterable[RawRecord]:
        for row in _FAKE:
            yield RawRecord(source_key=self.key, external_id=row["id"], payload=row)

    def normalize(self, record: RawRecord) -> AccountCandidate | None:
        p = record.payload
        return AccountCandidate(
            name=p["company"],
            domain=p.get("website"),
            industry="roofing",
            state=p.get("state"),
            employee_count=p.get("employees"),
            attributes={"raw": p},
            provenance={record.source_key: [record.external_id]},
        )
