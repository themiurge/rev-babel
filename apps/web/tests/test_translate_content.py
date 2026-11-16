"""scripts/translate_content.py, with a fake translator (no network)."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "translate_content.py"
spec = importlib.util.spec_from_file_location("translate_content", SCRIPT)
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)


def fake(text, source, target, fmt):
    if fmt == "html":
        return re.sub(
            r">([^<]+)<",
            lambda m: m.group(0) if m.group(1).isdigit() else f">[{target}] {m.group(1)}<",
            f">{text}<",
        )[1:-1]
    return f"[{target}] {text}"


@pytest.fixture
def web(tmp_path):
    (tmp_path / "decks").mkdir()
    deck = {
        "title": "t",
        "slides": [
            {
                "id": "S1",
                "it": '<p class="a">Chiama il <span translate="no">112</span></p>'
                '<rb-slot data-slot="S1-A"></rb-slot>',
                "notes": "never sent",
                "verify": ["x"],
            }
        ],
    }
    for slug in tc.DECK_SLUGS:
        (tmp_path / "decks" / f"{slug}.json").write_text(json.dumps(deck))
    game = {
        "ui": {"title": {"it": "Vero o falso?"}},
        "items": [{"mock": {"it": "no"}, "caption": {}}],
    }
    (tmp_path / "vero_o_falso.json").write_text(json.dumps(game))
    card = {"q": [{"emoji": "x", "it": "Fermati."}], "n": {"value": "112"}}
    (tmp_path / "scheda_social.json").write_text(json.dumps(card))
    (tmp_path / "strings.json").write_text(json.dumps({"Ciao": {"en": "Hi"}}))
    return tmp_path


def run(web, **kw):
    units, docs = tc.collect(web)
    sent = []

    def fn(*a):
        sent.append(a[0])
        return fake(*a)

    args = {"langs": ["en", "ar"], "force": False, "dry_run": False}
    args.update(kw)
    return (
        units,
        docs,
        sent,
        tc.run_translation(units, docs, translate_fn=fn, out=lambda *_: None, **args),
    )


def test_collect_units_and_metadata_never_sent(web):
    units, _ = tc.collect(web)
    ids = {u.id for u in units}
    assert "deck:lezione-8-social:S1" in ids
    assert "game:ui.title" in ids and "scheda:q[0]" in ids
    assert not any("mock" in i for i in ids)
    _, _, sent, _ = run(web)
    assert not any("never sent" in s or s == "x" for s in sent)


def test_dry_run_sends_nothing(web):
    _, _, sent, result = run(web, dry_run=True)
    assert sent == [] and result["count"]["en"] > 0


def test_translates_and_keeps_existing_without_force(web):
    units, docs, sent, result = run(web)
    ui = next(u for u in units if u.id == "ui:I social network")
    assert ui.holder["en"] == "[en] I social network"
    assert not result["failed"]
    saved = json.loads((web / "scheda_social.json").read_text())
    assert saved["translation"]["reviewed"] is False
    again = tc.collect(web)[0]
    assert tc.pending(again, ["en", "ar"], force=False) == []
    assert len(tc.pending(again, ["en"], force=True)) == len(again)


def test_existing_string_not_overwritten(web):
    units, _ = tc.collect(web)
    assert all(u.holder.get("en") != "x" for u in units)
    (web / "strings.json").write_text(json.dumps({"I social network": {"en": "Mine"}}))
    units, docs = tc.collect(web)
    tc.run_translation(units, docs, ["en"], False, False, fake, out=lambda *_: None)
    assert json.loads((web / "strings.json").read_text())["I social network"]["en"] == "Mine"


IT = (
    '<p class="a">Chiama il <span translate="no">112</span></p><rb-slot data-slot="S1-A"></rb-slot>'
)
UNIT = tc.Unit("x", IT, "html", {}, Path("x"))


def test_validation():
    assert tc.validate(UNIT, fake(IT, "it", "en", "html")) is None
    assert "tag" in tc.validate(UNIT, IT.replace('<p class="a">', "<p>"))
    assert tc.validate(UNIT, IT.replace("</p>", ""))
    assert "rb-slot" in tc.validate(UNIT, IT.replace("S1-A", "S1-B"))
    assert tc.validate(UNIT, IT.replace(">112<", ">113<"))
    assert "protected" in tc.validate(
        tc.Unit("y", "Chiama il 19696", "text", {}, Path("y")), "Call"
    )
    assert (
        tc.validate(
            tc.Unit("y", "Vai su commissariatodips.it", "text", {}, Path("y")),
            "Go to commissariatodips.it",
        )
        is None
    )


def test_rejected_unit_left_untranslated(web):
    units, docs = tc.collect(web)
    result = tc.run_translation(
        units,
        docs,
        ["en"],
        False,
        False,
        lambda t, s, g, f: "<b>x</b>" if f == "html" else "ok",
        out=lambda *_: None,
    )
    assert result["failed"] and not units[0].holder.get("en")


def test_csv_round_trip(web, tmp_path):
    units, docs, _, _ = run(web)
    csv_path = tmp_path / "out.csv"
    tc.export_csv(units, csv_path)
    assert csv_path.read_bytes().startswith(b"\xef\xbb\xbf")
    text = csv_path.read_text(encoding="utf-8-sig").replace("[en] Fermati.", "Stop.")
    csv_path.write_text(text, encoding="utf-8-sig")
    units, docs = tc.collect(web)
    assert tc.import_csv(units, docs, csv_path, out=lambda *_: None) == 1
    assert json.loads((web / "scheda_social.json").read_text())["q"][0]["en"] == "Stop."
