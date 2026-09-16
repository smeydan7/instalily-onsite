"""Base class every public-data-source adapter implements."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from app.pipeline.types import AccountCandidate, RawRecord


class BaseSource(ABC):
    """A public data source adapter.

    Two responsibilities, kept separate so each can be tested in isolation:
      1. `fetch`  — pull raw records from the source (HTTP, file, dump, …).
      2. `normalize` — turn one raw record into an AccountCandidate.
    """

    #: Stable machine key. Must match a DataSource.key row and SOURCE_REGISTRY.
    key: str = "base"
    #: Human label.
    name: str = "Base source"

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}

    @abstractmethod
    def fetch(self) -> Iterable[RawRecord]:
        """Yield raw records from the source."""
        raise NotImplementedError

    @abstractmethod
    def normalize(self, record: RawRecord) -> AccountCandidate | None:
        """Map one raw record to a candidate, or None to skip it."""
        raise NotImplementedError
