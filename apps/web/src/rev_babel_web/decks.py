"""Native HTML slide decks: an alternative to a Google Slides link for
Slide Sync Lite (ADR 0014, extended by ADR 0016).

Each deck is one JSON file under ``decks/`` with a title and a list of
slides; each slide is a dict keyed by language code, holding a small HTML
snippet (``it`` is required, the others are optional per-language
translations). Unlike the hover-title translations in ``i18n.py``, these
are shown outright, side by side with the Italian, so students reading a
locally-authored slide deck can follow it in their own language without a
translated Google Slides file existing at all.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

DECKS_DIR = Path(__file__).parent / "decks"


class DeckSummary(TypedDict):
    slug: str
    title: str
    slide_count: int


def list_decks() -> list[DeckSummary]:
    decks = []
    for path in sorted(DECKS_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        decks.append(
            {
                "slug": path.stem,
                "title": data.get("title", path.stem),
                "slide_count": len(data.get("slides", [])),
            }
        )
    return decks


def get_deck(slug: str) -> dict | None:
    path = DECKS_DIR / f"{slug}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def get_slide(slug: str, index: int, lang: str) -> dict | None:
    """The slide at 1-based ``index``, as Italian plus an optional translation."""
    deck = get_deck(slug)
    if deck is None:
        return None
    slides = deck.get("slides", [])
    if index < 1 or index > len(slides):
        return None
    slide = slides[index - 1]
    return {"it": slide.get("it", ""), "translated": slide.get(lang) if lang != "it" else None}
