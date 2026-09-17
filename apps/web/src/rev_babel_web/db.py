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
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(_SCHEMA)
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
