"""Lesson 8's take-home card: content, languages and the printed page. Pure
content and invented strings; no student data (docs/data-and-privacy.md)."""

from pathlib import Path

import jinja2
from rev_babel_web import scheda_social

TEMPLATES = Path(__file__).parents[1] / "templates"


def _render(lang: str) -> str:
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES), autoescape=True)
    return env.get_template("games/scheda_social.html").render(**scheda_social.context(lang))


def _texts():
    return list(scheda_social._texts(scheda_social.load()))


def test_every_text_has_italian_and_the_four_numbers():
    texts = _texts()
    assert texts and all(isinstance(t["it"], str) and t["it"] for t in texts)
    values = [n["value"] for n in scheda_social.load()["side2"]["numbers"]]
    assert values == ["commissariatodips.it", "112", "114", "19696"]


def test_unknown_or_untranslated_language_falls_back_to_italian():
    for lang in ("ar", "xx", "it", ""):
        ctx = scheda_social.context(lang)
        assert ctx["lang"] == "it" and ctx["second"] is False
    assert scheda_social.langs() == ["it"]


def test_second_language_needs_every_string(monkeypatch):
    data = scheda_social.load()

    def fake_load():
        import copy

        d = copy.deepcopy(data)
        for t in scheda_social._texts(d):
            t["en"] = t["it"] + " (en)"
        return d

    monkeypatch.setattr(scheda_social, "load", fake_load)
    assert scheda_social.langs() == ["it", "en"]
    ctx = scheda_social.context("en")
    assert ctx["lang"] == "en" and ctx["second"] and not ctx["rtl"]
    html = _render("en")
    assert 'lang="en"' in html and "Fermati. (en)" in html

    # one language missing on one string: not offered
    def fake_partial():
        d = fake_load()
        del d["side1"]["rule"]["en"]
        return d

    monkeypatch.setattr(scheda_social, "load", fake_partial)
    assert scheda_social.langs() == ["it"]


def test_rtl_flag(monkeypatch):
    monkeypatch.setattr(scheda_social, "langs", lambda: ["it", "ar"])
    assert scheda_social.context("ar")["rtl"] is True


def test_printed_page_has_both_sides_twice():
    html = _render("it")
    assert html.count('class="card"') == 4
    assert html.count("Fermati.") == 2
    assert "A4 landscape" in html
    assert html.count('dir="ltr">19696<') == 2
    assert "La mia banca:" in html


def test_privacy_words_absent_from_card_and_docs():
    """The provider, venue, city and people's names must not be written in the
    repository, so they are read from a gitignored file and the test skips
    without it."""
    import pytest

    words_file = Path(__file__).parents[3] / "data" / "private-words.txt"
    if not words_file.exists():
        pytest.skip("data/private-words.txt is absent (maintainer-only, gitignored)")
    words = [w.strip().lower() for w in words_file.read_text(encoding="utf-8").splitlines()]
    words = [w for w in words if w]
    root = Path(__file__).parents[3]
    files = [
        root / "apps/web/src/rev_babel_web/scheda_social.json",
        root / "apps/web/src/rev_babel_web/scheda_social.py",
        TEMPLATES / "games/scheda_social.html",
        root / "docs/decisions/0020-lesson-8-materials-store-and-game.md",
        root / "docs/data-and-privacy.md",
    ]
    for f in files:
        text = f.read_text(encoding="utf-8").lower()
        for w in words:
            assert w not in text, f"{f.name} contains a private word"
