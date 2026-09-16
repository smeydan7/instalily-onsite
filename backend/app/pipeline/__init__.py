"""Data pipeline: ingest -> enrich -> score -> generate insights.

Each stage is a small, replaceable unit so new public data sources and new scoring
or insight logic plug in without reworking the core. See `orchestrator.py` for the
top-level flow.
"""
