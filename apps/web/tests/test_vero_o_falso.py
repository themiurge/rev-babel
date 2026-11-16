"""Lesson 8's game: content, scoring, page config and the answer cards."""

import json
import re

import pytest
from rev_babel_web import vero_o_falso as vof

DATA = vof.load()
ITEMS = {i["id"]: i for i in DATA["items"]}
MOCK_ONLY = {"M1", "M2", "M3", "M4", "M5", "P2", "P3"}


def _cfg(statuses=None, render=lambda h: h):
    return vof.page_config(statuses or {}, render)


def _by_id(cfg):
    return {i["id"]: i for i in cfg["items"]}


def _status(slot, family="image", skipped=False, fields=None):
    return {
        "id": slot,
        "state": "pronto",
        "skipped": skipped,
        "file": {"family": family, "url": f"/admin/materials/{slot}/file?v=abc"},
        "fields": fields or {},
    }


def test_content_is_valid_with_the_planned_mix():
    assert vof.validate(DATA) == []
    assert len(DATA["items"]) == 12
    mix = {}
    for item in DATA["items"]:
        mix.setdefault(item["category"], []).append(item["answer"])
    count = {c: sorted(a) for c, a in mix.items()}
    assert count["foto"] == ["falso_ia", "vero", "vero"]
    assert count["video"] == ["falso_ia", "vero"]
    assert count["messaggi"] == ["truffa"] * 3 + ["vero"] * 2
    assert count["post"] == ["falso_ia", "falso_ia"]
    assert sum(1 for i in DATA["items"] if i["answer"] == "vero") == 5


def test_validate_catches_problems():
    bad = json.loads(json.dumps(DATA))
    bad["items"][0]["onlyVerifiable"] = True
    bad["items"][1]["answer"] = "boh"
    assert len(vof.validate(bad)) >= 2


def test_points():
    hard = {"answer": "vero", "hardToJudge": True, "onlyVerifiable": False}
    easy = {"answer": "truffa", "hardToJudge": False, "onlyVerifiable": False}
    only = {"answer": "verificare", "hardToJudge": True, "onlyVerifiable": True}
    assert vof.points(hard, "vero") == 2
    assert vof.points(hard, "verificare") == 1
    assert vof.points(hard, "truffa") == 0
    assert vof.points(easy, "verificare") == 0
    assert vof.points(easy, "truffa") == 2
    assert vof.points(only, "verificare") == 2
    assert vof.points(only, "vero") == 0
    for item in DATA["items"]:
        assert all(p >= 0 for p in vof.points_table(item).values())
        assert vof.points_table(item)[item["answer"]] == 2


def test_page_config_without_materials():
    cfg = _cfg()
    items = _by_id(cfg)
    assert {i for i, v in items.items() if v["available"]} == MOCK_ONLY
    assert items["I1"]["missingSlot"] == "I1"
    assert items["I1"]["mockHtml"] is None
    assert items["M1"]["usesFallback"] and items["M1"]["invented"]
    assert items["P2"]["invented"] and not items["P2"]["usesFallback"]
    assert [i["id"] for i in cfg["items"][:3]] == ["I1", "I2", "I3"]
    assert cfg["langs"][0] == "it"
    assert len(cfg["answers"]) == 4


def test_page_config_with_statuses_and_render():
    st = {
        "I1": _status("I1", fields={"caption": "Mia didascalia"}),
        "M1": _status("M1", skipped=True),
    }
    items = _by_id(_cfg(st, render=lambda h: "R:" + h))
    assert items["I1"]["available"] and items["I1"]["mediaType"] == "image"
    assert items["I1"]["mediaUrl"] == "/admin/materials/I1/file?v=abc"
    assert items["I1"]["caption"] == {"it": "Mia didascalia"}
    assert items["I1"]["alt"] == "Mia didascalia"
    assert items["M1"]["invented"]  # skipped: back to the mock
    assert items["M1"]["mediaType"] is None and items["M1"]["mockHtml"].startswith("R:")
    assert items["M2"]["mockHtml"].startswith("R:")


def test_mocks_have_no_links_or_scripts():
    for item in DATA["items"]:
        mock = item["mock"] or ""
        low = mock.lower()
        for bad in ("href", "http", "www.", "<script"):
            assert bad not in low, (item["id"], bad)
        # link-like text must be blurred
        for m in re.finditer(r"[\w-]+\.(?:it|com|org)\b", mock):
            pytest.fail(f"{item['id']}: unblurred link-like text {m.group(0)}")
    assert "blur" in ITEMS["M2"]["mock"]


def test_cards_context():
    ctx = vof.cards_context(9)
    assert ctx["copies"] == 4
    assert vof.cards_context(0)["copies"] == 1
    assert [c["id"] for c in ctx["cards"]] == list(vof.ANSWERS)
    assert set(ctx["langs"]) <= {"en", "fr", "ar", "ckb", "kmr"}
