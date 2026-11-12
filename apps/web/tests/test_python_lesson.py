"""Lesson 7: the Python page, its routes, the assistant and the deck. The model
is always mocked; every program here is invented practice code, never a
student's (docs/data-and-privacy.md)."""

import hashlib
import json
import logging
import re
from pathlib import Path

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient
from rev_babel_web import decks, main, python_helper, tutor
from rev_babel_web.main import app

FAKE_KEY = "test-key-not-real"
STATIC = Path(__file__).parents[1] / "static"
VENDOR = STATIC / "vendor/pyodide"
PY_DIR = STATIC / "lessons/lezione-7/python"
STEPS = python_helper.STEPS


def _student(name: str = "Student A") -> TestClient:
    c = TestClient(app)
    c.post("/welcome", data={"name": name})
    return c


def _body(ask="prossimo", step="s3", **extra) -> dict:
    return {
        "step": step,
        "ask": ask,
        "question": "",
        "code": STEPS[step]["start"],
        "error": "",
        **extra,
    }


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    tutor.limiter.reset()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls: list[dict] = []

    def fake_call(system, messages):
        calls.append({"system": system, "messages": messages})
        return "Prova così:\n```\nprint(piatto)\n```\n💡 Hai indicato la riga: bene."

    monkeypatch.setattr(tutor, "call_model", fake_call)
    return calls


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)


def _config(page_text: str) -> dict:
    raw = re.search(r'id="py-config"[^>]*>(.*?)</script>', page_text, re.S).group(1)
    return json.loads(raw.replace("<\\/", "</"))


# ---- pages and wiring ----


def test_lesson_7_is_in_the_menu_and_links_the_python_page() -> None:
    c = _student()
    assert "/course/lezione-7" in c.get("/course").text
    page = c.get("/course/lezione-7")
    assert page.status_code == 200 and "Programmare con Python" in page.text
    assert 'href="/games/python"' in page.text and 'target="_blank"' in page.text
    redirect = c.get("/course/lezione-7/python", follow_redirects=False)
    assert redirect.headers["location"] == "/games/python"


def test_python_needs_a_login() -> None:
    anon = TestClient(app)
    assert anon.get("/games/python", follow_redirects=False).status_code == 303
    assert anon.post("/api/python-helper", json=_body()).status_code == 401


def test_page_embeds_the_lesson_without_the_model_notes() -> None:
    page = _student().get("/games/python")
    assert page.status_code == 200
    assert "python.js" in page.text
    config = _config(page.text)
    assert config["live"] is False
    assert [s["id"] for s in config["content"]["steps"]] == [f"s{i}" for i in range(1, 8)]
    for step in config["content"]["steps"]:
        assert "focus" not in step and "assistant" not in step
    assert "worker.js" in config["workerUrl"] and "runner.py" in config["runnerUrl"]


def test_python_installed_follows_the_files(monkeypatch, tmp_path) -> None:
    c = _student()
    monkeypatch.setattr(main, "PYODIDE_DIR", str(tmp_path))
    assert _config(c.get("/games/python").text)["pythonInstalled"] is False
    for name in python_helper.PYODIDE_FILES:
        (tmp_path / name).write_bytes(b"")
    assert _config(c.get("/games/python").text)["pythonInstalled"] is True


def test_static_lesson_files_are_served() -> None:
    c = TestClient(app)
    runner = c.get("/static/lessons/lezione-7/python/runner.py")
    assert runner.status_code == 200 and runner.content == (PY_DIR / "runner.py").read_bytes()
    assert c.get("/static/lessons/lezione-7/python/worker.js").status_code == 200
    assert c.get("/static/lessons/lezione-7/python/python.js").status_code == 200


def test_vendored_runtime_is_checksummed_and_served() -> None:
    assert (VENDOR / "SHA256SUMS").is_file() and (VENDOR / "LICENSE").is_file()
    if not (VENDOR / "pyodide.asm.wasm").exists():
        pytest.skip("Pyodide not fetched (run `make pyodide`)")
    for line in (VENDOR / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split()
        assert hashlib.sha256((VENDOR / name).read_bytes()).hexdigest() == digest, name
    c = TestClient(app)
    wasm = c.get("/static/vendor/pyodide/pyodide.asm.wasm")
    assert wasm.headers["content-type"] == "application/wasm"
    assert (
        c.get("/static/vendor/pyodide/pyodide.asm.mjs")
        .headers["content-type"]
        .startswith("text/javascript")
    )


# ---- the assistant ----


@pytest.mark.parametrize("ask", ["errore", "prossimo", "riga", "idea"])
def test_offline_answers_are_scripted(_fresh, ask) -> None:
    c = _student()
    for step in STEPS:
        data = c.post("/api/python-helper", json=_body(ask, step)).json()
        assert data["kind"] == "offline" and data["notice"] == "notice_offline"
        assert data["segments"][0]["text"] == STEPS[step]["assistant"][ask]
    assert _fresh == []  # the model was never called


def test_offline_error_and_free_question() -> None:
    c = _student()
    ui = python_helper.CONTENT["ui"]
    err = c.post("/api/python-helper", json=_body("errore", error="riga 2: NameError")).json()
    assert err["segments"][0]["text"].startswith(ui["offline_errore"])
    free = c.post("/api/python-helper", json=_body("libera", question="Come si fa?")).json()
    assert free["segments"][0]["text"] == ui["offline_free"] + "\n💡 " + STEPS["s3"]["hints"][0]


def test_live_request_shape(live, _fresh) -> None:
    c = _student()
    body = _body("errore", "s3", error="riga 2: NameError: name 'piato' is not defined")
    data = c.post("/api/python-helper", json=body).json()
    assert data["kind"] == "live" and len(_fresh) == 1
    system = _fresh[0]["system"]
    assert system[0]["cache_control"] == {"type": "ephemeral"}
    assert system[0]["text"] == python_helper.SYSTEM_PROMPT
    assert STEPS["s3"]["focus"] in system[1]["text"]
    (message,) = _fresh[0]["messages"]
    assert message["role"] == "user"
    assert "1| piatto = " in message["content"]
    assert "piato" in message["content"]
    assert "Cosa vuol dire l'errore?" in message["content"]
    assert [s["type"] for s in data["segments"]] == ["text", "code", "text"]
    free = c.post("/api/python-helper", json=_body("libera", question="Cosa è print?")).json()
    assert free["kind"] == "live"
    assert "La mia domanda: Cosa è print?" in _fresh[1]["messages"][0]["content"]


def test_format_reply_cuts_code_and_cleans_prose() -> None:
    code = "\n".join(f"riga{i}" for i in range(8))
    text = f"## **Ecco**\n```python\n# nota\n{code}\n```\nFatto.\n💡 Prova."
    segments = python_helper.format_reply(text)
    assert [s["type"] for s in segments] == ["text", "code", "text"]
    assert segments[0]["text"] == "Ecco"
    block = segments[1]["text"].split("\n")
    assert block[0] == "# nota" and block[-1] == "…" and len(block) == 6
    assert python_helper.format_reply("Solo testo.") == [{"type": "text", "text": "Solo testo."}]


@pytest.mark.parametrize(
    "extra",
    [
        {"code": 'mail = "studente@example.com"'},
        {"code": "numero = 3331234567"},
        {"code": 'password = "abc123"'},
        {"ask": "libera", "question": "Il mio RSSMRA80A01H501U va bene?"},
    ],
)
@pytest.mark.parametrize("with_key", [False, True])
def test_personal_data_is_blocked(monkeypatch, _fresh, extra, with_key) -> None:
    if with_key:
        monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)
    data = _student().post("/api/python-helper", json=_body(**extra)).json()
    assert data["kind"] == "blocked" and data["notice"] == "notice_blocked"
    assert _fresh == []


def test_the_lessons_own_material_passes_the_filter() -> None:
    for step in STEPS.values():
        assert not tutor.looks_sensitive(step["start"])
        for text in step["assistant"].values():
            assert not tutor.looks_sensitive(text)
        for text in step["hints"]:
            assert not tutor.looks_sensitive(text)


def test_rate_limit_is_shared_with_the_tutor(live, _fresh) -> None:
    c = _student()
    for _ in range(tutor.PER_MINUTE):
        assert c.post("/api/python-helper", json=_body()).status_code == 200
    over = c.post("/api/python-helper", json=_body())
    assert over.status_code == 429 and over.json()["kind"] == "limited"
    assert len(_fresh) == tutor.PER_MINUTE
    # Six tutor calls then one helper call: the same budget.
    tutor.limiter.reset()
    d = _student("Student B")
    tutor_body = {"mission": "chiara", "reply_lang": "it", "message": "Ciao", "history": []}
    for _ in range(tutor.PER_MINUTE):
        assert d.post("/api/tutor", json=tutor_body).status_code == 200
    assert d.post("/api/python-helper", json=_body()).status_code == 429


def test_validation() -> None:
    c = _student()

    def post(**kw) -> int:
        return c.post("/api/python-helper", json={**_body(), **kw}).status_code

    assert post(step="s9") == 400
    assert post(ask="boh") == 400
    assert post(ask="libera", question="") == 400
    assert post(code="x" * (python_helper.MAX_CODE + 1)) == 400
    assert post(ask="libera", question="q" * (python_helper.MAX_QUESTION + 1)) == 400
    assert post(code="x" * (python_helper.MAX_CODE * 2 + 1)) == 422


@pytest.mark.parametrize(
    "error",
    [
        anthropic.APIConnectionError(request=httpx.Request("POST", "https://x")),
        tutor.TutorUnavailable("refusal"),
    ],
)
def test_model_failure_falls_back_to_the_script(live, monkeypatch, caplog, error) -> None:
    def failing(system, messages):
        raise error

    monkeypatch.setattr(tutor, "call_model", failing)
    body = _body("libera", question="domanda segretissima", code='piatto = "zucchine"')
    with caplog.at_level(logging.WARNING, logger="rev_babel_web.python_helper"):
        data = _student().post("/api/python-helper", json=body).json()
    assert data["kind"] == "error" and data["notice"] == "notice_error"
    assert data["segments"][0]["text"].startswith(python_helper.CONTENT["ui"]["offline_free"])
    assert "segretissima" not in caplog.text and "zucchine" not in caplog.text
    assert type(error).__name__ in caplog.text


def test_static_system_prompt_is_long_enough_to_cache() -> None:
    assert len(python_helper.SYSTEM_PROMPT) > 512 * 4
    for step in STEPS.values():
        assert f"- {step['focus']}" in python_helper.SYSTEM_PROMPT


# ---- the deck ----


def test_deck_is_listed_and_well_formed() -> None:
    found = {d["slug"]: d for d in decks.list_decks()}
    assert found["lezione-7-python"]["slide_count"] == 14
    slides = decks.get_deck("lezione-7-python")["slides"]
    for slide in slides:
        assert slide["it"].strip()
        assert "{{" not in slide["it"] and "[[P" not in slide["it"]
    assert "handoff" in slides[7]["it"] and "handoff" in slides[12]["it"]
    assert "print(" in slides[3]["it"] and "Ciao!" in slides[3]["it"]
