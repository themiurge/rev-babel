import pytest
from pydantic import ValidationError


def test_valid_caption_round_trips(make_caption):
    caption = make_caption()
    assert caption.target_lang == "en"


def test_degraded_caption_must_carry_source_text(make_caption):
    caption = make_caption(degraded=True, text="Buongiorno a tutte.")
    assert caption.text == caption.source_text


def test_degraded_caption_with_translated_text_is_rejected(make_caption):
    with pytest.raises(ValidationError):
        make_caption(degraded=True, text="Good morning, everyone.")


def test_rejects_blank_engine(make_caption):
    with pytest.raises(ValidationError):
        make_caption(engine="")


def test_rejects_negative_latency(make_caption):
    with pytest.raises(ValidationError):
        make_caption(latency_ms=-1)
