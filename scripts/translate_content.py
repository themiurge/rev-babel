#!/usr/bin/env python3
"""Machine-translate the lesson 8 course material (decks, game, card, hover titles).

    scripts/translate_content.py --all [--langs en,fr,ckb,kmr,ar] [--force] [--dry-run]
    scripts/translate_content.py --export-csv data/lezione8.csv
    scripts/translate_content.py --import-csv data/lezione8.csv

PRIVACY: every unit is sent to Google Cloud Translation. Only course material
the teacher wrote is ever collected here; never point this at anything a
student wrote (docs/data-and-privacy.md).

Units: each slide's ``it`` HTML in the two lesson 8 decks, every
``{"it": ...}`` text in ``vero_o_falso.json`` (but not the ``mock`` HTML, which
is a message as it arrives on a phone in Italy) and ``scheda_social.json``,
and the two hover titles in ``strings.json``. Presenter ``notes`` and
``verify`` flags are never sent.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import html
import importlib.util
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "apps" / "web" / "src" / "rev_babel_web"
DECK_SLUGS = ("lezione-8-social", "lezione-8-genitori")
LANGS = ("en", "fr", "ckb", "kmr", "ar")
UI_STRINGS = ("I social network", "Scheda da portare a casa")
SKIP_KEYS = {"mock"}
NOTE = "Machine translation, unreviewed: ask a native speaker to check before relying on it."

# Things that must come through a translation untouched.
PROTECTED = re.compile(
    r"https?://\S+|\b[\w-]+(?:\.[\w-]+)*\.(?:it|com|org|net|eu)\b|\b\d{3,}\b",
    re.IGNORECASE,
)
ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def _load_translate_module():
    spec = importlib.util.spec_from_file_location(
        "_translate", Path(__file__).with_name("translate.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Unit:
    """One Italian text, with the dict that holds its translations."""

    def __init__(self, uid: str, it: str, fmt: str, holder: dict, path: Path):
        self.id, self.it, self.fmt, self.holder, self.path = uid, it, fmt, holder, path


class _Signature(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tags: list[tuple] = []
        self.slots: list[str] = []
        self.no_text: list[str] = []
        self._no_depth: list[tuple[str, list[str]]] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self.tags.append(
            (
                tag,
                " ".join((a.get("class") or "").split()),
                a.get("data-slot"),
                a.get("data-field"),
                a.get("translate"),
            )
        )
        if tag == "rb-slot":
            self.slots.append(f"{a.get('data-slot')}/{a.get('data-field')}")
        if a.get("translate") == "no":
            self._no_depth.append((tag, []))

    def handle_endtag(self, tag):
        self.tags.append(("/" + tag,))
        if self._no_depth and self._no_depth[-1][0] == tag:
            self.no_text.append("".join(self._no_depth.pop()[1]))

    def handle_data(self, data):
        for _, parts in self._no_depth:
            parts.append(data)


def signature(markup: str) -> _Signature:
    sig = _Signature()
    sig.feed(markup)
    sig.close()
    return sig


def _protected(text: str) -> list[str]:
    plain = html.unescape(re.sub(r"<[^>]+>", " ", text)).translate(ARABIC_DIGITS)
    return sorted(m.group(0).rstrip(".,;:)»").lower() for m in PROTECTED.finditer(plain))


def validate(unit: Unit, translated: str) -> str | None:
    """None when the translation is acceptable, else the reason."""
    if not translated.strip():
        return "empty translation"
    if unit.fmt == "html":
        a, b = signature(unit.it), signature(translated)
        if a.slots != b.slots:
            return "rb-slot ids differ"
        if a.tags != b.tags:
            return "tag structure differs"
        if a.no_text != b.no_text:
            return "translate=no span changed"
    for token in _protected(unit.it):
        if token not in _protected(translated):
            return f"protected text {token!r} changed or lost"
    return None


# ---------------------------------------------------------------- collection


def _walk(node, path: str, skip=SKIP_KEYS):
    if isinstance(node, dict):
        if isinstance(node.get("it"), str):
            yield path, node
        for key, value in node.items():
            if key in skip:
                continue
            yield from _walk(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from _walk(value, f"{path}[{i}]")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def collect(web: Path = WEB) -> tuple[list[Unit], dict[Path, dict]]:
    """All units, plus the loaded document for every file they live in."""
    docs: dict[Path, dict] = {}
    units: list[Unit] = []
    for slug in DECK_SLUGS:
        path = web / "decks" / f"{slug}.json"
        docs[path] = deck = load_json(path)
        for slide in deck.get("slides", []):
            if isinstance(slide.get("it"), str):
                units.append(Unit(f"deck:{slug}:{slide['id']}", slide["it"], "html", slide, path))
    for prefix, name in (("game", "vero_o_falso.json"), ("scheda", "scheda_social.json")):
        path = web / name
        docs[path] = data = load_json(path)
        for jpath, holder in _walk(data, ""):
            units.append(Unit(f"{prefix}:{jpath}", holder["it"], "text", holder, path))
    path = web / "strings.json"
    docs[path] = strings = load_json(path)
    for key in UI_STRINGS:
        holder = strings.setdefault(key, {})
        units.append(Unit(f"ui:{key}", key, "text", holder, path))
    return units, docs


def pending(units: list[Unit], langs, force: bool):
    return [(u, lang) for u in units for lang in langs if force or not u.holder.get(lang)]


def stamp(doc: dict, path: Path) -> None:
    if path.name != "strings.json":
        doc["translation"] = {
            "by": "Google Cloud Translation",
            "reviewed": False,
            "date": datetime.date.today().isoformat(),
        }


def save(docs: dict[Path, dict], changed: set[Path]) -> None:
    for path in changed:
        if path.name == "strings.json":
            docs[path] = {k: v for k, v in docs[path].items() if v != {}}
        stamp(docs[path], path)
        path.write_text(
            json.dumps(
                docs[path], ensure_ascii=False, indent=2 if path.name == "strings.json" else 1
            )
            + "\n",
            encoding="utf-8",
        )


# ------------------------------------------------------------------- running


def run_translation(units, docs, langs, force, dry_run, translate_fn, out=print) -> dict:
    todo = pending(units, langs, force)
    chars = {lang: 0 for lang in langs}
    count = {lang: 0 for lang in langs}
    for unit, lang in todo:
        count[lang] += 1
        chars[lang] += len(unit.it)
    for lang in langs:
        out(f"{lang}: {count[lang]} units, {chars[lang]} characters")
    result = {"done": 0, "failed": [], "changed": set(), "count": count, "chars": chars}
    if dry_run or not todo:
        return result
    streak = 0
    for unit, lang in todo:
        try:
            text = translate_fn(unit.it, "it", lang, unit.fmt)
            if unit.fmt == "text":
                text = html.unescape(text)
            problem = validate(unit, text)
        except SystemExit as err:
            text, problem = "", f"API error: {err}"
        if problem:
            result["failed"].append((unit.id, lang, problem))
            out(f"REJECTED {unit.id} [{lang}]: {problem}")
            streak += 1
            if streak >= 8 and result["done"] == 0:
                out("Eight failures in a row and no success: stopping.")
                break
            continue
        streak = 0
        unit.holder[lang] = text
        result["done"] += 1
        result["changed"].add(unit.path)
    save(docs, result["changed"])
    return result


# ----------------------------------------------------------------------- CSV


def export_csv(units: list[Unit], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "it", *LANGS])
        for u in units:
            writer.writerow([u.id, u.it, *(u.holder.get(lang, "") for lang in LANGS)])


def import_csv(units, docs, source: Path, out=print) -> int:
    by_id = {u.id: u for u in units}
    changed: set[Path] = set()
    n = 0
    with source.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            unit = by_id.get(row.get("id", ""))
            if unit is None:
                out(f"unknown id {row.get('id')!r}, skipped")
                continue
            for lang in LANGS:
                value = (row.get(lang) or "").strip()
                if not value or value == unit.holder.get(lang):
                    continue
                problem = validate(unit, value)
                if problem:
                    out(f"REJECTED {unit.id} [{lang}]: {problem}")
                    continue
                unit.holder[lang] = value
                changed.add(unit.path)
                n += 1
    save(docs, changed)
    return n


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--all", action="store_true", help="translate every missing unit")
    parser.add_argument("--langs", default=",".join(LANGS))
    parser.add_argument("--force", action="store_true", help="redo existing translations")
    parser.add_argument("--dry-run", action="store_true", help="count only, send nothing")
    parser.add_argument("--export-csv", type=Path)
    parser.add_argument("--import-csv", type=Path)
    args = parser.parse_args(argv)
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]
    units, docs = collect()
    if args.export_csv:
        export_csv(units, args.export_csv)
        print(f"Wrote {len(units)} units to {args.export_csv}")
    if args.import_csv:
        print(f"Imported {import_csv(units, docs, args.import_csv)} cells")
    if args.all:
        mod = _load_translate_module()
        key = None if args.dry_run else mod.load_key()

        def fn(text, source, target, fmt):
            return mod.translate(text, source, target, fmt, key)

        result = run_translation(units, docs, langs, args.force, args.dry_run, fn)
        print(f"Translated {result['done']} cells; {len(result['failed'])} rejected.")
        for uid, lang, why in result["failed"]:
            print(f"  - {uid} [{lang}]: {why}")
    if not (args.all or args.export_csv or args.import_csv):
        parser.error("nothing to do: pass --all, --export-csv or --import-csv")
    print(NOTE)


if __name__ == "__main__":
    main()
