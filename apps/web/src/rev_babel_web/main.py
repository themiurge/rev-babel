"""FastAPI app: welcome screen, name capture, and the course page.

See ADR 0013 for why this captures a typed name at all, ahead of the
avatar picker (ADR 0010) that is meant to replace it.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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
    {"slug": "lezione-1", "title": "Lezione 1", "long_title": "La Tastiera e il Mouse"},
]

app = FastAPI()
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    session_cookie="rev_babel_session",
    same_site="lax",
    https_only=os.environ.get("WEB_COOKIE_SECURE", "true").lower() != "false",
)
app.mount("/static", StaticFiles(directory=os.path.join(_WEB_ROOT, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(_WEB_ROOT, "templates"))


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


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)
