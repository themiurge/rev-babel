"""One-time phone approvals for lesson 4's SPID simulator.

The game on the computer asks for a challenge; the student scans its QR
code with their phone, which opens a short Italian page with Approva /
Rifiuta; the computer polls until the phone has decided. Challenges live
in this process's memory only (like ``live.py``, this relies on a single
uvicorn worker) and hold no personal data: a random code, the owning
student's id (so only that student's computer can read the outcome), the
fictional service name, and a state.
"""

from __future__ import annotations

import secrets
import threading
import time
from dataclasses import dataclass

import segno

# No 0/O, 1/I/L: the code is printed under the QR for typing by hand.
_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 8
TTL_SECONDS = 10 * 60
MAX_PENDING = 500

PENDING = "pending"
APPROVED = "approved"
REJECTED = "rejected"


@dataclass
class Challenge:
    code: str
    student_id: str
    service: str
    created: float
    state: str = PENDING


_lock = threading.Lock()
_challenges: dict[str, Challenge] = {}


def _purge(now: float) -> None:
    for code in [c for c, ch in _challenges.items() if now - ch.created > TTL_SECONDS]:
        del _challenges[code]


def create(student_id: str, service: str) -> Challenge:
    now = time.time()
    with _lock:
        _purge(now)
        if len(_challenges) >= MAX_PENDING:
            oldest = min(_challenges.values(), key=lambda ch: ch.created)
            del _challenges[oldest.code]
        # A student has one open challenge at a time: starting again
        # (new QR, new task) retires the previous one.
        for code in [c for c, ch in _challenges.items() if ch.student_id == student_id]:
            del _challenges[code]
        code = "".join(secrets.choice(_ALPHABET) for _ in range(CODE_LENGTH))
        while code in _challenges:
            code = "".join(secrets.choice(_ALPHABET) for _ in range(CODE_LENGTH))
        challenge = Challenge(code=code, student_id=student_id, service=service, created=now)
        _challenges[code] = challenge
        return challenge


def get(code: str) -> Challenge | None:
    now = time.time()
    with _lock:
        _purge(now)
        return _challenges.get(code.upper())


def decide(code: str, approve: bool) -> Challenge | None:
    """Record the phone's decision. Only a still-pending challenge can be decided."""
    now = time.time()
    with _lock:
        _purge(now)
        challenge = _challenges.get(code.upper())
        if challenge is None or challenge.state != PENDING:
            return None
        challenge.state = APPROVED if approve else REJECTED
        return challenge


def consume(code: str) -> None:
    """The computer has seen the outcome: the code can never be used again."""
    with _lock:
        _challenges.pop(code.upper(), None)


def qr_svg(url: str) -> str:
    return segno.make(url, error="m").svg_inline(scale=5, border=2, dark="#111", light="#fff")
