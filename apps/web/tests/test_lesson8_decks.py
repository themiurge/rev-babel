"""Lesson 8's two decks: structure, teacher-only metadata, markup."""

import re
from html.parser import HTMLParser

from rev_babel_web import decks

MAIN = "lezione-8-social"
PARENTS = "lezione-8-genitori"

MAIN_IDS = (
    ["S%02d" % n for n in range(1, 19)]
    + ["S18b"]
    + ["S%02d" % n for n in range(19, 26)]
    + ["S25b"]
    + ["S%02d" % n for n in range(26, 34)]
)
PARENT_IDS = ["G%02d" % n for n in range(1, 15)]
FLAGGED = {
    MAIN: ["S06", "S08", "S13", "S15", "S19", "S23", "S24", "S28", "S29", "S32"],
    PARENTS: ["G03", "G08", "G09", "G10", "G11", "G14"],
}
# Copied from materials.SLOT_TAG_RE on purpose (this package does not import it).
SLOT_TAG_RE = re.compile(
    r"<rb-slot data-slot=([\"'])(?P<id>[A-Z][0-9]{1,2}(?:-[A-Z])?)\1"
    r"(?: data-field=([\"'])(?P<field>[a-z_]{1,20})\3)?>(?P<inner>.*?)</rb-slot>",
    re.DOTALL,
)
VOID = {"br", "hr", "img", "input", "meta", "link", "wbr"}


def _slides(slug: str) -> list[dict]:
    deck = decks.get_deck(slug)
    assert deck is not None
    return deck["slides"]


class _Walker(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[str] = []
        self.errors: list[str] = []
        self.text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"unexpected </{tag}> with stack {self.stack}")
            return
        self.stack.pop()

    def handle_data(self, data):
        self.text.append(data)


def _walk(html: str) -> _Walker:
    walker = _Walker()
    walker.feed(html)
    walker.close()
    return walker


def test_both_decks_are_listed_with_their_titles() -> None:
    found = {d["slug"]: d for d in decks.list_decks()}
    assert found[MAIN]["slide_count"] == 35
    assert found[MAIN]["title"] == "Social media: come funzionano e come usarli in sicurezza"
    assert found[PARENTS]["slide_count"] == 14
    assert found[PARENTS]["title"] == "Genitori e social media: come accompagnare i figli"


def test_ids_are_in_the_planned_order_and_every_slide_has_text_and_notes() -> None:
    for slug, ids in ((MAIN, MAIN_IDS), (PARENTS, PARENT_IDS)):
        slides = _slides(slug)
        assert [s["id"] for s in slides] == ids
        for slide in slides:
            assert slide["it"].strip(), slide["id"]
            assert slide["notes"].strip(), slide["id"]


def test_optional_slides_and_verify_flags() -> None:
    main = {s["id"]: s for s in _slides(MAIN)}
    assert {i for i, s in main.items() if s.get("optional")} == {"S08", "S29"}
    for slug, ids in FLAGGED.items():
        by_id = {s["id"]: s for s in _slides(slug)}
        for slide_id in ids:
            flags = by_id[slide_id].get("verify")
            assert flags, slide_id
            assert all(f.startswith("VERIFY before class") for f in flags), slide_id


def test_no_placeholder_leaks_slots_are_well_formed_and_tags_balance() -> None:
    for slug in (MAIN, PARENTS):
        for slide in _slides(slug):
            html = slide["it"]
            assert "{{ROUTE" not in html and "NT(" not in html, slide["id"]
            assert html.count("<rb-slot") == len(SLOT_TAG_RE.findall(html)), slide["id"]
            walker = _walk(html)
            assert walker.errors == [] and walker.stack == [], (slide["id"], walker.errors)


def test_route_strip_marks_the_current_stop() -> None:
    by_id = {s["id"]: s for s in _slides(MAIN)}
    assert 'class="stop now">1 Account' in by_id["S05"]["it"]
    assert 'class="stop done">1 Account' in by_id["S09"]["it"]
    assert "stop now" not in by_id["S04"]["it"] and "stop done" not in by_id["S04"]["it"]
    assert by_id["S31"]["it"].count("stop done") == 6
    assert "route" not in {s["id"]: s for s in _slides(PARENTS)}["G01"]["it"]


def test_get_slide_never_returns_the_notes() -> None:
    for slug in (MAIN, PARENTS):
        for index in (1, 6, 11):
            slide = decks.get_slide(slug, index, "ar")
            assert slide is not None
            assert set(slide) == {"it", "translated"}
            for value in slide.values():
                assert value is None or "VERIFY" not in value


def test_meta_and_raw_slide_and_out_of_range() -> None:
    meta = decks.get_slide_meta(MAIN, 11)
    assert meta is not None
    assert meta["id"] == "S11" and meta["notes"] and meta["optional"] is False
    assert decks.get_slide_meta(MAIN, 8)["optional"] is True
    assert decks.get_slide_meta(MAIN, 6)["verify"]
    raw = decks.get_raw_slide(MAIN, 11)
    assert raw is not None and raw["id"] == "S11" and "it" in raw
    for index in (0, 36):
        assert decks.get_raw_slide(MAIN, index) is None
        assert decks.get_slide_meta(MAIN, index) is None
    assert decks.get_raw_slide("nope", 1) is None


def test_word_budget() -> None:
    for slug in (MAIN, PARENTS):
        for slide in _slides(slug):
            # Emoji and bare symbols are pictures, not words to read.
            tokens = " ".join(_walk(slide["it"]).text).split()
            words = len([t for t in tokens if re.search(r"\w", t)])
            # Three posts to read (S18) and six scam tiles (S23) need more.
            limit = {"S18": 100, "S18b": 100, "S23": 70}.get(slide["id"], 60)
            assert words <= limit, (slide["id"], words)
