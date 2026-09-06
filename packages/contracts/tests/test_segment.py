import pytest
from pydantic import ValidationError


def test_valid_segment_round_trips(make_segment):
    segment = make_segment()
    assert segment.source_lang == "it"


@pytest.mark.parametrize("lang", ["it", "en", "mixed", "und"])
def test_accepts_all_documented_source_langs(make_segment, lang):
    assert make_segment(source_lang=lang).source_lang == lang


def test_rejects_unknown_source_lang(make_segment):
    with pytest.raises(ValidationError):
        make_segment(source_lang="fr")


def test_rejects_blank_text(make_segment):
    with pytest.raises(ValidationError):
        make_segment(text="   ")


def test_rejects_blank_lesson_id(make_segment):
    with pytest.raises(ValidationError):
        make_segment(lesson_id="")


def test_rejects_end_before_start(make_segment):
    with pytest.raises(ValidationError):
        make_segment(started_at_ms=1_000, ended_at_ms=1_000)


def test_rejects_negative_seq(make_segment):
    with pytest.raises(ValidationError):
        make_segment(seq=-1)
