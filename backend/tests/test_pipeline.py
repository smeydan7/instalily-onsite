"""Pure-stage pipeline test — no DB needed."""
from app.pipeline.orchestrator import _process
from app.pipeline.sources.example_source import ExampleSource


def test_example_source_normalizes_and_scores() -> None:
    source = ExampleSource()
    records = list(source.fetch())
    assert records, "example source should yield records"

    candidate = source.normalize(records[0])
    assert candidate is not None

    processed = _process(candidate)
    assert 0.0 <= processed.score <= 100.0
    assert "activity_band" in processed.attributes
    assert processed.insights  # at least the firmographic summary
