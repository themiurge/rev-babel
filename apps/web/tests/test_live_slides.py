import asyncio

from fastapi.testclient import TestClient
from rev_babel_web import live
from rev_babel_web.main import app

client = TestClient(app)
CAPTURE_HEADERS = {"Host": "mic.test"}


def _login(name: str) -> TestClient:
    student = TestClient(app)
    student.post("/welcome", data={"name": name})
    return student


def test_extract_file_id_from_url_and_bare_id() -> None:
    url = "https://docs.google.com/presentation/d/1AbC-XYZ/edit?usp=sharing"
    assert live.extract_file_id(url) == "1AbC-XYZ"
    assert live.extract_file_id("1AbC-XYZ") == "1AbC-XYZ"


def test_goto_clamps_and_is_idempotent() -> None:
    live.start("1AbC", "Test deck", 10)
    first = live.goto(999)
    assert first["index"] == 10
    revision = first["revision"]
    same = live.goto(10)
    assert same["revision"] == revision
    live.end()


def test_sse_events_yields_retry_hint_then_initial_state() -> None:
    live.start("1AbC", "Test deck", 5)

    async def read_two_chunks() -> tuple[str, str]:
        events = live.sse_events()
        first = await events.__anext__()
        second = await events.__anext__()
        await events.aclose()
        return first, second

    first, second = asyncio.run(read_two_chunks())
    assert first == "retry: 3000\n\n"
    assert second.startswith("event: state\ndata: ")
    live.end()


def test_present_is_blocked_off_the_capture_host() -> None:
    response = client.get("/present")
    assert response.status_code == 403


def test_present_is_served_on_the_capture_host() -> None:
    response = client.get("/present", headers=CAPTURE_HEADERS)
    assert response.status_code == 200
    assert "Avvia la presentazione" in response.text


def test_root_redirects_to_present_on_the_capture_host() -> None:
    response = client.get("/", headers=CAPTURE_HEADERS, follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/present"


def test_root_is_the_student_login_page_off_the_capture_host() -> None:
    anonymous = TestClient(app)
    response = anonymous.get("/", follow_redirects=False)
    assert response.status_code == 200


def test_admin_endpoints_are_blocked_off_the_capture_host() -> None:
    response = client.post(
        "/admin/api/live/start",
        json={"file_id_or_url": "abc123", "title": "T", "slide_count": 5},
    )
    assert response.status_code == 403


def test_start_goto_status_and_end_flow_over_http() -> None:
    start = client.post(
        "/admin/api/live/start",
        headers=CAPTURE_HEADERS,
        json={
            "file_id_or_url": "https://docs.google.com/presentation/d/1AbC-XYZ/edit",
            "title": "Riconoscere le truffe online",
            "slide_count": 24,
        },
    )
    assert start.status_code == 200
    state = start.json()
    assert state["file_id"] == "1AbC-XYZ"
    assert state["index"] == 1
    assert state["status"] == "live"

    goto = client.post("/admin/api/live/goto", headers=CAPTURE_HEADERS, json={"index": 9})
    assert goto.json()["index"] == 9

    clamped = client.post("/admin/api/live/goto", headers=CAPTURE_HEADERS, json={"index": 999})
    assert clamped.json()["index"] == 24

    blanked = client.post(
        "/admin/api/live/status", headers=CAPTURE_HEADERS, json={"status": "blank"}
    )
    assert blanked.json()["status"] == "blank"

    bad_status = client.post(
        "/admin/api/live/status", headers=CAPTURE_HEADERS, json={"status": "nope"}
    )
    assert bad_status.status_code == 400

    ended = client.post("/admin/api/live/end", headers=CAPTURE_HEADERS)
    assert ended.json()["status"] == "ended"


def test_api_live_requires_a_student_session() -> None:
    anonymous = TestClient(app)
    response = anonymous.get("/api/live")
    assert response.status_code == 401


def test_follow_requires_a_student_session() -> None:
    anonymous = TestClient(app)
    response = anonymous.get("/follow", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_follow_page_renders_for_a_logged_in_student() -> None:
    student = _login("Follow Test")
    response = student.get("/follow")
    assert response.status_code == 200
    assert 'id="frame"' in response.text


def test_api_live_returns_current_state_for_a_logged_in_student() -> None:
    student = _login("State Reader")
    response = student.get("/api/live")
    assert response.status_code == 200
    assert "revision" in response.json()


def test_present_lists_local_decks_to_pick_from() -> None:
    response = client.get("/present", headers=CAPTURE_HEADERS)
    assert response.status_code == 200
    assert "lezione-2-account-demo" in response.text
    assert "Il proprio account (esempio)" in response.text


def test_start_local_switches_the_live_source_to_a_deck() -> None:
    start = client.post(
        "/admin/api/live/start_local",
        headers=CAPTURE_HEADERS,
        json={"deck_slug": "lezione-2-account-demo"},
    )
    assert start.status_code == 200
    state = start.json()
    assert state["source"] == "local"
    assert state["deck_slug"] == "lezione-2-account-demo"
    assert state["slide_count"] == 3
    assert state["index"] == 1

    goto = client.post("/admin/api/live/goto", headers=CAPTURE_HEADERS, json={"index": 2})
    assert goto.json()["index"] == 2
    client.post("/admin/api/live/end", headers=CAPTURE_HEADERS)


def test_start_local_rejects_an_unknown_deck() -> None:
    response = client.post(
        "/admin/api/live/start_local",
        headers=CAPTURE_HEADERS,
        json={"deck_slug": "does-not-exist"},
    )
    assert response.status_code == 404


def test_admin_can_preview_a_deck_slide_without_a_live_session() -> None:
    response = client.get(
        "/admin/api/decks/lezione-2-account-demo/slides/1", headers=CAPTURE_HEADERS
    )
    assert response.status_code == 200
    assert "Il tuo account" in response.json()["it"]


def test_admin_deck_preview_is_blocked_off_the_capture_host() -> None:
    response = client.get("/admin/api/decks/lezione-2-account-demo/slides/1")
    assert response.status_code == 403


def test_local_slide_endpoint_serves_italian_and_the_students_translation() -> None:
    live.start_local("lezione-2-account-demo", "Il proprio account (esempio)", 3)
    student = _login("Deck Reader")
    student.post("/api/language", json={"language": "fr"})

    response = student.get("/api/live/slide?index=1")
    assert response.status_code == 200
    body = response.json()
    assert "Il tuo account" in body["it"]
    assert "Ton compte" in body["translated"]
    live.end()


def test_local_slide_endpoint_has_no_translation_for_italian_speakers() -> None:
    live.start_local("lezione-2-account-demo", "Il proprio account (esempio)", 3)
    student = _login("Deck Reader Italian")

    response = student.get("/api/live/slide?index=1")
    assert response.json()["translated"] is None
    live.end()


def test_local_slide_endpoint_404s_when_the_live_source_is_google() -> None:
    live.start("1AbC", "Test deck", 5)
    student = _login("Google Source Reader")

    response = student.get("/api/live/slide?index=1")
    assert response.status_code == 404
    live.end()


def test_follow_page_renders_the_split_screen_container() -> None:
    student = _login("Split Screen Reader")
    response = student.get("/follow")
    assert response.status_code == 200
    assert 'id="split"' in response.text
    assert 'id="slide-it"' in response.text
    assert 'id="slide-translated"' in response.text
