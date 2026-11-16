"""Native HTML slide decks: an alternative to a Google Slides link for
Slide Sync Lite (ADR 0014, extended by ADR 0016).

Each deck is one JSON file under ``decks/`` with a title and a list of
slides; each slide is a dict keyed by language code, holding a small HTML
snippet (``it`` is required, the others are optional per-language
translations). Unlike the hover-title translations in ``i18n.py``, these
are shown outright, side by side with the Italian, so students reading a
locally-authored slide deck can follow it in their own language without a
translated Google Slides file existing at all.

A slide may also carry teacher-only metadata beside its language keys:
``id`` (a stable name such as ``S11``), ``notes`` (English presenter
notes), ``verify`` (a list of dated "check before class" flags) and
``optional``. ``get_slide`` never returns them, so the student endpoint
cannot leak them; only the capture-host endpoints expose them, through
``get_slide_meta`` (ADR 0020).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

DECKS_DIR = Path(__file__).parent / "decks"

# The keys of a slide that hold HTML to show; every other key is metadata.
LANG_KEYS = ("it", "en", "fr", "ckb", "kmr", "ar")


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


def get_raw_slide(slug: str, index: int) -> dict | None:
    """The whole slide dict at 1-based ``index``: languages and metadata."""
    deck = get_deck(slug)
    if deck is None:
        return None
    slides = deck.get("slides", [])
    if index < 1 or index > len(slides):
        return None
    return slides[index - 1]


def get_slide_meta(slug: str, index: int) -> dict | None:
    """Teacher-only metadata of a slide (never send this to students)."""
    slide = get_raw_slide(slug, index)
    if slide is None:
        return None
    return {
        "id": slide.get("id"),
        "notes": slide.get("notes", ""),
        "verify": list(slide.get("verify", [])),
        "optional": bool(slide.get("optional", False)),
    }
