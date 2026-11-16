"""Lesson 8's materials store: real photos, screenshots, video and voice
that the teacher provides for the decks and the game.

Files live under data/materials/<SLOT>/ (gitignored, never in version
control), one cleaned file plus a meta.json per slot. The committed
materials_manifest.json lists every slot that can be filled; nothing else
can be uploaded. Metadata is stripped by media_clean.py before a file is
kept. See docs/decisions/0020-lesson-8-materials-store-and-game.md and
plans/lezione-8-social.md section 4.

The HTTP routes live in main.py; this module is pure storage and
rendering. It holds no state in memory beyond per-slot write locks, so
like the rest of the app it assumes a single uvicorn worker.
"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import shutil
import threading
import time
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path

from . import media_clean

# Read through the module global at call time so tests can monkeypatch it.
MATERIALS_DIR = Path(os.environ.get("DATA_DIR", "data")) / "materials"
MANIFEST_PATH = Path(__file__).parent / "materials_manifest.json"

SLOT_ID_RE = re.compile(r"^[A-Z][0-9]{1,2}(?:-[A-Z])?$")
SLOT_TAG_RE = re.compile(
    r"<rb-slot data-slot=([\"'])(?P<id>[A-Z][0-9]{1,2}(?:-[A-Z])?)\1"
    r"(?: data-field=([\"'])(?P<field>[a-z_]{1,20})\3)?>(?P<inner>.*?)</rb-slot>",
    re.DOTALL,
)
KIND_FAMILY = {"image": "image", "screenshot": "image", "video": "video", "audio": "audio"}
LIMITS = {"image": 15 * 2**20, "video": 90 * 2**20, "audio": 20 * 2**20}
MAX_UPLOAD_BYTES = max(LIMITS.values())
MAX_TOTAL_BYTES = 2 * 2**30
ADMIN_FILE_URL = "/admin/materials/{id}/file?v={v}"
STUDENT_FILE_URL = "/api/live/material/{id}?v={v}"
STATES = ("mancante", "incompleto", "pronto", "saltato")

NEEDED = ("required", "fallback", "optional")
ANSWERS = ("vero", "falso_ia", "truffa", "verificare")
FIELD_TYPES = ("text", "url")
URL_RE = re.compile(r"^https?://\S+$")
TMP_MAX_AGE = 3600

_locks: dict[str, threading.RLock] = {}
_locks_guard = threading.Lock()


class MaterialError(Exception):
    """`.status` is the HTTP code, `.message` is Italian, shown to the teacher."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


# --- manifest ---------------------------------------------------------------


@lru_cache(maxsize=1)
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def validate_manifest(data: dict) -> list[str]:
    """Return a list of problems; [] when the manifest is valid."""
    errors: list[str] = []
    artifacts = data.get("artifacts")
    slots = data.get("slots")
    if not isinstance(artifacts, list) or not isinstance(slots, list):
        return ["artifacts and slots must be lists"]
    artifact_ids: set[str] = set()
    for a in artifacts:
        aid = a.get("id")
        if not aid or aid in artifact_ids:
            errors.append(f"artifact id missing or duplicate: {aid!r}")
        artifact_ids.add(aid)
        if not a.get("title"):
            errors.append(f"artifact {aid}: no title")
    seen: set[str] = set()
    for s in slots:
        sid = s.get("id", "")
        if not isinstance(sid, str) or not SLOT_ID_RE.match(sid):
            errors.append(f"bad slot id: {sid!r}")
        if sid in seen:
            errors.append(f"duplicate slot id: {sid}")
        seen.add(sid)
        if s.get("artifact") not in artifact_ids:
            errors.append(f"{sid}: unknown artifact {s.get('artifact')!r}")
        if s.get("kind") not in KIND_FAMILY:
            errors.append(f"{sid}: bad kind {s.get('kind')!r}")
        if s.get("needed") not in NEEDED:
            errors.append(f"{sid}: bad needed {s.get('needed')!r}")
        for key in ("where", "title", "alt"):
            if not s.get(key):
                errors.append(f"{sid}: no {key}")
        if not s.get("instructions"):
            errors.append(f"{sid}: no instructions")
        if not isinstance(s.get("safety"), list):
            errors.append(f"{sid}: safety must be a list")
        if not isinstance(s.get("noFaces"), bool):
            errors.append(f"{sid}: noFaces must be a boolean")
        if s.get("artifact") == "game":
            if s.get("answer") not in ANSWERS:
                errors.append(f"{sid}: game slot needs an answer in {ANSWERS}")
        elif s.get("answer") is not None:
            errors.append(f"{sid}: only game slots have an answer")
        keys: set[str] = set()
        for fld in s.get("fields", []):
            k = fld.get("key", "")
            if not re.fullmatch(r"[a-z_]{1,20}", k) or k in keys:
                errors.append(f"{sid}: bad or duplicate field key {k!r}")
            keys.add(k)
            if fld.get("type") not in FIELD_TYPES:
                errors.append(f"{sid}.{k}: bad field type {fld.get('type')!r}")
            if not isinstance(fld.get("max"), int) or fld["max"] < 1:
                errors.append(f"{sid}.{k}: bad max")
            if not isinstance(fld.get("required"), bool):
                errors.append(f"{sid}.{k}: required must be a boolean")
            if not fld.get("label"):
                errors.append(f"{sid}.{k}: no label")
    return errors


def slot(slot_id: str) -> dict | None:
    """The manifest slot, or None unless the id is well formed and listed."""
    if not isinstance(slot_id, str) or not SLOT_ID_RE.match(slot_id):
        return None
    for s in manifest()["slots"]:
        if s["id"] == slot_id:
            return s
    return None


def _require_slot(slot_id: str) -> dict:
    s = slot(slot_id)
    if s is None:
        raise MaterialError(404, "Materiale sconosciuto.")
    return s


def limit_for(slot_id: str) -> int:
    return LIMITS[KIND_FAMILY[_require_slot(slot_id)["kind"]]]


# --- meta on disk -----------------------------------------------------------


def _lock(slot_id: str) -> threading.RLock:
    with _locks_guard:
        return _locks.setdefault(slot_id, threading.RLock())


def _slot_dir(slot_id: str) -> Path:
    return MATERIALS_DIR / slot_id


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _read_meta(slot_id: str) -> dict:
    try:
        meta = json.loads((_slot_dir(slot_id) / "meta.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    meta.setdefault("file", None)
    meta.setdefault("fields", {})
    meta.setdefault("skipped", False)
    return meta


def _write_meta(slot_id: str, meta: dict) -> None:
    d = _slot_dir(slot_id)
    d.mkdir(parents=True, exist_ok=True)
    meta["updated"] = _now()
    tmp = d / "meta.json.tmp"
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, d / "meta.json")


def _remove_files(slot_id: str) -> None:
    d = _slot_dir(slot_id)
    if d.is_dir():
        for p in d.glob("file.*"):
            p.unlink(missing_ok=True)


def _tidy(slot_id: str, meta: dict) -> dict:
    """Write meta, or remove the slot's folder if nothing is left in it."""
    if not meta["file"] and not meta["fields"] and not meta["skipped"]:
        shutil.rmtree(_slot_dir(slot_id), ignore_errors=True)
    else:
        _write_meta(slot_id, meta)
    return status(slot_id)


# --- status -----------------------------------------------------------------


def status(slot_id: str) -> dict:
    s = _require_slot(slot_id)
    meta = _read_meta(slot_id)
    f = meta["file"]
    if f and not (_slot_dir(slot_id) / f"file{f['ext']}").is_file():
        f = None
    fields = {k: v for k, v in meta["fields"].items() if isinstance(v, str) and v}
    required_ok = all(fields.get(fd["key"]) for fd in s.get("fields", []) if fd.get("required"))
    if meta["skipped"]:
        state = "saltato"
    elif f and required_ok:
        state = "pronto"
    elif f or fields:
        state = "incompleto"
    else:
        state = "mancante"
    file_info = None
    if f:
        file_info = {
            "family": f["family"],
            "mime": f["mime"],
            "size": f["size"],
            "version": f["version"],
            "uploaded": f["uploaded"],
            "removed": f.get("removed", []),
            "url": ADMIN_FILE_URL.format(id=slot_id, v=f["version"]),
        }
    return {
        "id": slot_id,
        "state": state,
        "skipped": bool(meta["skipped"]),
        "file": file_info,
        "fields": fields,
        "updated": meta.get("updated"),
    }


def all_status() -> list[dict]:
    return [status(s["id"]) for s in manifest()["slots"]]


def summary() -> list[dict]:
    by_id = {st["id"]: st for st in all_status()}
    out = []
    for a in manifest()["artifacts"]:
        mine = [s["id"] for s in manifest()["slots"] if s["artifact"] == a["id"]]
        live = [i for i in mine if by_id[i]["state"] != "saltato"]
        counts = {k: sum(1 for i in live if by_id[i]["state"] == k) for k in STATES}
        out.append(
            {
                "id": a["id"],
                "title": a["title"],
                "total": len(live),
                "ready": counts["pronto"],
                "missing": counts["mancante"],
                "incomplete": counts["incompleto"],
                "skipped": len(mine) - len(live),
                "missingIds": [i for i in live if by_id[i]["state"] in ("mancante", "incompleto")],
                "nothingNeeded": not mine,
            }
        )
    return out


def page_data() -> dict:
    by_id = {st["id"]: st for st in all_status()}
    return {
        "artifacts": summary(),
        "slots": [{**s, "status": by_id[s["id"]]} for s in manifest()["slots"]],
        "limits": LIMITS,
    }


# --- uploads ----------------------------------------------------------------


def new_tmp_path() -> Path:
    """A fresh path under .tmp for a streamed upload; sweeps stale leftovers."""
    tmp_dir = MATERIALS_DIR / ".tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    cutoff = time.time() - TMP_MAX_AGE
    for p in tmp_dir.iterdir():
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink()
        except OSError:
            pass
    return tmp_dir / uuid.uuid4().hex


def _store_bytes(exclude_slot: str) -> int:
    total = 0
    if MATERIALS_DIR.is_dir():
        for d in MATERIALS_DIR.iterdir():
            if d.name.startswith(".") or d.name == exclude_slot or not d.is_dir():
                continue
            for p in d.glob("file.*"):
                total += p.stat().st_size
    return total


_WANTS = {"image": "una foto", "video": "un video", "audio": "un audio"}


def store_upload(slot_id: str, tmp_path: Path) -> dict:
    """Check, clean and keep an uploaded file; the temp file is always consumed."""
    try:
        return _store_upload(slot_id, tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)


def _store_upload(slot_id: str, tmp_path: Path) -> dict:
    s = _require_slot(slot_id)
    with open(tmp_path, "rb") as fh:
        head = fh.read(64)
    try:
        family, mime, ext = media_clean.sniff(head)
    except media_clean.Unsupported as e:
        raise MaterialError(415, e.message) from e
    slot_family = KIND_FAMILY[s["kind"]]
    fits = (
        (slot_family == "image" and family == "image")
        or (slot_family == "video" and family == "av")
        or (slot_family == "audio" and family in ("audio", "av"))
    )
    if not fits:
        raise MaterialError(415, f"Questo spazio vuole {_WANTS[slot_family]}.")
    if family == "av" and slot_family == "audio":
        mime = "audio/webm" if mime == "video/webm" else "audio/mp4"
        family = "audio"
    elif family == "av":
        family = "video"
    size = tmp_path.stat().st_size
    limit = limit_for(slot_id)
    if size > limit:
        raise MaterialError(413, f"File troppo grande: massimo {limit // 2**20} MB.")
    if _store_bytes(slot_id) + size > MAX_TOTAL_BYTES:
        raise MaterialError(413, "Spazio finito: elimina qualche file.")
    try:
        removed = media_clean.clean_file(tmp_path, mime)
    except media_clean.Unsupported as e:
        raise MaterialError(415, e.message) from e
    digest = hashlib.sha256()
    with open(tmp_path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    with _lock(slot_id):
        meta = _read_meta(slot_id)
        _remove_files(slot_id)
        _slot_dir(slot_id).mkdir(parents=True, exist_ok=True)
        os.replace(tmp_path, _slot_dir(slot_id) / f"file{ext}")
        meta["file"] = {
            "family": family,
            "mime": mime,
            "ext": ext,
            "size": (_slot_dir(slot_id) / f"file{ext}").stat().st_size,
            "version": digest.hexdigest()[:12],
            "uploaded": _now(),
            "removed": removed,
        }
        meta["skipped"] = False
        _write_meta(slot_id, meta)
    return status(slot_id)


def delete_file(slot_id: str) -> dict:
    _require_slot(slot_id)
    with _lock(slot_id):
        meta = _read_meta(slot_id)
        _remove_files(slot_id)
        meta["file"] = None
        return _tidy(slot_id, meta)


def set_fields(slot_id: str, values: dict[str, str]) -> dict:
    s = _require_slot(slot_id)
    defs = {fd["key"]: fd for fd in s.get("fields", [])}
    clean: dict[str, str] = {}
    for key, raw in values.items():
        fd = defs.get(key)
        if fd is None:
            raise MaterialError(400, "Campo sconosciuto.")
        value = (raw if isinstance(raw, str) else "").strip()
        if len(value) > fd["max"]:
            raise MaterialError(400, f"Testo troppo lungo: massimo {fd['max']} caratteri.")
        if value and fd["type"] == "url" and not URL_RE.match(value):
            raise MaterialError(400, "Il link deve iniziare con https://")
        clean[key] = value
    with _lock(slot_id):
        meta = _read_meta(slot_id)
        for key, value in clean.items():
            if value:
                meta["fields"][key] = value
            else:
                meta["fields"].pop(key, None)
        return _tidy(slot_id, meta)


def set_skipped(slot_id: str, skipped: bool) -> dict:
    _require_slot(slot_id)
    with _lock(slot_id):
        meta = _read_meta(slot_id)
        meta["skipped"] = bool(skipped)
        return _tidy(slot_id, meta)


def delete_all() -> None:
    shutil.rmtree(MATERIALS_DIR, ignore_errors=True)


def file_for(slot_id: str, include_skipped: bool = False) -> tuple[Path, str] | None:
    """(path, mime) of the stored file, or None. A skipped slot has no file
    for students or the game unless `include_skipped` (the teacher's preview)."""
    if slot(slot_id) is None:
        return None
    meta = _read_meta(slot_id)
    f = meta["file"]
    if not f or (meta["skipped"] and not include_skipped):
        return None
    path = _slot_dir(slot_id) / f"file{f['ext']}"
    if not path.is_file():
        return None
    return path, f["mime"]


# --- rendering into deck HTML -----------------------------------------------


def slots_in_html(html_text: str) -> set[str]:
    return {m.group("id") for m in SLOT_TAG_RE.finditer(html_text)}


def _missing_box(slot_id: str) -> str:
    return (
        '<div class="slot-missing"><span class="slot-missing-emoji">📦</span>'
        f"Materiale in arrivo<small>{html.escape(slot_id)}</small></div>"
    )


def render_slots(html_text: str, audience: str) -> str:
    """Replace every <rb-slot> with its media, its teacher text or its fallback."""
    url_tpl = STUDENT_FILE_URL if audience == "student" else ADMIN_FILE_URL

    def one(m: re.Match) -> str:
        sid = m.group("id")
        inner = m.group("inner")
        s = slot(sid)
        if s is None:
            return _missing_box(sid)
        st = status(sid)
        field = m.group("field")
        if field:
            value = st["fields"].get(field)
            return html.escape(value, quote=True) if value else inner
        f = st["file"]
        if f and not st["skipped"]:
            url = html.escape(url_tpl.format(id=sid, v=f["version"]), quote=True)
            alt = html.escape(s["alt"], quote=True)
            if f["family"] == "image":
                body = f'<img class="slot-img" src="{url}" alt="{alt}">'
            elif f["family"] == "video":
                body = (
                    f'<video class="slot-video" src="{url}" controls playsinline '
                    'preload="metadata"></video>'
                )
            else:
                body = f'<audio class="slot-audio" src="{url}" controls preload="metadata"></audio>'
            return f'<figure class="slot-media">{body}</figure>'
        return inner if inner.strip() else _missing_box(sid)

    return SLOT_TAG_RE.sub(one, html_text)
