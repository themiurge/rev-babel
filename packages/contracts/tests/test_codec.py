import pytest
from rev_babel_contracts import ContractViolation, Segment, dump_jsonl, parse_jsonl


def test_round_trip_preserves_every_field(make_segment):
    segments = [make_segment(seq=0), make_segment(seq=1, text="Apriamo il browser.")]

    lines = list(dump_jsonl(segments))
    parsed = list(parse_jsonl(lines, Segment))

    assert parsed == segments


def test_one_object_per_line(make_segment):
    lines = list(dump_jsonl([make_segment()]))
    assert len(lines) == 1
    assert lines[0].endswith("\n")
    assert lines[0].count("\n") == 1


def test_blank_lines_are_skipped(make_segment):
    lines = list(dump_jsonl([make_segment()]))
    parsed = list(parse_jsonl(["\n", *lines, "   \n"], Segment))
    assert len(parsed) == 1


def test_malformed_json_fails_loudly():
    with pytest.raises(ContractViolation):
        list(parse_jsonl(["{not json"], Segment))


def test_wrong_shape_fails_loudly(make_segment):
    line = make_segment().model_dump_json().replace('"seq":0', '"seq":"zero"')
    with pytest.raises(ContractViolation):
        list(parse_jsonl([line], Segment))


def test_missing_field_fails_loudly():
    with pytest.raises(ContractViolation):
        list(parse_jsonl(['{"lesson_id": "lesson-1"}'], Segment))
