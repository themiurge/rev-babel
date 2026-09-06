from collections.abc import Iterable, Iterator

from .caption import Caption
from .errors import ContractViolation
from .segment import Segment

# "Roughly 3-15 seconds of speech, hard-capped" (plans/m1-translation.md);
# the hard cap is the part a validator can actually enforce.
MAX_SEGMENT_MS = 15_000


def validate_segment_stream(segments: Iterable[Segment]) -> Iterator[Segment]:
    """Assert the characteristics `services/asr` must guarantee: `seq` is
    gapless and in order, and no segment exceeds the hard duration cap.

    Raises `ContractViolation` on the first violation, rather than skipping
    or reordering: an out-of-order stream is a bug upstream, not a case to
    paper over here.
    """
    expected_seq: int | None = None
    for segment in segments:
        if expected_seq is None:
            expected_seq = segment.seq
        elif segment.seq != expected_seq:
            raise ContractViolation(
                f"Segment.seq out of order or gapped for lesson {segment.lesson_id!r}: "
                f"expected {expected_seq}, got {segment.seq}"
            )

        duration = segment.ended_at_ms - segment.started_at_ms
        if duration > MAX_SEGMENT_MS:
            raise ContractViolation(
                f"Segment {segment.seq} spans {duration} ms, exceeding the "
                f"{MAX_SEGMENT_MS} ms hard cap"
            )

        yield segment
        expected_seq += 1


def validate_caption_stream(captions: Iterable[Caption]) -> Iterator[Caption]:
    """Assert `seq` is gapless and in order within each `target_lang`: a
    caption stream fans one segment stream out per language (docs/eco.md),
    so each language's sub-stream must independently satisfy the same
    ordering guarantee as the segments it was translated from.
    """
    expected_seq: dict[str, int] = {}
    for caption in captions:
        next_expected = expected_seq.get(caption.target_lang)
        if next_expected is None:
            next_expected = caption.seq
        elif caption.seq != next_expected:
            raise ContractViolation(
                f"Caption.seq out of order or gapped for lesson {caption.lesson_id!r} "
                f"target_lang {caption.target_lang!r}: expected {next_expected}, "
                f"got {caption.seq}"
            )

        yield caption
        expected_seq[caption.target_lang] = next_expected + 1
