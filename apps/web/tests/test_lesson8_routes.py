"""Lesson 8 wiring: materials API, decks, game, card (ADR 0020).

Fixtures are invented bytes; students are role labels. Host gating uses the
conftest capture host ``mic.test``.
"""

import json
import re
import struct
import zlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from rev_babel_web import decks, live, main, materials
from rev_babel_web.main import app

HOST = {"Host": "mic.test"}
WEB = Path(__file__).parents[1]
SRC = WEB / "src" / "rev_babel_web"
DECK = "lezione-8-social"


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(materials, "MATERIALS_DIR", tmp_path / "materials")
    monkeypatch.setattr(main, "MATERIALS_KEY", "")
    yield
    live.end()


def _teacher() -> TestClient:
    return TestClient(app, headers=HOST)


def _student(name: str = "student_a") -> TestClient:
    c = TestClient(app)
    c.post("/welcome", data={"name": name})
    return c


def _chunk(kind: bytes, data: bytes) -> bytes:
    body = kind + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def _png(text: bytes = b"") -> bytes:
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    idat = zlib.compress(b"\x00\xff\x00\x00")
    parts = [b"\x89PNG\r\n\x1a\n", _chunk(b"IHDR", ihdr)]
    if text:
        parts.append(_chunk(b"tEXt", text))
    parts += [_chunk(b"IDAT", idat), _chunk(b"IEND", b"")]
    return b"".join(parts)


def _slide_index(slot_id: str, deck: str = DECK) -> int:
    for i, s in enumerate(decks.get_deck(deck)["slides"], start=1):
        if slot_id in materials.slots_in_html(s["it"]):
            return i
    raise AssertionError(slot_id)


def _go_live(index: int) -> None:
    live.start_local(DECK, "Test deck", len(decks.get_deck(DECK)["slides"]))
    live.goto(index)


# 25
def test_lesson_page_lists_card_and_follow() -> None:
    page = _student().get("/course/lezione-8")
    assert page.status_code == 200
    assert "Scheda da portare a casa" in page.text
    assert "Segui la lezione" in page.text
    assert "I social network" in page.text


# 26
@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/materiali"),
        ("get", "/admin/api/materials"),
        ("post", "/admin/api/materials/S11-A/file"),
        ("delete", "/admin/api/materials/S11-A/file"),
        ("post", "/admin/api/materials/S11-A/fields"),
        ("post", "/admin/api/materials/S11-A/skip"),
        ("post", "/admin/api/materials/delete-all"),
        ("get", "/admin/materials/S11-A/file"),
        ("get", "/vero-o-falso"),
        ("get", "/vero-o-falso/carte"),
        ("get", "/present/telecomando"),
        ("get", "/admin/api/live/notes"),
        ("get", f"/admin/api/decks/{DECK}/slides/1"),
    ],
)
def test_off_the_capture_host_is_forbidden(method: str, path: str) -> None:
    c = _student()
    bodies = {
        "fields": {"fields": {}},
        "skip": {"skipped": True},
        "delete-all": {"confirm": "ELIMINA"},
    }
    body = bodies.get(path.rsplit("/", 1)[-1])
    kwargs = {"json": body} if body else {}
    response = getattr(c, method)(path, **kwargs) if method != "delete" else c.delete(path)
    assert response.status_code == 403


# 27
def test_materials_page_and_listing() -> None:
    t = _teacher()
    assert t.get("/materiali").status_code == 200
    data = t.get("/admin/api/materials").json()
    ids = [s["id"] for s in materials.manifest()["slots"]]
    assert [s["id"] for s in data["slots"]] == ids
    assert all(s["status"]["state"] == "mancante" for s in data["slots"])
    assert data["keyConfigured"] is False
    parents = next(a for a in data["artifacts"] if a["id"] == "deck-parents")
    assert parents["nothingNeeded"] is True


# 28
def test_upload_round_trip_and_errors() -> None:
    t = _teacher()
    r = t.post("/admin/api/materials/S11-A/file", content=_png(b"Comment\x00secret"))
    assert r.status_code == 200
    assert r.json()["state"] == "pronto"
    got = t.get("/admin/materials/S11-A/file")
    assert got.status_code == 200
    assert got.headers["x-content-type-options"] == "nosniff"
    assert "private" in got.headers["cache-control"]
    assert b"tEXt" not in got.content and got.content.startswith(b"\x89PNG")
    ranged = t.get("/admin/materials/S11-A/file", headers={"Range": "bytes=0-3"})
    assert ranged.status_code == 206
    assert t.post("/admin/api/materials/S11-A/file", content=b"hello").status_code == 415
    heic = b"\x00\x00\x00\x18ftypheic" + b"\x00" * 20
    bad = t.post("/admin/api/materials/S11-A/file", content=heic)
    assert bad.status_code == 415 and "HEIC" in bad.json()["detail"]
    assert t.post("/admin/api/materials/S11-A/file", content=b"").status_code == 400
    big = t.post(
        "/admin/api/materials/S11-A/file", content=b"\0" * (materials.limit_for("S11-A") + 1)
    )
    assert big.status_code == 413
    assert t.post("/admin/api/materials/NOPE/file", content=_png()).status_code == 404
    assert t.post("/admin/api/materials/..%2Fx/file", content=_png()).status_code == 404
    assert t.get("/admin/materials/NOPE/file").status_code == 404
    assert not list((materials.MATERIALS_DIR / ".tmp").glob("*"))


# 29
def test_fields_skip_delete_and_delete_all() -> None:
    t = _teacher()
    base = "/admin/api/materials/I1"
    r = t.post(f"{base}/fields", json={"fields": {"caption": "Mercato"}})
    assert r.status_code == 200 and r.json()["fields"]["caption"] == "Mercato"
    assert t.post(f"{base}/fields", json={"fields": {"nope": "x"}}).status_code == 400
    t.post(f"{base}/file", content=_png())
    assert t.post(f"{base}/skip", json={"skipped": True}).json()["state"] == "saltato"
    assert t.get("/admin/materials/I1/file").status_code == 200  # teacher preview
    assert t.post(f"{base}/skip", json={"skipped": False}).json()["state"] == "pronto"
    assert t.delete(f"{base}/file").json()["file"] is None
    t.post(f"{base}/file", content=_png())
    assert t.post("/admin/api/materials/delete-all", json={"confirm": "no"}).status_code == 400
    assert t.get("/admin/materials/I1/file").status_code == 200
    assert t.post("/admin/api/materials/delete-all", json={"confirm": "ELIMINA"}).json() == {
        "ok": True
    }
    assert t.get("/admin/materials/I1/file").status_code == 404


# 30
def test_key_gate(monkeypatch) -> None:
    monkeypatch.setattr(main, "MATERIALS_KEY", "chiave-di-prova")
    t = _teacher()
    assert t.get("/admin/api/materials").status_code == 401
    assert t.post("/admin/api/materials/I1/file", content=_png()).status_code == 401
    assert 'action="/materiali/chiave"' in t.get("/materiali").text
    wrong = t.get("/materiali?k=sbagliata")
    assert wrong.status_code == 200 and "Chiave sbagliata" in wrong.text
    assert t.get("/admin/api/materials").status_code == 401
    bad = t.post("/materiali/chiave", data={"key": "x"})
    assert "Chiave sbagliata" in bad.text
    ok = t.get("/materiali?k=chiave-di-prova", follow_redirects=False)
    assert ok.status_code == 303 and ok.headers["location"] == "/materiali"
    assert t.get("/admin/api/materials").json()["keyConfigured"] is True
    # The file GET needs no key (classroom PC, /present and the game).
    other = _teacher()
    t.post("/admin/api/materials/I1/file", content=_png())
    assert other.get("/admin/materials/I1/file").status_code == 200
    form = _teacher()
    r = form.post("/materiali/chiave", data={"key": "chiave-di-prova"}, follow_redirects=False)
    assert r.status_code == 303
    assert form.get("/admin/api/materials").status_code == 200


# 31
def test_slides_notes_and_urls() -> None:
    t = _teacher()
    idx = _slide_index("S11-A")
    slide = t.get(f"/admin/api/decks/{DECK}/slides/{idx}").json()
    assert slide["id"] == "S11" and slide["notes"]
    assert [m["id"] for m in slide["missing"]] == ["S11-A", "S11-B"]
    assert all(m["needed"] for m in slide["missing"])
    assert "slot-missing" in slide["it"] and "<rb-slot" not in slide["it"]
    _go_live(idx)
    student = _student()
    s_slide = student.get(f"/api/live/slide?index={idx}").json()
    assert "notes" not in s_slide and "verify" not in s_slide and "id" not in s_slide
    assert "<rb-slot" not in s_slide["it"]
    t.post("/admin/api/materials/S11-A/file", content=_png())
    assert (
        "/admin/materials/S11-A/file?v="
        in t.get(f"/admin/api/decks/{DECK}/slides/{idx}").json()["it"]
    )
    assert "/api/live/material/S11-A?v=" in student.get(f"/api/live/slide?index={idx}").json()["it"]
    notes = t.get("/admin/api/live/notes").json()
    assert notes["state"]["index"] == idx
    assert notes["slide"]["id"] == "S11" and notes["slide"]["notes"]
    assert [m["id"] for m in notes["slide"]["missing"]] == ["S11-B"]
    assert set(notes["slide"]) == {"id", "notes", "verify", "optional", "missing"}


def test_notes_endpoint_null_when_not_local() -> None:
    live.start("1AbC", "Google deck", 5)
    assert _teacher().get("/admin/api/live/notes").json()["slide"] is None
    live.end()


# 32
def test_student_material_gating() -> None:
    t = _teacher()
    idx = _slide_index("S11-A")
    t.post("/admin/api/materials/S11-A/file", content=_png())
    t.post("/admin/api/materials/S11-B/file", content=_png())
    _go_live(idx)
    student = _student()
    r = student.get("/api/live/material/S11-A")
    assert r.status_code == 200 and r.headers["x-content-type-options"] == "nosniff"
    assert TestClient(app).get("/api/live/material/S11-A").status_code == 401
    assert student.get("/api/live/material/I1").status_code == 404  # not on this slide
    assert student.get("/api/live/material/..%2Fx").status_code == 404
    live.set_status("blank")
    assert student.get("/api/live/material/S11-A").status_code == 404
    live.set_status("live")
    t.post("/admin/api/materials/S11-A/skip", json={"skipped": True})
    assert student.get("/api/live/material/S11-A").status_code == 404
    live.goto(idx + 1 if idx < 35 else idx - 1)
    assert student.get("/api/live/material/S11-B").status_code == 404
    live.end()
    assert student.get("/api/live/material/S11-B").status_code == 404


# 33
def test_game_page_config() -> None:
    t = _teacher()

    def config() -> dict:
        html = t.get("/vero-o-falso").text
        raw = re.search(r'id="vof-config" type="application/json">(.*?)</script>', html, re.S)
        return json.loads(raw.group(1).replace("<\\/", "</"))

    cfg = config()
    assert len(cfg["items"]) == 18
    assert sum(1 for i in cfg["items"] if i["available"]) == 9
    t.post("/admin/api/materials/I1/file", content=_png())
    item = next(i for i in config()["items"] if i["id"] == "I1")
    assert item["available"] and "/admin/materials/I1/file?v=" in json.dumps(item)


# 34
def test_cards_page() -> None:
    t = _teacher()
    page = t.get("/vero-o-falso/carte")
    assert page.status_code == 200
    for word in ("Vero", "Falso", "Truffa", "Verificare"):
        assert word.lower() in page.text.lower()
    one = t.get("/vero-o-falso/carte?copie=1").text
    two = t.get("/vero-o-falso/carte?copie=2").text
    assert len(two) > len(one)


# 35
def test_take_home_card() -> None:
    student = _student()
    r = student.get("/games/scheda-social")
    assert r.status_code == 200 and "commissariatodips.it" in r.text
    anon = TestClient(app).get("/games/scheda-social", follow_redirects=False)
    assert anon.status_code == 303 and anon.headers["location"] == "/"
    assert _teacher().get("/games/scheda-social?lang=ar").status_code == 200
    assert _teacher().get("/games/scheda-social").status_code == 200


# 36
def test_manifest_consistency() -> None:
    m = materials.manifest()
    by_id = {s["id"]: s for s in m["slots"]}
    for deck_slug, art in (
        ("lezione-8-social", "deck-main"),
        ("lezione-8-genitori", "deck-parents"),
    ):
        used = set()
        for s in decks.get_deck(deck_slug)["slides"]:
            for lang in decks.LANG_KEYS:
                used |= materials.slots_in_html(str(s.get(lang) or ""))
        assert used <= set(by_id), used - set(by_id)
        assert {i for i in used if by_id[i]["artifact"] != art} == set()
        assert used == {i for i, s in by_id.items() if s["artifact"] == art}
    game = json.loads((SRC / "vero_o_falso.json").read_text(encoding="utf-8"))
    game_slots = set()
    for item in game["items"]:
        if item.get("media"):
            sid = item["media"]["slot"]
            assert by_id[sid]["artifact"] == "game"
            assert by_id[sid]["answer"] == item["answer"]
            game_slots.add(sid)
        if item.get("mock"):
            found = materials.slots_in_html(json.dumps(item["mock"]))
            assert found <= set(by_id)
            game_slots |= found
    assert game_slots == {i for i, s in by_id.items() if s["artifact"] == "game"}


# 37
def test_privacy_grep_lesson8_files() -> None:
    words_file = Path(__file__).parents[3] / "data" / "private-words.txt"
    if not words_file.is_file():
        pytest.skip("data/private-words.txt is absent (CI): nothing to check against")
    words = [w.strip().lower() for w in words_file.read_text(encoding="utf-8").splitlines()]
    words = [w for w in words if w]
    files = [
        SRC / "decks" / "lezione-8-social.json",
        SRC / "decks" / "lezione-8-genitori.json",
        SRC / "materials_manifest.json",
        SRC / "vero_o_falso.json",
        SRC / "scheda_social.json",
        WEB / "templates" / "materials.html",
        WEB / "templates" / "present_remote.html",
        WEB / "templates" / "games" / "vero_o_falso.html",
        WEB / "templates" / "games" / "vero_o_falso_carte.html",
        WEB / "templates" / "games" / "_vof_icons.html",
        WEB / "templates" / "games" / "scheda_social.html",
        WEB / "static" / "lessons" / "lezione-8" / "materiali" / "materiali.js",
        WEB / "static" / "lessons" / "lezione-8" / "vero-o-falso" / "game.js",
    ]
    for f in files:
        assert f.is_file(), f
        text = f.read_text(encoding="utf-8").lower()
        for w in words:
            assert w not in text, f"a forbidden word appears in {f.name}"


# 38
def test_present_links_and_remote_page() -> None:
    t = _teacher()
    page = t.get("/present")
    assert page.status_code == 200
    assert "/materiali" in page.text and "/present/telecomando" in page.text
    assert "lezione-8-social" in page.text and "lezione-8-genitori" in page.text
    assert t.get("/present/telecomando").status_code == 200
