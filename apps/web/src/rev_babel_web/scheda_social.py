"""Lesson 8's printable take-home card (ADR 0020).

Pure content: ``scheda_social.json`` holds every string in Italian and, once
translated, in other languages. Nothing here is personal data and nothing is
stored.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

RTL = ("ar", "ckb")


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(Path(__file__).with_name("scheda_social.json").read_text(encoding="utf-8"))


def _texts(node):
    """Yield every text object: a dict whose ``it`` is a string."""
    if isinstance(node, dict):
        if isinstance(node.get("it"), str):
            yield node
        for value in node.values():
            yield from _texts(value)
    elif isinstance(node, list):
        for value in node:
            yield from _texts(value)


def langs() -> list[str]:
    """``it`` plus every language present on every string of the card."""
    texts = list(_texts(load()))
    common: set[str] | None = None
    for text in texts:
        keys = {k for k, v in text.items() if k != "it" and k != "emoji" and isinstance(v, str)}
        common = keys if common is None else common & keys
    return ["it", *sorted(common or ())]


def context(lang: str) -> dict:
    available = langs()
    chosen = lang if lang in available else "it"
    return {
        "c": load(),
        "lang": chosen,
        "second": chosen != "it",
        "rtl": chosen in RTL,
    }
