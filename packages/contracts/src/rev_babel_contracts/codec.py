from collections.abc import Iterable, Iterator
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from .errors import ContractViolation

M = TypeVar("M", bound=BaseModel)


def dump_jsonl(items: Iterable[BaseModel]) -> Iterator[str]:
    """One JSON object per line, UTF-8, no trailing whitespace beyond the newline."""
    for item in items:
        yield item.model_dump_json() + "\n"


def parse_jsonl(lines: Iterable[str], model: type[M]) -> Iterator[M]:
    """Parse a JSON Lines stream into `model` instances.

    Blank lines are skipped. Anything else that fails to parse or fails the
    model's own shape validation raises `ContractViolation` immediately:
    a malformed stream fails loudly rather than silently dropping the line.
    """
    for lineno, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            yield model.model_validate_json(stripped)
        except ValidationError as exc:
            raise ContractViolation(f"line {lineno}: malformed {model.__name__}: {exc}") from exc
