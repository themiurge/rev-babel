"""Shared data shapes passed between rev-babel's services: a transcribed
`Segment` (services/asr) and a translated `Caption` (services/mt), the same
shape on stdin, on an asyncio queue, and on a WebSocket (issue 0005).
"""

from .caption import Caption
from .codec import dump_jsonl, parse_jsonl
from .errors import ContractViolation
from .segment import Segment, SourceLang
from .validation import validate_caption_stream, validate_segment_stream

__all__ = [
    "Caption",
    "ContractViolation",
    "Segment",
    "SourceLang",
    "dump_jsonl",
    "parse_jsonl",
    "validate_caption_stream",
    "validate_segment_stream",
]
