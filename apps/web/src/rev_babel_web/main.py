"""FastAPI app: welcome screen, name capture, and the course page.

See ADR 0013 for why this captures a typed name at all, ahead of the
avatar picker (ADR 0010) that is meant to replace it.
"""

from __future__ import annotations

import os
import time

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

from rev_babel_web import db

_HERE = os.path.dirname(__file__)
_WEB_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))

SESSION_SECRET = os.environ.get("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError(
        "SESSION_SECRET is not set. Copy .env.example to .env and fill it "
        "in (see docs/operations.md)."
    )

MAX_NAME_LENGTH = 60

LESSONS = [
    {
        "slug": "lezione-1",
        "title": "Lezione 1",
        "long_title": "La Tastiera e il Mouse",
        "url": "/course/lezione-1",
    },
]

# Per-game sanity bounds on a reported score, so a stray or malicious
# postMessage can't write nonsense into the database. Not a leaderboard —
# each student sees only their own numbers, per docs/data-and-privacy.md.
GAMES = {
    "mouse": {
        "title": "Il mouse",
        "unit": "ms",
        "max_value": 60_000,
        "src": "/static/lessons/lezione-1/mouse/index.html",
    },
    "keyboard": {
        "title": "La tastiera",
        "unit": "s",
        "max_value": 3_600,
        "src": "/static/lessons/lezione-1/keyboard/index.html",
    },
}

# Which games belong to which lesson. Only lezione-1 has any today.
LESSON_GAMES = {"lezione-1": GAMES}


def _format_score(unit: str, value: float | None) -> str:
    if value is None:
        return "—"
    return f"{round(value)} ms" if unit == "ms" else f"{value:.1f} s"


class ScoreIn(BaseModel):
    game: str
    value: float = Field(gt=0)


SESSION_MAX_AGE_SECONDS = 24 * 60 * 60

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="rev_babel_session",
    same_site="lax",
    https_only=os.environ.get("WEB_COOKIE_SECURE", "true").lower() != "false",
    max_age=SESSION_MAX_AGE_SECONDS,
)
app.mount("/static", StaticFiles(directory=os.path.join(_WEB_ROOT, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_WEB_ROOT, "templates"))
# Busts the browser's cache for /static/style.css on every restart, so a CSS
# edit during a live session doesn't get served stale from cache.
templates.env.globals["static_version"] = str(int(time.time()))


def _current_name(request: Request) -> str | None:
    student_id = request.session.get("student_id")
    if not student_id:
        return None
    return db.get_student_name(student_id)


def _clean_name(raw: str) -> str | None:
    name = raw.strip()
    if not name or len(name) > MAX_NAME_LENGTH or not name.isprintable():
        return None
    return name


@app.get("/")
def welcome(request: Request):
    if _current_name(request) is not None:
        return RedirectResponse("/course", status_code=303)
    return templates.TemplateResponse(request, "welcome.html", {"error": None})


@app.post("/welcome")
def submit_name(request: Request, name: str = Form(...)):
    clean = _clean_name(name)
    if clean is None:
        return templates.TemplateResponse(
            request,
            "welcome.html",
            {"error": "Scrivi il tuo nome per continuare."},
            status_code=400,
        )
    request.session["student_id"] = db.create_student(clean)
    return RedirectResponse("/course", status_code=303)


@app.get("/course")
def course(request: Request):
    name = _current_name(request)
    if name is None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "course.html", {"name": name, "lessons": LESSONS})


@app.get("/course/{lesson_slug}")
def lesson_detail(request: Request, lesson_slug: str):
    name = _current_name(request)
    if name is None:
        return RedirectResponse("/", status_code=303)
    lesson = next((lesson for lesson in LESSONS if lesson["slug"] == lesson_slug), None)
    if lesson is None:
        raise HTTPException(status_code=404)
    games = LESSON_GAMES.get(lesson_slug, {})
    return templates.TemplateResponse(
        request, "lesson.html", {"name": name, "lessons": LESSONS, "lesson": lesson, "games": games}
    )


@app.get("/course/{lesson_slug}/{game_slug}")
def lesson_game(request: Request, lesson_slug: str, game_slug: str):
    name = _current_name(request)
    if name is None:
        return RedirectResponse("/", status_code=303)
    info = LESSON_GAMES.get(lesson_slug, {}).get(game_slug)
    if info is None:
        raise HTTPException(status_code=404)
    student_id = request.session["student_id"]
    return templates.TemplateResponse(
        request,
        "game.html",
        {
            "name": name,
            "lessons": LESSONS,
            "lesson_slug": lesson_slug,
            "game": game_slug,
            "info": info,
            "best_display": _format_score(info["unit"], db.personal_best(student_id, game_slug)),
            "last_display": _format_score(info["unit"], db.last_score(student_id, game_slug)),
        },
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.post("/api/scores")
def submit_score(request: Request, score: ScoreIn):
    student_id = request.session.get("student_id")
    if student_id is None or db.get_student_name(student_id) is None:
        raise HTTPException(status_code=401, detail="No active session.")
    game_info = GAMES.get(score.game)
    if game_info is None or score.value > game_info["max_value"]:
        raise HTTPException(status_code=400, detail="Unknown game or implausible score.")
    db.record_score(student_id, score.game, score.value)
    return JSONResponse(
        {
            "best": db.personal_best(student_id, score.game),
            "last": db.last_score(student_id, score.game),
        }
    )
