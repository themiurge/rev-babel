"""Tests for media_clean: sniffing and metadata stripping, on invented bytes."""

import struct
import zlib

import pytest
from rev_babel_web import media_clean as mc


def seg(marker: int, payload: bytes) -> bytes:
    return bytes([0xFF, marker]) + struct.pack(">H", len(payload) + 2) + payload


def make_jpeg() -> bytes:
    return (
        b"\xff\xd8"
        + seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00")
        + seg(0xE1, b"Exif\x00\x00GPS")
        + seg(0xE2, b"ICC_PROFILE\x00abc")
        + seg(0xFE, b"a comment")
        + seg(0xDB, b"\x00" + b"\x10" * 64)
        + b"\xff\xda\x00\x02scan-data\xff\xd9"
    )


def png_chunk(ctype: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(ctype + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + ctype + data + struct.pack(">I", crc)


def riff_chunk(fourcc: bytes, payload: bytes) -> bytes:
    pad = b"\x00" if len(payload) & 1 else b""
    return fourcc + struct.pack("<I", len(payload)) + payload + pad


def riff(form: bytes, *chunks: bytes) -> bytes:
    body = form + b"".join(chunks)
    return b"RIFF" + struct.pack("<I", len(body)) + body


def box(btype: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload) + 8) + btype + payload


def test_sniff_table():
    assert mc.sniff(b"\xff\xd8\xff\xe0") == ("image", "image/jpeg", ".jpg")
    assert mc.sniff(b"\x89PNG\r\n\x1a\n....") == ("image", "image/png", ".png")
    assert mc.sniff(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == ("image", "image/webp", ".webp")
    assert mc.sniff(b"\x00\x00\x00\x18ftypM4A \x00") == ("av", "audio/mp4", ".m4a")
    assert mc.sniff(b"\x00\x00\x00\x18ftypM4B \x00") == ("av", "audio/mp4", ".m4a")
    assert mc.sniff(b"\x00\x00\x00\x18ftypisom\x00") == ("av", "video/mp4", ".mp4")
    assert mc.sniff(b"\x00\x00\x00\x14ftypqt  \x00") == ("av", "video/mp4", ".mp4")
    assert mc.sniff(b"\x1a\x45\xdf\xa3\x01") == ("av", "video/webm", ".webm")
    assert mc.sniff(b"OggS\x00") == ("audio", "audio/ogg", ".ogg")
    assert mc.sniff(b"RIFF\x00\x00\x00\x00WAVEfmt ") == ("audio", "audio/wav", ".wav")
    assert mc.sniff(b"ID3\x04\x00") == ("audio", "audio/mpeg", ".mp3")
    assert mc.sniff(b"\xff\xfb\x90\x00") == ("audio", "audio/mpeg", ".mp3")


@pytest.mark.parametrize("brand", [b"heic", b"heix", b"mif1", b"avif", b"hevc"])
def test_sniff_refuses_heic_and_avif(brand):
    with pytest.raises(mc.Unsupported, match="HEIC"):
        mc.sniff(b"\x00\x00\x00\x18ftyp" + brand + b"\x00")


def test_sniff_refuses_unknown():
    with pytest.raises(mc.Unsupported):
        mc.sniff(b"hello world, not media")
    with pytest.raises(mc.Unsupported):
        mc.sniff(b"")


def test_strip_jpeg_drops_app1_and_com_keeps_the_rest():
    data = make_jpeg()
    out, removed = mc.strip_jpeg(data)
    assert removed == ["APP1", "COM"]
    assert b"Exif" not in out and b"a comment" not in out
    assert out.startswith(b"\xff\xd8" + seg(0xE0, b"JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"))
    assert seg(0xE2, b"ICC_PROFILE\x00abc") in out
    assert out.endswith(b"\xff\xda\x00\x02scan-data\xff\xd9")


def test_strip_jpeg_keeps_adobe_and_drops_other_icc_less_app2():
    data = b"\xff\xd8" + seg(0xEE, b"Adobe") + seg(0xE2, b"MPF\x00") + b"\xff\xda\x00\x02x"
    out, removed = mc.strip_jpeg(data)
    assert seg(0xEE, b"Adobe") in out
    assert removed == ["APP2"]


def test_strip_jpeg_truncated_segment_raises():
    data = b"\xff\xd8" + b"\xff\xe1\x00\xff" + b"short"
    with pytest.raises(mc.Unsupported):
        mc.strip_jpeg(data)


def test_strip_png_keeps_only_critical_chunks():
    ihdr = png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    idat = png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00"))
    iend = png_chunk(b"IEND", b"")
    data = (
        mc._PNG_SIG
        + ihdr
        + png_chunk(b"tEXt", b"Comment\x00gps")
        + png_chunk(b"eXIf", b"MM\x00*")
        + idat
        + png_chunk(b"tIME", b"\x07\xea\x0b\x10\x00\x00\x00")
        + iend
    )
    out, removed = mc.strip_png(data)
    assert out == mc._PNG_SIG + ihdr + idat + iend
    assert removed == ["tEXt", "eXIf", "tIME"]


def test_strip_webp_drops_exif_xmp_and_clears_flags():
    vp8x = riff_chunk(b"VP8X", bytes([0x2C]) + b"\x00" * 9)  # ICC, EXIF, XMP flags
    data = riff(
        b"WEBP",
        vp8x,
        riff_chunk(b"VP8 ", b"pixel"),
        riff_chunk(b"EXIF", b"gps"),
        riff_chunk(b"XMP ", b"xm"),
    )
    out, removed = mc.strip_webp(data)
    assert removed == ["EXIF", "XMP"]
    assert b"gps" not in out and b"xm" not in out.replace(b"VP8X", b"")
    assert out[:4] == b"RIFF" and struct.unpack("<I", out[4:8])[0] == len(out) - 8
    vp8x_at = out.index(b"VP8X") + 8
    assert out[vp8x_at] == 0x20  # ICC flag stays, EXIF and XMP flags cleared


def test_strip_mp3_removes_id3v2_with_footer_and_id3v1():
    frame = b"\xff\xfb\x90\x00" + b"\x00" * 40
    tag = b"ID3\x04\x00\x10" + bytes([0, 0, 0, 5]) + b"abcde" + b"3DI\x04\x00\x10" + b"\x00" * 4
    v1 = b"TAG" + b"\x00" * 125
    out, removed = mc.strip_mp3(tag + frame + v1)
    assert out == frame
    assert removed == ["ID3v2", "ID3v1"]


def test_strip_mp3_needs_frame_sync():
    with pytest.raises(mc.Unsupported):
        mc.strip_mp3(b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"not audio")


def test_strip_wav_drops_list_chunk():
    fmt = riff_chunk(b"fmt ", b"\x01\x00\x01\x00" + b"\x00" * 12)
    data_chunk = riff_chunk(b"data", b"\x01\x02\x03")  # odd length, padded
    data = riff(b"WAVE", fmt, riff_chunk(b"LIST", b"INFOICMT\x04\x00\x00\x00abc\x00"), data_chunk)
    out, removed = mc.strip_wav(data)
    assert removed == ["LIST"]
    assert out == riff(b"WAVE", fmt, data_chunk)
    assert struct.unpack("<I", out[4:8])[0] == len(out) - 8


def test_neutralise_mp4(tmp_path):
    mvhd = box(b"mvhd", b"M" * 20)
    udta = box(b"udta", box(b"\xa9xyz", b"+45.0+009.0/"))
    tkhd = box(b"tkhd", b"T" * 12)
    meta = box(b"meta", b"\x00\x00\x00\x00hdlr-secret")
    moov = box(b"moov", mvhd + udta + box(b"trak", tkhd + meta))
    mdat = box(b"mdat", b"media-bytes" * 5)
    uuid_box = box(b"uuid", b"U" * 20)
    original = box(b"ftyp", b"isom\x00\x00\x02\x00isom") + moov + mdat + uuid_box
    p = tmp_path / "v.mp4"
    p.write_bytes(original)
    removed = mc.neutralise_mp4(p)
    out = p.read_bytes()
    assert sorted(removed) == ["meta", "udta", "uuid"]
    assert len(out) == len(original)
    assert b"+45.0" not in out and b"secret" not in out and b"U" * 20 not in out
    for kept in (mvhd, tkhd, mdat):
        assert kept in out
    start = original.index(b"udta") - 4
    assert out[start + 4 : start + 8] == b"free"
    assert set(out[start + 8 : start + len(udta)]) == {0}


def test_neutralise_mp4_oversized_box_raises(tmp_path):
    p = tmp_path / "bad.mp4"
    p.write_bytes(
        box(b"ftyp", b"isom\x00\x00\x00\x00") + struct.pack(">I", 9999) + b"moov" + b"x" * 8
    )
    with pytest.raises(mc.Unsupported):
        mc.neutralise_mp4(p)


def test_neutralise_mp4_needs_ftyp_first(tmp_path):
    p = tmp_path / "bad.mp4"
    p.write_bytes(box(b"moov", b"x" * 8))
    with pytest.raises(mc.Unsupported):
        mc.neutralise_mp4(p)


def test_clean_file_rewrites_in_place_and_ignores_ogg(tmp_path):
    p = tmp_path / "a.jpg"
    p.write_bytes(make_jpeg())
    assert mc.clean_file(p, "image/jpeg") == ["APP1", "COM"]
    assert b"Exif" not in p.read_bytes()
    assert not list(tmp_path.glob("*.clean"))
    o = tmp_path / "a.ogg"
    o.write_bytes(b"OggS-data")
    assert mc.clean_file(o, "audio/ogg") == []
    assert o.read_bytes() == b"OggS-data"
