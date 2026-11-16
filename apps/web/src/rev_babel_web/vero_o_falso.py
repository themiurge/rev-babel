"""Lesson 8's game "Vero o falso?": content, scoring and the page config.

The teacher drives the game on the projector; students vote with four
coloured paper cards. The scoring rule lives here (`points`) and is shipped
to the page as a per-item table, so game.js only adds numbers. Media come
from the materials store (status dicts passed in by main.py); an item
without its file falls back to its drawn example, or is unavailable.
See plans/lezione-8-social.md section 7 and ADR 0020.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import i18n

GAME_PATH = Path(__file__).parent / "vero_o_falso.json"
ANSWERS = ("vero", "falso_ia", "truffa", "verificare")
LANGS = ("it", "en", "fr", "ar", "ckb", "kmr")
RTL = ("ar", "ckb")
REQUIRED_UI = (
    "title", "subtitle", "teams", "team1", "team2", "team3", "timer", "seconds",
    "scoring", "scoringOn", "scoringOff", "language", "start", "resume",
    "newGame", "preparing", "menu", "missing", "fallbackTag", "invented",
    "done", "think", "vote", "paused", "reveal", "skip", "next", "back",
    "clue", "action", "source", "categoryDone", "points", "toMenu", "finish",
    "final", "habitsTitle", "listen", "replay", "whoVoted",
)  # fmt: skip
ITEM_ID_RE = re.compile(r"^[A-Z][0-9]$")
MEDIA_TYPES = ("image", "video", "audio")


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(GAME_PATH.read_text(encoding="utf-8"))


def validate(data: dict) -> list[str]:
    """Problems found in the content, [] when it is valid."""
    problems: list[str] = []
    answers = data.get("answers", {})
    for a in ANSWERS:
        if a not in answers:
            problems.append(f"missing answer {a}")
    for key in REQUIRED_UI:
        if not data.get("ui", {}).get(key, {}).get("it"):
            problems.append(f"ui.{key} has no Italian text")
    if len(data.get("habits", [])) != 5:
        problems.append("there must be five habits")
    cat_ids = [c["id"] for c in data.get("categories", [])]
    if len(set(cat_ids)) != len(cat_ids):
        problems.append("duplicate category ids")
    items = data.get("items", [])
    ids = [i.get("id", "") for i in items]
    if len(set(ids)) != len(ids):
        problems.append("duplicate item ids")
    listed = [i for c in data.get("categories", []) for i in c["items"]]
    if sorted(listed) != sorted(ids):
        problems.append("categories do not list every item exactly once")
    for item in items:
        iid = item.get("id", "?")
        if not ITEM_ID_RE.match(iid):
            problems.append(f"{iid}: bad id")
        if item.get("category") not in cat_ids:
            problems.append(f"{iid}: unknown category")
        else:
            cat = next(c for c in data["categories"] if c["id"] == item["category"])
            if iid not in cat["items"]:
                problems.append(f"{iid}: not listed in its category")
        if item.get("answer") not in ANSWERS:
            problems.append(f"{iid}: bad answer")
        if item.get("onlyVerifiable") != (item.get("answer") == "verificare"):
            problems.append(f"{iid}: onlyVerifiable must match answer == verificare")
        if not isinstance(item.get("hardToJudge"), bool):
            problems.append(f"{iid}: hardToJudge must be a bool")
        if not item.get("clue", {}).get("it"):
            problems.append(f"{iid}: no Italian clue")
        if not item.get("action", {}).get("it"):
            problems.append(f"{iid}: no Italian action")
        media, mock = item.get("media"), item.get("mock")
        if not media and not mock:
            problems.append(f"{iid}: needs media or mock")
        if item.get("invented") and not mock:
            problems.append(f"{iid}: invented needs a mock")
        if media and media.get("type") not in MEDIA_TYPES:
            problems.append(f"{iid}: bad media type")
    return problems


def points(item: dict, vote: str) -> int:
    """2 for the right card; 1 for "Devo verificare" on an item that is hard to
    judge by eye; otherwise 0. Never negative."""
    if vote == item["answer"]:
        return 2
    if vote == "verificare" and item["hardToJudge"]:
        return 1
    return 0


def points_table(item: dict) -> dict[str, int]:
    return {answer: points(item, answer) for answer in ANSWERS}


def available_langs(data: dict) -> list[str]:
    """ "it" plus every language present in all the texts the game shows."""
    texts: list[dict] = []
    texts += list(data["ui"].values())
    for a in data["answers"].values():
        texts += [a["word"], a["sub"]]
    texts += [c["label"] for c in data["categories"]]
    for item in data["items"]:
        texts += [item["clue"], item["action"]]
    texts += [{k: v for k, v in h.items() if k != "emoji"} for h in data["habits"]]
    return ["it"] + [lang for lang in LANGS[1:] if all(t.get(lang) for t in texts)]


def _item_config(
    item: dict, statuses: dict[str, dict], render_html: Callable[[str], str], cat_label: str
) -> dict:
    media = item.get("media")
    slot = media["slot"] if media else None
    st = statuses.get(slot) if slot else None
    has_file = bool(st and st.get("file") and not st.get("skipped"))
    media_type = media_url = mock_html = missing = None
    uses_fallback = False
    if has_file:
        media_type = st["file"]["family"]
        media_url = st["file"]["url"]
        available = True
    elif item.get("mock"):
        mock_html = render_html(item["mock"])
        uses_fallback = slot is not None
        available = True
    else:
        available = False
        missing = slot
    fields = (st or {}).get("fields") or {}
    caption = {"it": fields["caption"]} if fields.get("caption") else item.get("caption", {})
    return {
        "id": item["id"],
        "category": item["category"],
        "answer": item["answer"],
        "onlyVerifiable": item["onlyVerifiable"],
        "hardToJudge": item["hardToJudge"],
        "points": points_table(item),
        "available": available,
        "mediaType": media_type,
        "mediaUrl": media_url,
        "mockHtml": mock_html,
        "invented": item["invented"] or uses_fallback,
        "usesFallback": uses_fallback,
        "missingSlot": missing,
        "caption": caption,
        "clue": item["clue"],
        "action": item["action"],
        "link": fields.get("link"),
        "alt": caption.get("it") or cat_label,
    }


def page_config(statuses: dict[str, dict], render_html: Callable[[str], str]) -> dict[str, Any]:
    """Everything game.js needs. `statuses` maps slot id to materials.status();
    `render_html` turns a mock into HTML (resolving any rb-slot in it)."""
    data = load()
    by_id = {i["id"]: i for i in data["items"]}
    items = []
    for cat in data["categories"]:
        for iid in cat["items"]:
            items.append(_item_config(by_id[iid], statuses, render_html, cat["label"]["it"]))
    return {
        "langs": available_langs(data),
        "langNames": {"it": "Italiano", **i18n.LANGUAGES},
        "rtl": list(RTL),
        "ui": data["ui"],
        "answers": [{"id": a, **data["answers"][a]} for a in ANSWERS],
        "habits": data["habits"],
        "categories": data["categories"],
        "items": items,
        "defaults": {"timer": 40, "timers": [30, 40, 45, 60], "teams": 2},
        "materialsUrl": "/materiali",
        "storageKey": "rb-vof-v1",
    }


def cards_context(copies: int) -> dict[str, Any]:
    data = load()
    langs = [
        lang
        for lang in ("en", "fr", "ar", "ckb", "kmr")
        if all(data["answers"][a]["word"].get(lang) for a in ANSWERS)
    ]
    cards = [{"id": a, **data["answers"][a]} for a in ANSWERS]
    return {"copies": min(max(copies, 1), 4), "langs": langs, "rtl": list(RTL), "cards": cards}
