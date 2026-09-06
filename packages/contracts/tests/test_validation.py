import pytest
from rev_babel_contracts import ContractViolation
from rev_babel_contracts.validation import (
    MAX_SEGMENT_MS,
    validate_caption_stream,
    validate_segment_stream,
)


def test_gapless_in_order_stream_passes_through(make_segment):
    segments = [
        make_segment(seq=i, started_at_ms=i * 1_000, ended_at_ms=i * 1_000 + 500) for i in range(5)
    ]
    assert list(validate_segment_stream(segments)) == segments


def test_gap_in_seq_fails_loudly(make_segment):
    segments = [make_segment(seq=0), make_segment(seq=2)]
    with pytest.raises(ContractViolation):
        list(validate_segment_stream(segments))


def test_out_of_order_seq_fails_loudly(make_segment):
    segments = [make_segment(seq=1), make_segment(seq=0)]
    with pytest.raises(ContractViolation):
        list(validate_segment_stream(segments))


def test_repeated_seq_fails_loudly(make_segment):
    segments = [make_segment(seq=0), make_segment(seq=0)]
    with pytest.raises(ContractViolation):
        list(validate_segment_stream(segments))


def test_stream_can_start_at_a_nonzero_seq(make_segment):
    segments = [make_segment(seq=5), make_segment(seq=6)]
    assert list(validate_segment_stream(segments)) == segments


def test_segment_over_hard_cap_fails_loudly(make_segment):
    segment = make_segment(started_at_ms=0, ended_at_ms=MAX_SEGMENT_MS + 1)
    with pytest.raises(ContractViolation):
        list(validate_segment_stream([segment]))


def test_segment_at_exactly_the_hard_cap_passes(make_segment):
    segment = make_segment(started_at_ms=0, ended_at_ms=MAX_SEGMENT_MS)
    assert list(validate_segment_stream([segment])) == [segment]


def test_caption_streams_are_validated_independently_per_target_lang(make_caption):
    captions = [
        make_caption(seq=0, target_lang="en"),
        make_caption(seq=0, target_lang="fr"),
        make_caption(seq=1, target_lang="en"),
        make_caption(seq=1, target_lang="fr"),
    ]
    assert list(validate_caption_stream(captions)) == captions


def test_gap_in_one_target_lang_fails_loudly(make_caption):
    captions = [
        make_caption(seq=0, target_lang="en"),
        make_caption(seq=0, target_lang="fr"),
        make_caption(seq=2, target_lang="en"),
    ]
    with pytest.raises(ContractViolation):
        list(validate_caption_stream(captions))
