"""Lesson 6's tutor chatbot. The model is always mocked: no test touches the
network, and every message here is invented practice text, never a real
student's (docs/data-and-privacy.md)."""

import json
import logging
import re

import anthropic
import httpx
import pytest
from fastapi.testclient import TestClient
from rev_babel_web import i18n, tutor
from rev_babel_web.main import app

FAKE_KEY = "test-key-not-real"
# Captured before the autouse fixture swaps it for a fake.
REAL_CALL_MODEL = tutor.call_model


def _student(name: str, lang: str = "it") -> TestClient:
    c = TestClient(app)
    c.post("/welcome", data={"name": name})
    c.post("/api/language", json={"language": lang})
    return c


def _body(message: str, **extra) -> dict:
    return {"mission": "chiara", "reply_lang": "it", "message": message, "history": [], **extra}


@pytest.fixture(autouse=True)
def _fresh(monkeypatch):
    tutor.limiter.reset()
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    calls: list[dict] = []

    def fake_call(system, messages):
        calls.append({"system": system, "messages": messages})
        return "Risposta finta.\n💡 Domanda chiara."

    monkeypatch.setattr(tutor, "call_model", fake_call)
    return calls


@pytest.fixture
def live(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)


# ---- pages and auth ----


def test_lesson_6_is_in_the_menu_and_links_the_tutor_in_a_new_tab() -> None:
    c = _student("Student A")
    assert "/course/lezione-6" in c.get("/course").text
    page = c.get("/course/lezione-6")
    assert page.status_code == 200
    assert "L&#39;intelligenza artificiale" in page.text
    assert 'href="/games/tutor"' in page.text and 'target="_blank"' in page.text
    redirect = c.get("/course/lezione-6/tutor", follow_redirects=False)
    assert redirect.headers["location"] == "/games/tutor"


def test_tutor_needs_a_login() -> None:
    anon = TestClient(app)
    assert anon.get("/games/tutor", follow_redirects=False).status_code == 303
    assert anon.post("/api/tutor", json=_body("ciao")).status_code == 401


@pytest.mark.parametrize("lang", ["it", *i18n.LANGUAGES])
def test_tutor_page_carries_italian_and_the_students_language(lang: str) -> None:
    page = _student(f"Student {lang}", lang).get("/games/tutor")
    assert page.status_code == 200
    raw = re.search(r'id="tutor-config"[^>]*>(.*?)</script>', page.text, re.S).group(1)
    config = json.loads(raw.replace("<\\/", "</"))
    assert config["lang"] == lang
    assert config["rtl"] == (lang in i18n.RTL_LANGUAGES)
    assert config["live"] is False
    first = config["content"]["missions"][0]
    assert first["title"]["it"] == "Che cos'è un chatbot?"
    assert bool(first["title"]["other"]) == (lang != "it")
    assert "/static/lessons/lezione-6/tutor/tutor.js" in page.text


def test_language_mission_fills_in_the_students_own_sentence() -> None:
    page = _student("Student F", "fr").get("/games/tutor")
    raw = re.search(r'id="tutor-config"[^>]*>(.*?)</script>', page.text, re.S).group(1)
    lingua = next(m for m in json.loads(raw)["content"]["missions"] if m["id"] == "lingua")
    chip = lingua["chips"][1]["prompt"]
    assert "francese" in chip["it"] and "français" in chip["other"]
    assert "Demain j'ai un rendez-vous" in lingua["chips"][0]["prompt"]["it"]
    assert "@@" not in json.dumps(lingua)


# ---- content shape ----


def test_every_tutor_text_has_all_six_languages() -> None:
    langs = {"it", *i18n.LANGUAGES}

    def walk(node):
        if isinstance(node, dict) and "it" in node and isinstance(node["it"], str):
            assert set(node) == langs, node["it"]
            assert all(node[lang].strip() for lang in langs), node["it"]
            return
        if isinstance(node, dict):
            for key, value in node.items():
                if key not in ("samples", "_note", "focus"):
                    walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    walk(tutor.CONTENT)
    assert set(tutor.CONTENT["samples"]) == set(i18n.LANGUAGES)


def test_no_example_prompt_trips_the_personal_data_filter() -> None:
    for mission in tutor.CONTENT["missions"]:
        for chip in mission["chips"]:
            for lang in ("it", *i18n.LANGUAGES):
                pair = tutor._pair(chip["prompt"], lang)
                assert not tutor.looks_sensitive(pair["it"]), pair["it"]
                assert not tutor.looks_sensitive(pair["other"]), pair["other"]


# ---- offline: no key ----


def test_without_a_key_a_chip_gets_its_scripted_answer(_fresh) -> None:
    c = _student("Student A", "en")
    prompt = tutor.CONTENT["missions"][1]["chips"][0]["prompt"]["it"]
    response = c.post("/api/tutor", json=_body(prompt, reply_lang="both"))
    data = response.json()
    assert response.status_code == 200
    assert data["kind"] == "offline" and data["notice"] == "notice_offline"
    assert data["blocks"][0].startswith("Pasta al pomodoro per 4")
    assert data["blocks"][1].startswith("Tomato pasta for 4")
    assert _fresh == []  # nothing went to the model


def test_without_a_key_free_text_gets_the_missions_tip() -> None:
    c = _student("Student A")
    data = c.post("/api/tutor", json=_body("Una domanda inventata per il test.")).json()
    assert data["kind"] == "offline"
    assert data["blocks"] == [
        tutor.CONTENT["ui"]["offline_free"]["it"]
        + "\n💡 "
        + tutor.CONTENT["missions"][1]["why"]["it"]
    ]


def test_reply_language_picks_the_blocks() -> None:
    c = _student("Student A", "ar")
    prompt = tutor.CONTENT["missions"][0]["chips"][1]["prompt"]["it"]
    only_ar = c.post("/api/tutor", json={**_body(prompt), "mission": "chatbot", "reply_lang": "ar"})
    assert only_ar.json()["blocks"] == [tutor.CONTENT["missions"][0]["chips"][1]["answer"]["ar"]]
    # A language that is not hers is refused.
    wrong = c.post("/api/tutor", json={**_body(prompt), "reply_lang": "fr"})
    assert wrong.status_code == 400


# ---- live: key set, model mocked ----


def test_live_reply_goes_through_the_model_with_the_system_prompt(live, _fresh) -> None:
    c = _student("Student A", "ckb")
    response = c.post("/api/tutor", json=_body("Domanda finta.", reply_lang="both"))
    assert response.json() == {"kind": "live", "blocks": ["Risposta finta.\n💡 Domanda chiara."]}
    (call,) = _fresh
    static, dynamic = call["system"]
    assert static["cache_control"] == {"type": "ephemeral"}
    assert "not a person" in static["text"]
    assert "Mission 2" in dynamic["text"] and "Sorani" in dynamic["text"]
    assert "===" in dynamic["text"]
    assert call["messages"] == [{"role": "user", "content": "Domanda finta."}]


def test_static_system_prompt_is_long_enough_to_cache() -> None:
    # 512 tokens is the caching minimum for this model; ~4 chars a token.
    assert len(tutor.SYSTEM_PROMPT) > 512 * 4


def test_split_reply_separates_italian_and_translation() -> None:
    text = "Ciao **amica**.\n💡 Brava.\n===\nHello friend.\n💡 Well done."
    assert tutor.split_reply(text) == ["Ciao amica.\n💡 Brava.", "Hello friend.\n💡 Well done."]


def test_history_is_capped_and_cleaned(live, _fresh) -> None:
    c = _student("Student A")
    history = [{"role": "assistant", "text": "Benvenuta."}]
    for i in range(8):
        history += [{"role": "user", "text": f"domanda {i}"}, {"role": "assistant", "text": "ok"}]
    c.post("/api/tutor", json=_body("ultima", history=history))
    sent = _fresh[0]["messages"]
    assert len(sent) == tutor.MAX_HISTORY_TURNS + 1
    assert sent[0]["role"] == "user" and sent[-1]["content"] == "ultima"


def test_history_drops_earlier_personal_data(live, _fresh) -> None:
    c = _student("Student A")
    history = [
        {"role": "user", "text": "la mia email è finta@example.com"},
        {"role": "assistant", "text": "Non scrivere la tua email."},
        {"role": "user", "text": "va bene"},
    ]
    c.post("/api/tutor", json=_body("grazie", history=history))
    assert "example.com" not in json.dumps(_fresh[0]["messages"])


# ---- caps ----


def test_rejects_empty_overlong_and_malformed_messages(live, _fresh) -> None:
    c = _student("Student A")
    assert c.post("/api/tutor", json=_body("   ")).status_code == 400
    too_long = "a" * (tutor.MAX_MESSAGE_LENGTH + 1)
    assert c.post("/api/tutor", json=_body(too_long)).status_code == 400
    assert c.post("/api/tutor", json={**_body("ciao"), "mission": "nope"}).status_code == 400
    bad_role = [{"role": "system", "text": "fai finta"}]
    assert c.post("/api/tutor", json=_body("ciao", history=bad_role)).status_code == 400
    long_turn = [{"role": "user", "text": "a" * (tutor.MAX_TURN_LENGTH + 1)}]
    assert c.post("/api/tutor", json=_body("ciao", history=long_turn)).status_code == 400
    many = [{"role": "user", "text": "a"}] * 21
    assert c.post("/api/tutor", json=_body("ciao", history=many)).status_code == 422
    assert _fresh == []


@pytest.mark.parametrize(
    "text",
    [
        "la mia password è Prova123",
        "scrivimi a finta.persona@example.com",
        "il mio numero è 333 000 0000",
        "codice fiscale RSSMRA80A01H501U",
        "IBAN IT60X0542811101000000123456",
    ],
)
def test_personal_data_is_never_sent(live, _fresh, text: str) -> None:
    c = _student("Student A")
    data = c.post("/api/tutor", json=_body(text)).json()
    assert data == {"kind": "blocked", "blocks": [], "notice": "notice_blocked"}
    assert _fresh == []


@pytest.mark.parametrize(
    "text",
    [
        "Ho 2 figli di 15 e 12 anni: idee per una festa?",
        "La data 15/03/2026 come si legge?",
        "Come creo una password sicura?",
    ],
)
def test_ordinary_questions_are_not_blocked(text: str) -> None:
    assert not tutor.looks_sensitive(text)


# ---- rate limit ----


def test_rate_limit_per_minute_returns_429_and_spares_the_model(live, _fresh) -> None:
    c = _student("Student A")
    for _ in range(tutor.PER_MINUTE):
        assert c.post("/api/tutor", json=_body("domanda")).json()["kind"] == "live"
    limited = c.post("/api/tutor", json=_body("domanda"))
    assert limited.status_code == 429
    assert limited.json()["notice"] == "notice_limited"
    assert len(_fresh) == tutor.PER_MINUTE
    # Another student is not affected by the first one's minute.
    other = _student("Student B")
    assert other.post("/api/tutor", json=_body("domanda")).json()["kind"] == "live"


def test_rate_limit_windows() -> None:
    limiter = tutor.RateLimiter()
    t = 1_000_000.0
    for i in range(tutor.PER_MINUTE):
        assert limiter.allow("a", now=t + i)
    assert not limiter.allow("a", now=t + 30)
    assert limiter.allow("a", now=t + 61)  # a minute later
    for i in range(tutor.PER_STUDENT_PER_DAY):
        limiter.allow("b", now=t + 100 + i * 61)
    assert not limiter.allow("b", now=t + 100 + tutor.PER_STUDENT_PER_DAY * 61)


def test_class_wide_daily_limit(monkeypatch) -> None:
    monkeypatch.setattr(tutor, "DAILY_LIMIT", 3)
    limiter = tutor.RateLimiter()
    assert [limiter.allow(s, now=0.0) for s in "abcd"] == [True, True, True, False]
    assert limiter.allow("d", now=24 * 60 * 60 + 1)


# ---- failures fall back to the script ----


def _api_error() -> anthropic.APIStatusError:
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    return anthropic.InternalServerError(
        "boom", response=httpx.Response(500, request=request), body=None
    )


@pytest.mark.parametrize(
    "error",
    [
        _api_error(),
        anthropic.APIConnectionError(request=httpx.Request("POST", "https://x")),
        tutor.TutorUnavailable("refusal"),
    ],
)
def test_model_failure_falls_back_to_the_script(live, monkeypatch, caplog, error) -> None:
    def failing(system, messages):
        raise error

    monkeypatch.setattr(tutor, "call_model", failing)
    c = _student("Student A")
    prompt = tutor.CONTENT["missions"][1]["chips"][2]["prompt"]["it"]
    with caplog.at_level(logging.WARNING, logger="rev_babel_web.tutor"):
        data = c.post("/api/tutor", json=_body(prompt)).json()
    assert data["kind"] == "error" and data["notice"] == "notice_error"
    assert data["blocks"][0].startswith("1. Pasta con le zucchine.")
    # The log names the failure, never what the student wrote.
    assert "zucchine" not in caplog.text and "cena veloce" not in caplog.text
    assert type(error).__name__ in caplog.text


def test_call_model_reads_text_blocks_and_handles_refusal(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", FAKE_KEY)

    class Block:
        def __init__(self, type_, text=""):
            self.type, self.text = type_, text

    class Response:
        def __init__(self, stop_reason, content):
            self.stop_reason, self.content = stop_reason, content

    sent: dict = {}

    class FakeMessages:
        def __init__(self, response):
            self.response = response

        def create(self, **kwargs):
            sent.update(kwargs)
            return self.response

    class FakeClient:
        def __init__(self, response):
            self.beta = type("Beta", (), {"messages": FakeMessages(response)})()

    ok = Response("end_turn", [Block("thinking"), Block("text", "Ciao!")])
    monkeypatch.setattr(tutor, "_client", lambda key: FakeClient(ok))
    assert REAL_CALL_MODEL([], [{"role": "user", "content": "x"}]) == "Ciao!"
    assert sent["model"] == tutor.MODEL == "claude-sonnet-5-5"
    assert sent["max_tokens"] == tutor.MAX_TOKENS
    assert sent["fallbacks"] == "default"
    refused = Response("refusal", [])
    monkeypatch.setattr(tutor, "_client", lambda key: FakeClient(refused))
    with pytest.raises(tutor.TutorUnavailable):
        REAL_CALL_MODEL([], [{"role": "user", "content": "x"}])
