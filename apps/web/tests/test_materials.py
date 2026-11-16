"""Tests for the lesson 8 materials store, on invented bytes in a temp dir."""

import copy
import struct
import zlib

import pytest
from rev_babel_web import materials as m


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(m, "MATERIALS_DIR", tmp_path / "materials")
    return tmp_path / "materials"


def png_chunk(ctype: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(ctype + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + ctype + data + struct.pack(">I", crc)


def make_png(extra: bytes = b"") -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n"
        + png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
        + extra
        + png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
        + png_chunk(b"IEND", b"")
    )


JPEG = b"\xff\xd8\xff\xe1\x00\x08Exif\x00\x00\xff\xda\x00\x02data\xff\xd9"
OGG = b"OggS" + b"\x00" * 30


def upload(slot_id: str, data: bytes) -> dict:
    p = m.new_tmp_path()
    p.write_bytes(data)
    return m.store_upload(slot_id, p)


def test_manifest_is_valid():
    assert m.validate_manifest(m.manifest()) == []
    assert len(m.manifest()["slots"]) == 25


def test_broken_manifest_gives_errors():
    bad = copy.deepcopy(m.manifest())
    bad["slots"].append(copy.deepcopy(bad["slots"][0]))  # duplicate id
    bad["slots"][1]["kind"] = "hologram"
    bad["slots"][2]["artifact"] = "nowhere"
    game = next(s for s in bad["slots"] if s["artifact"] == "game")
    game["answer"] = None
    errors = "\n".join(m.validate_manifest(bad))
    assert "duplicate slot id" in errors
    assert "bad kind" in errors
    assert "unknown artifact" in errors
    assert "needs an answer" in errors


def test_slot_lookup_is_strict():
    assert m.slot("S11-A")["kind"] == "screenshot"
    for bad in ("", "../etc", "s11-a", "S99", "I1/", "I1\n", "S11-AA"):
        assert m.slot(bad) is None


def test_status_transitions():
    assert m.status("I1")["state"] == "mancante"
    assert m.status("I1")["file"] is None
    st = upload("I1", JPEG)
    assert st["state"] == "pronto"
    assert st["file"]["url"] == f"/admin/materials/I1/file?v={st['file']['version']}"
    assert st["file"]["removed"] == ["APP1"]
    assert m.set_skipped("I1", True)["state"] == "saltato"
    assert m.set_skipped("I1", False)["state"] == "pronto"
    assert m.delete_file("I1")["state"] == "mancante"
    assert not (m.MATERIALS_DIR / "I1").exists()


def test_required_field_makes_incomplete():
    st = upload("P1", make_png())
    assert st["state"] == "incompleto"
    st = m.set_fields("P1", {"link": "https://example.org/notizia"})
    assert st["state"] == "pronto"
    assert st["fields"] == {"link": "https://example.org/notizia"}
    # a field alone, no file: incomplete, not missing
    m.delete_file("P1")
    assert m.status("P1")["state"] == "incompleto"


def test_upload_wrong_family_limit_and_replace(monkeypatch):
    with pytest.raises(m.MaterialError) as e:
        upload("A1", make_png())
    assert e.value.status == 415
    with pytest.raises(m.MaterialError) as e:
        upload("I1", b"hello world")
    assert e.value.status == 415
    with pytest.raises(m.MaterialError) as e:
        upload("NOPE", JPEG)
    assert e.value.status == 404
    monkeypatch.setitem(m.LIMITS, "image", 10)
    with pytest.raises(m.MaterialError) as e:
        upload("I1", make_png())
    assert e.value.status == 413
    monkeypatch.setitem(m.LIMITS, "image", 15 * 2**20)
    first = upload("I1", JPEG)
    second = upload("I1", make_png(png_chunk(b"tEXt", b"k\x00v")))
    files = sorted(p.name for p in (m.MATERIALS_DIR / "I1").iterdir())
    assert files == ["file.png", "meta.json"]
    assert second["file"]["version"] != first["file"]["version"]
    assert second["file"]["removed"] == ["tEXt"]
    meta_text = (m.MATERIALS_DIR / "I1" / "meta.json").read_text()
    assert "name" not in meta_text.replace('"removed"', "")


def test_upload_failures_consume_the_temp_file():
    p = m.new_tmp_path()
    p.write_bytes(b"junk")
    with pytest.raises(m.MaterialError):
        m.store_upload("I1", p)
    assert not p.exists()


def test_store_total_cap(monkeypatch):
    upload("I1", JPEG)
    monkeypatch.setattr(m, "MAX_TOTAL_BYTES", len(JPEG) + 5)
    with pytest.raises(m.MaterialError) as e:
        upload("I3", JPEG)
    assert e.value.status == 413
    assert upload("I1", JPEG)["state"] == "pronto"  # replacing does not count twice


def test_audio_slot_accepts_ogg_and_browser_webm():
    assert upload("A1", OGG)["file"]["mime"] == "audio/ogg"
    webm = b"\x1a\x45\xdf\xa3" + b"\x00" * 30
    st = upload("A1", webm)
    assert st["file"]["mime"] == "audio/webm" and st["file"]["family"] == "audio"


def test_set_fields_validation():
    with pytest.raises(m.MaterialError) as e:
        m.set_fields("I1", {"nope": "x"})
    assert e.value.status == 400
    with pytest.raises(m.MaterialError):
        m.set_fields("I1", {"caption": "x" * 121})
    with pytest.raises(m.MaterialError) as e:
        m.set_fields("P1", {"link": "javascript:alert(1)"})
    assert "https://" in e.value.message
    m.set_fields("I1", {"caption": "  Mercato  "})
    assert m.status("I1")["fields"] == {"caption": "Mercato"}
    assert m.set_fields("I1", {"caption": ""})["fields"] == {}
    assert not (m.MATERIALS_DIR / "I1").exists()


def test_render_slots_missing_fallback_and_media():
    tag = '<rb-slot data-slot="S11-A"></rb-slot>'
    box = m.render_slots(tag, "student")
    assert 'class="slot-missing"' in box and "Materiale in arrivo" in box and "S11-A" in box
    drawn = '<rb-slot data-slot="S11-A"><p>Esempio</p></rb-slot>'
    assert m.render_slots(drawn, "admin") == "<p>Esempio</p>"
    st = upload("S11-A", make_png())
    v = st["file"]["version"]
    assert f'src="/admin/materials/S11-A/file?v={v}"' in m.render_slots(tag, "admin")
    out = m.render_slots(tag, "student")
    assert f'src="/api/live/material/S11-A?v={v}"' in out
    assert '<figure class="slot-media"><img class="slot-img"' in out
    assert 'alt="Pagina iniziale di YouTube, account A"' in out
    # skipped goes back to the fallback
    m.set_skipped("S11-A", True)
    assert "slot-missing" in m.render_slots(tag, "student")
    # video and audio
    mp4 = b"\x00\x00\x00\x14ftypisom\x00\x00\x00\x00isom" + b"\x00\x00\x00\x08free"
    upload("V1", mp4)
    assert '<video class="slot-video"' in m.render_slots(
        '<rb-slot data-slot="V1"></rb-slot>', "admin"
    )
    upload("A1", OGG)
    assert '<audio class="slot-audio"' in m.render_slots(
        "<rb-slot data-slot='A1'></rb-slot>", "admin"
    )
    # an id that is not in the manifest renders the missing box
    assert "slot-missing" in m.render_slots('<rb-slot data-slot="Z99"></rb-slot>', "admin")


def test_render_slots_fields_are_escaped_and_default_shows():
    tag = '<rb-slot data-slot="S28" data-field="caption">Didascalia di <b>prova</b></rb-slot>'
    assert m.render_slots(tag, "student") == "Didascalia di <b>prova</b>"
    m.set_fields("S28", {"caption": '<script>alert("x")</script>'})
    out = m.render_slots(tag, "student")
    assert "<script>" not in out
    assert "&lt;script&gt;" in out and "&quot;" in out


def test_slots_in_html():
    page = (
        '<rb-slot data-slot="S11-A"></rb-slot>'
        "<rb-slot data-slot='I1' data-field=\"caption\">x</rb-slot>"
    )
    assert m.slots_in_html(page) == {"S11-A", "I1"}


def test_summary_and_page_data():
    by_id = {a["id"]: a for a in m.summary()}
    assert by_id["deck-parents"]["nothingNeeded"] is True
    assert by_id["deck-main"]["total"] == 7 and by_id["deck-main"]["ready"] == 0
    upload("S11-A", make_png())
    m.set_skipped("S11-B", True)
    main = {a["id"]: a for a in m.summary()}["deck-main"]
    assert main["ready"] == 1 and main["skipped"] == 1 and main["total"] == 6
    assert "S11-A" not in main["missingIds"] and "S11-B" not in main["missingIds"]
    data = m.page_data()
    assert [s["id"] for s in data["slots"]] == [s["id"] for s in m.manifest()["slots"]]
    assert data["slots"][0]["status"]["state"] == "pronto"
    assert data["limits"] == m.LIMITS


def test_file_for_and_skipped():
    assert m.file_for("I1") is None
    upload("I1", JPEG)
    path, mime = m.file_for("I1")
    assert path.name == "file.jpg" and mime == "image/jpeg"
    m.set_skipped("I1", True)
    assert m.file_for("I1") is None
    assert m.file_for("I1", include_skipped=True) is not None
    assert m.file_for("../x") is None


def test_delete_all_and_nothing_outside_the_store(store):
    upload("I1", JPEG)
    upload("A1", OGG)
    outside = store.parent
    before = {p.name for p in outside.iterdir()}
    assert before == {"materials"}
    m.delete_all()
    assert not store.exists()
    m.delete_all()  # harmless twice
    assert m.status("I1")["state"] == "mancante"


def test_stale_tmp_files_are_swept(store):
    import os
    import time

    p = m.new_tmp_path()
    p.write_bytes(b"x")
    old = time.time() - 7200
    os.utime(p, (old, old))
    m.new_tmp_path()
    assert not p.exists()
