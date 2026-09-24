"""SQLite storage for students, their language preference, and scores.

Deviates from ADR 0010 as a deliberate, temporary stopgap for lesson 1 —
see ADR 0013. Stores a typed name, unlike the avatar picker ADR 0010
describes. Since ADR 0015, a student row is a permanent account (picked
from a roster at login, not recreated every session) rather than a
throwaway per-session row. The database file lives under ``data/`` and is
gitignored (``*.db``); it never enters version control.
"""

from __future__ import annotations

import os
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TypedDict

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


class Student(TypedDict):
    id: str
    name: str
    language: str


def _migrate(conn: sqlite3.Connection) -> None:
    columns = {row[1] for row in conn.execute("PRAGMA table_info(students)")}
    if "language" not in columns:
        conn.execute("ALTER TABLE students ADD COLUMN language TEXT NOT NULL DEFAULT 'it'")


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(_SCHEMA)
        _migrate(conn)
        yield conn
        conn.commit()
    finally:
        conn.close()


def create_student(name: str, language: str = "it") -> str:
    student_id = str(uuid.uuid4())
    with connect() as conn:
        conn.execute(
            "INSERT INTO students (id, name, language) VALUES (?, ?, ?)",
            (student_id, name, language),
        )
    return student_id


def get_student(student_id: str) -> Student | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, language FROM students WHERE id = ?", (student_id,)
        ).fetchone()
    return {"id": row[0], "name": row[1], "language": row[2]} if row else None


def find_student_by_name(name: str) -> str | None:
    with connect() as conn:
        row = conn.execute(
            "SELECT id FROM students WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
    return row[0] if row else None


def list_students() -> list[Student]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, language FROM students ORDER BY lower(name)"
        ).fetchall()
    return [{"id": r[0], "name": r[1], "language": r[2]} for r in rows]


def set_student_language(student_id: str, language: str) -> None:
    with connect() as conn:
        conn.execute("UPDATE students SET language = ? WHERE id = ?", (language, student_id))


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
