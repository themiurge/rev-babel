#!/usr/bin/env python3
"""Translate text with the Google Cloud Translation API (v2, API-key auth).

    scripts/translate.py --from it-IT --to en-US "Fai clic su Inizia."
    echo "<p>Ciao</p>" | scripts/translate.py --from it --to ar --format html

The key comes from GOOGLE_TRANSLATE_API_KEY (the environment, or `.env` in
the repository root) - never from the command line, where it would land in
shell history.

PRIVACY: whatever you pass is sent to Google. Use it for course material
only; never for anything a student wrote or anything that names a student
(docs/data-and-privacy.md).

Region tags are dropped (it-IT -> it, en-US -> en) because the API takes
bare language codes, except zh-CN / zh-TW / pt-BR style codes it knows.
The project's own codes are mapped: kmr (Kurmanji) -> ku, ckb stays ckb.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://translation.googleapis.com/language/translate/v2"
KEEP_REGION = {"zh-cn", "zh-tw"}
PROJECT_CODES = {"kmr": "ku"}


def api_code(tag: str) -> str:
    tag = tag.strip().replace("_", "-")
    if tag.lower() in KEEP_REGION:
        return tag.lower().replace("zh-cn", "zh-CN").replace("zh-tw", "zh-TW")
    base = tag.split("-")[0].lower()
    return PROJECT_CODES.get(base, base)


def load_key() -> str:
    key = os.environ.get("GOOGLE_TRANSLATE_API_KEY")
    if not key:
        env_file = Path(__file__).resolve().parent.parent / ".env"
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                name, _, value = line.partition("=")
                if name.strip() == "GOOGLE_TRANSLATE_API_KEY":
                    key = value.strip().strip("'\"")
    if not key:
        sys.exit("GOOGLE_TRANSLATE_API_KEY is not set (environment or .env).")
    return key


def translate(text: str, source: str, target: str, fmt: str, key: str) -> str:
    body = urllib.parse.urlencode(
        {"q": text, "source": api_code(source), "target": api_code(target), "format": fmt}
    ).encode()
    request = urllib.request.Request(
        ENDPOINT,
        data=body,
        # The key goes in a header, not the URL, so it stays out of logs.
        headers={"X-goog-api-key": key, "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")
        sys.exit(f"Google Translate returned HTTP {err.code}: {detail}")
    return payload["data"]["translations"][0]["translatedText"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--from", dest="source", required=True, help="e.g. it-IT or it")
    parser.add_argument("--to", dest="target", required=True, help="e.g. en-US, fr, ar, ckb, kmr")
    parser.add_argument(
        "--format", choices=["text", "html"], default="text", help="html keeps tags intact"
    )
    parser.add_argument("text", nargs="*", help="text to translate (default: read stdin)")
    args = parser.parse_args()

    text = " ".join(args.text) if args.text else sys.stdin.read()
    if not text.strip():
        sys.exit("Nothing to translate.")
    print(translate(text, args.source, args.target, args.format, load_key()))


if __name__ == "__main__":
    main()
