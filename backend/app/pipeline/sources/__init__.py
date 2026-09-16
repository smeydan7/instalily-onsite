"""Source adapters — one per public data source.

Register a new source by subclassing `BaseSource` and adding it to `SOURCE_REGISTRY`.
"""
from app.pipeline.sources.base import BaseSource
from app.pipeline.sources.example_source import ExampleSource
from app.pipeline.sources.gaf_source import GafContractorSource

# key -> source class. The orchestrator instantiates from here.
SOURCE_REGISTRY: dict[str, type[BaseSource]] = {
    GafContractorSource.key: GafContractorSource,
    ExampleSource.key: ExampleSource,  # demo/fallback source
}

__all__ = ["BaseSource", "SOURCE_REGISTRY"]
