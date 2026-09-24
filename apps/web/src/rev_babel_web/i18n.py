"""Hover translations for the site's Italian UI labels.

Italian is the primary language everywhere; a student's "second language"
only ever shows up as a `title` attribute (a native browser tooltip) over
the Italian text, never replacing it. `STRINGS` is keyed by the exact
Italian source string, which doubles as the translation key - no
separate id scheme to keep in sync with the templates.

Translations were machine-generated in batches (see the `agy` CLI
sessions referenced in ADR 0015) and have not been reviewed by a native
speaker of any of the five languages. Treat them as a first pass, not a
verified translation - especially the two Kurdish variants: `ckb` (Sorani
/ Central Kurdish) was the maintainer's best guess at "the northern Iraq
one," and `kmr` (Kurmanji / Northern Kurdish) was added alongside it as a
hedge rather than a confirmed correction - see ADR 0015's follow-up.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

LanguageCode = Literal["it", "en", "fr", "ckb", "kmr", "ar"]

# Display name for each selectable "second language," shown in its own
# script so the choice doesn't require reading Italian or Latin script.
# "it" isn't offered as a second language - the dropdown's own default
# state (no hover translations at all) covers that case.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "fr": "Français",
    "ckb": "کوردی",
    "kmr": "Kurmancî",
    "ar": "العربية",
}

RTL_LANGUAGES = {"ckb", "ar"}

_STRINGS_PATH = Path(__file__).parent / "strings.json"
STRINGS: dict[str, dict[str, str]] = json.loads(_STRINGS_PATH.read_text(encoding="utf-8"))


def translate(text: str, lang: str) -> str:
    """The hover text for `text` in `lang`, or "" if there is none.

    Returns "" (not `text` itself) for `lang == "it"` and for any string
    missing a translation, so templates can do
    `{% if hint %}title="{{ hint }}"{% endif %}` and simply omit the
    attribute rather than showing a redundant or empty tooltip.
    """
    if lang == "it":
        return ""
    return STRINGS.get(text, {}).get(lang, "")
