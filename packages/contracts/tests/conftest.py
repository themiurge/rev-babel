import pytest
from rev_babel_contracts import Caption, Segment


@pytest.fixture
def make_segment():
    def _make(**overrides) -> Segment:
        fields = {
            "lesson_id": "lesson-1",
            "seq": 0,
            "started_at_ms": 0,
            "ended_at_ms": 2_000,
            "source_lang": "it",
            "text": "Buongiorno a tutte.",
        }
        fields.update(overrides)
        return Segment(**fields)

    return _make


@pytest.fixture
def make_caption():
    def _make(**overrides) -> Caption:
        fields = {
            "lesson_id": "lesson-1",
            "seq": 0,
            "source_lang": "it",
            "source_text": "Buongiorno a tutte.",
            "target_lang": "en",
            "text": "Good morning, everyone.",
            "engine": "echo",
            "latency_ms": 5,
            "degraded": False,
        }
        fields.update(overrides)
        return Caption(**fields)

    return _make
