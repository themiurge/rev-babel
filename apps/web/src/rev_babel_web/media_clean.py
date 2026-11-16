"""Identify uploaded media by their first bytes and strip hidden metadata.

Used by the lesson 8 materials store (materials.py, ADR 0020). The teacher
uploads photos, screenshots, video and voice from a phone; phones put GPS
coordinates and dates in those files. Nothing here needs a dependency:
every format is handled by walking its container structure with the
standard library, so the cleaning is easy to read and to test with
invented bytes.

Images are re-encoded in the browser as well (which already drops
metadata); this module is the server-side guarantee for what the browser
could not re-encode (video, audio, an original sent after a decode failure).
"""

from __future__ import annotations

import os
import struct
from pathlib import Path


class Unsupported(Exception):
    """The file cannot be accepted. `.message` is Italian, shown to the teacher."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


MSG_UNKNOWN = (
    "Tipo di file non riconosciuto. Vanno bene: foto JPG o PNG, video MP4, "
    "audio MP3, M4A, OGG o WAV."
)
MSG_HEIC = (
    "Foto HEIC o AVIF: sul telefono scegli «Più compatibile», oppure carica "
    "la foto da questa pagina con 📷."
)
MSG_DAMAGED = "File rovinato o incompleto."
MSG_DAMAGED_VIDEO = "File video rovinato o incompleto."

_HEIC_BRANDS = {b"heic", b"heix", b"heim", b"heis", b"hevc", b"hevx", b"mif1", b"msf1", b"avif"}
_AUDIO_BRANDS = {b"M4A ", b"M4B "}


def sniff(head: bytes) -> tuple[str, str, str]:
    """Return (family, mime, extension) from the first bytes. First match wins."""
    if head[:3] == b"\xff\xd8\xff":
        return ("image", "image/jpeg", ".jpg")
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        return ("image", "image/png", ".png")
    if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return ("image", "image/webp", ".webp")
    if head[4:8] == b"ftyp":
        brand = head[8:12]
        if brand in _HEIC_BRANDS:
            raise Unsupported(MSG_HEIC)
        if brand in _AUDIO_BRANDS:
            return ("av", "audio/mp4", ".m4a")
        return ("av", "video/mp4", ".mp4")
    if head[:4] == b"\x1a\x45\xdf\xa3":
        return ("av", "video/webm", ".webm")
    if head[:4] == b"OggS":
        return ("audio", "audio/ogg", ".ogg")
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return ("audio", "audio/wav", ".wav")
    if head[:3] == b"ID3" or (len(head) >= 2 and head[0] == 0xFF and head[1] & 0xE0 == 0xE0):
        return ("audio", "audio/mpeg", ".mp3")
    raise Unsupported(MSG_UNKNOWN)


# --- JPEG -------------------------------------------------------------------


def strip_jpeg(data: bytes) -> tuple[bytes, list[str]]:
    """Drop APP1-APP15 and COM segments, except the ICC profile and Adobe."""
    if data[:2] != b"\xff\xd8":
        raise Unsupported(MSG_DAMAGED)
    out = bytearray(data[:2])
    removed: list[str] = []
    i = 2
    n = len(data)
    while i < n:
        if data[i] != 0xFF:
            raise Unsupported(MSG_DAMAGED)
        if i + 1 >= n:
            raise Unsupported(MSG_DAMAGED)
        marker = data[i + 1]
        if marker == 0xFF:  # fill byte before a marker
            out.append(0xFF)
            i += 1
            continue
        if marker == 0x01 or 0xD0 <= marker <= 0xD7:  # standalone markers
            out += data[i : i + 2]
            i += 2
            continue
        if marker == 0xDA or marker == 0xD9:  # start of scan / end of image
            out += data[i:]
            return bytes(out), removed
        if i + 4 > n:
            raise Unsupported(MSG_DAMAGED)
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        end = i + 2 + length
        if length < 2 or end > n:
            raise Unsupported(MSG_DAMAGED)
        payload = data[i + 4 : end]
        keep = True
        if 0xE1 <= marker <= 0xEF or marker == 0xFE:
            keep = (marker == 0xE2 and payload.startswith(b"ICC_PROFILE\x00")) or marker == 0xEE
        if keep:
            out += data[i:end]
        else:
            removed.append("COM" if marker == 0xFE else f"APP{marker - 0xE0}")
        i = end
    # No start-of-scan seen: nothing to show, so the file is damaged.
    raise Unsupported(MSG_DAMAGED)


# --- PNG --------------------------------------------------------------------

_PNG_SIG = b"\x89PNG\r\n\x1a\n"
_PNG_KEEP = {
    b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"cHRM", b"gAMA", b"iCCP",
    b"sBIT", b"sRGB", b"bKGD", b"pHYs", b"acTL", b"fcTL", b"fdAT", b"cICP",
}  # fmt: skip


def strip_png(data: bytes) -> tuple[bytes, list[str]]:
    """Drop ancillary chunks that can carry text, dates or EXIF."""
    if data[:8] != _PNG_SIG:
        raise Unsupported(MSG_DAMAGED)
    out = bytearray(_PNG_SIG)
    removed: list[str] = []
    i = 8
    n = len(data)
    while i < n:
        if i + 8 > n:
            raise Unsupported(MSG_DAMAGED)
        length = struct.unpack(">I", data[i : i + 4])[0]
        ctype = data[i + 4 : i + 8]
        end = i + 12 + length
        if end > n:
            raise Unsupported(MSG_DAMAGED)
        if ctype in _PNG_KEEP:
            out += data[i:end]
        else:
            removed.append(ctype.decode("latin-1"))
        i = end
    return bytes(out), removed


# --- RIFF: WebP and WAV -----------------------------------------------------


def _riff_chunks(data: bytes, form: bytes) -> list[tuple[bytes, bytes]]:
    if len(data) < 12 or data[:4] != b"RIFF" or data[8:12] != form:
        raise Unsupported(MSG_DAMAGED)
    chunks: list[tuple[bytes, bytes]] = []
    i = 12
    n = len(data)
    while i < n:
        if i + 8 > n:
            raise Unsupported(MSG_DAMAGED)
        fourcc = data[i : i + 4]
        size = struct.unpack("<I", data[i + 4 : i + 8])[0]
        end = i + 8 + size
        if end > n:
            raise Unsupported(MSG_DAMAGED)
        chunks.append((fourcc, data[i + 8 : end]))
        i = end + (size & 1)  # chunks are padded to an even length
    return chunks


def _riff_build(form: bytes, chunks: list[tuple[bytes, bytes]]) -> bytes:
    body = bytearray(form)
    for fourcc, payload in chunks:
        body += fourcc + struct.pack("<I", len(payload)) + payload
        if len(payload) & 1:
            body += b"\x00"
    return b"RIFF" + struct.pack("<I", len(body)) + bytes(body)


def strip_webp(data: bytes) -> tuple[bytes, list[str]]:
    kept: list[tuple[bytes, bytes]] = []
    removed: list[str] = []
    for fourcc, payload in _riff_chunks(data, b"WEBP"):
        if fourcc in (b"EXIF", b"XMP "):
            removed.append(fourcc.decode("latin-1").strip())
            continue
        if fourcc == b"VP8X" and payload:
            payload = bytes([payload[0] & ~0x0C & 0xFF]) + payload[1:]
        kept.append((fourcc, payload))
    return _riff_build(b"WEBP", kept), removed


def strip_wav(data: bytes) -> tuple[bytes, list[str]]:
    kept: list[tuple[bytes, bytes]] = []
    removed: list[str] = []
    for fourcc, payload in _riff_chunks(data, b"WAVE"):
        if fourcc in (b"fmt ", b"data", b"fact"):
            kept.append((fourcc, payload))
        else:
            removed.append(fourcc.decode("latin-1").strip())
    return _riff_build(b"WAVE", kept), removed


# --- MP3 --------------------------------------------------------------------


def strip_mp3(data: bytes) -> tuple[bytes, list[str]]:
    removed: list[str] = []
    while data[:3] == b"ID3":
        if len(data) < 10:
            raise Unsupported(MSG_DAMAGED)
        size = 0
        for b in data[6:10]:
            size = (size << 7) | (b & 0x7F)
        total = 10 + size + (10 if data[5] & 0x10 else 0)
        if total > len(data):
            raise Unsupported(MSG_DAMAGED)
        data = data[total:]
        removed.append("ID3v2")
    if len(data) >= 128 and data[-128:-125] == b"TAG":
        data = data[:-128]
        removed.append("ID3v1")
    if len(data) < 2 or data[0] != 0xFF or data[1] & 0xE0 != 0xE0:
        raise Unsupported(MSG_DAMAGED)
    return data, removed


# --- MP4 / MOV / M4A --------------------------------------------------------

_MP4_CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"edts"}
_MP4_SECRET = {b"udta", b"meta", b"uuid"}
_ZEROS = b"\x00" * (1 << 20)


def neutralise_mp4(path: Path) -> list[str]:
    """Overwrite udta/meta/uuid boxes with zeroed `free` boxes, in place.

    Sizes and offsets never change, so the file still plays. Streams the
    file: never loads it whole.
    """
    removed: list[str] = []
    with open(path, "r+b") as f:
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(4)
        if f.read(4) != b"ftyp":
            raise Unsupported(MSG_DAMAGED_VIDEO)
        _walk_boxes(f, 0, size, removed, top=True)
    return removed


def _walk_boxes(f, start: int, end: int, removed: list[str], top: bool = False) -> None:
    pos = start
    while end - pos >= 8:
        f.seek(pos)
        head = f.read(8)
        if len(head) < 8:
            raise Unsupported(MSG_DAMAGED_VIDEO)
        size = struct.unpack(">I", head[:4])[0]
        btype = head[4:8]
        header = 8
        if size == 1:
            ext = f.read(8)
            if len(ext) < 8:
                raise Unsupported(MSG_DAMAGED_VIDEO)
            size = struct.unpack(">Q", ext)[0]
            header = 16
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            raise Unsupported(MSG_DAMAGED_VIDEO)
        if btype in _MP4_SECRET:
            f.seek(pos + 4)
            f.write(b"free")
            f.seek(pos + header)
            left = size - header
            while left > 0:
                chunk = min(left, len(_ZEROS))
                f.write(_ZEROS[:chunk])
                left -= chunk
            name = btype.decode("latin-1")
            if name not in removed:
                removed.append(name)
        elif btype in _MP4_CONTAINERS:
            _walk_boxes(f, pos + header, pos + size, removed)
        pos += size


# --- entry point ------------------------------------------------------------


def clean_file(path: Path, mime: str) -> list[str]:
    """Clean `path` in place for its mime type; return what was removed."""
    if mime in ("video/mp4", "audio/mp4"):
        return neutralise_mp4(path)
    stripper = {
        "image/jpeg": strip_jpeg,
        "image/png": strip_png,
        "image/webp": strip_webp,
        "audio/mpeg": strip_mp3,
        "audio/wav": strip_wav,
    }.get(mime)
    if stripper is None:  # Ogg and WebM recordings carry no location
        return []
    cleaned, removed = stripper(path.read_bytes())
    tmp = path.with_name(path.name + ".clean")
    tmp.write_bytes(cleaned)
    os.replace(tmp, path)
    return removed
