import asyncio

from fastapi.testclient import TestClient
from rev_babel_web import chat
from rev_babel_web.main import app


def _login(name: str) -> TestClient:
    student = TestClient(app)
    student.post("/welcome", data={"name": name})
    return student


def setup_function() -> None:
    chat.clear()


def test_chat_requires_login() -> None:
    anon = TestClient(app)
    assert anon.post("/api/chat", json={"text": "hi"}).status_code == 401
    assert anon.get("/api/chat/stream").status_code == 401
    assert anon.get("/chat", follow_redirects=False).status_code == 303


def test_post_uses_the_logged_in_name_and_collapses_whitespace() -> None:
    student = _login("Student A")
    response = student.post("/api/chat", json={"text": "  ciao   a tutti "})
    assert response.status_code == 200
    assert response.json()["name"] == "Student A"
    assert chat.history()[0]["text"] == "ciao a tutti"


def test_rejects_empty_and_overlong_messages() -> None:
    student = _login("Student A")
    assert student.post("/api/chat", json={"text": "   "}).status_code == 400
    too_long = "x" * (chat.MAX_TEXT_LENGTH + 1)
    assert student.post("/api/chat", json={"text": too_long}).status_code == 400


def test_messages_expire_after_24_hours() -> None:
    chat.post("Student A", "old")
    chat._messages[0]["ts"] -= chat.TTL_SECONDS + 1
    chat.post("Student A", "new")
    assert [m["text"] for m in chat.history()] == ["new"]


def test_sse_sends_history_then_new_messages() -> None:
    chat.post("Student A", "first")

    async def run() -> list[str]:
        events = chat.sse_events()
        chunks = [await events.__anext__(), await events.__anext__()]
        chat.post("Student B", "second")
        chunks.append(await events.__anext__())
        await events.aclose()
        return chunks

    retry, history, message = asyncio.run(run())
    assert retry.startswith("retry:")
    assert "event: history" in history and "first" in history
    assert "event: message" in message and "second" in message
