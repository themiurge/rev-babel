"""Lesson 8's presenter pieces: deck CSS in both stylesheets, the notes panel
on /present and the phone remote template (static checks; routes are F's)."""

import re
from pathlib import Path

WEB = Path(__file__).parents[1]
STYLE = (WEB / "static" / "style.css").read_text(encoding="utf-8")
PRESENT = (WEB / "templates" / "present.html").read_text(encoding="utf-8")
REMOTE = (WEB / "templates" / "present_remote.html").read_text(encoding="utf-8")

CLASSES = [
    "rb-slot", ".slot-media", ".slot-img", ".slot-video", ".slot-audio", ".slot-missing",
    ".pair", ".pair-col", ".pair-tag", ".mock-post", ".post-head", ".post-verdict", ".post-row",
    ".ai-label", ".num-grid", ".num-card", ".num-big", ".age-bar", ".age-fill", ".age-mark.m15",
    ".pic.stop", ".pic.red", ".pic.yellow", ".pic-grid.many .pic",
]  # fmt: skip


def test_deck_css_is_in_both_stylesheets() -> None:
    for name in CLASSES:
        assert f".slide-box {name}" in STYLE, name
        assert f"#local-slide {name}" in STYLE, name
        assert f"#local-slide {name}" in PRESENT, name


def test_deck_css_braces_balance() -> None:
    assert STYLE.count("{") == STYLE.count("}")
    style_block = PRESENT.split("<style>")[1].split("</style>")[0]
    assert style_block.count("{") == style_block.count("}")


def test_present_has_hidden_notes_panel_and_links() -> None:
    assert re.search(r'<aside id="notes" hidden>', PRESENT)
    assert 'id="notes-btn" hidden' in PRESENT
    assert 'id="missing"' in PRESENT
    assert 'case "n": case "N"' in PRESENT
    for href in ("/materiali", "/vero-o-falso", "/vero-o-falso/carte", "/games/scheda-social"):
        assert f'href="{href}"' in PRESENT
    assert 'href="/present/telecomando"' in PRESENT


def test_notes_are_written_with_text_content_only() -> None:
    # Notes come from the server, but still: never as HTML.
    assert "innerHTML = data.it" in PRESENT  # the slide itself, as before
    assert PRESENT.count("innerHTML") == 1
    assert "innerHTML" not in REMOTE and "insertAdjacentHTML" not in REMOTE


def test_remote_talks_to_the_planned_endpoints() -> None:
    assert "/admin/api/live/notes" in REMOTE
    assert '"/admin/api/live" + path' in REMOTE
    assert '"/goto"' in REMOTE and '"/status"' in REMOTE
    assert "Nessuna presentazione locale in corso" in REMOTE
    assert "http://" not in REMOTE and "https://" not in REMOTE  # no external assets
