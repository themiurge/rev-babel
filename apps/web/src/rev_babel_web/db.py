"""Minimal SQLite storage for lesson-1 student sessions.

Deviates from ADR 0010 as a deliberate, temporary stopgap for lesson 1 —
see ADR 0013. Stores a typed name, unlike the avatar picker ADR 0010
describes. The database file lives under ``data/`` and is gitignored
(``*.db``); it never enters version control.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("DATA_DIR", "data")) / "rev_babel.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS game_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES students(id),
    game TEXT NOT NULL,
    value REAL NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(_SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_student(name: str) -> str:
    student_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO students (id, name) VALUES (?, ?)",
            (student_id, name),
        )
    return student_id


def get_student_name(student_id: str) -> str | None:
    with connect() as conn:
        row = conn.execute("SELECT name FROM students WHERE id = ?", (student_id,)).fetchone()
    return row[0] if row else None


def record_score(student_id: str, game: str, value: float) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO game_scores (student_id, game, value) VALUES (?, ?, ?)",
            (student_id, game, value),
        )


def personal_best(student_id: str, game: str) -> float | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT MIN(value) FROM game_scores WHERE student_id = ? AND game = ?",
            (student_id, game),
        ).fetchone()
    return row[0] if row and row[0] is not None else None


def last_score(student_id: str, game: str) -> float | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT value FROM game_scores WHERE student_id = ? AND game = ? "
            "ORDER BY id DESC LIMIT 1",
            (student_id, game),
        ).fetchone()
    return row[0] if row else None
