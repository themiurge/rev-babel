import re
import time

from fastapi.testclient import TestClient
from rev_babel_web import spid_game
from rev_babel_web.main import app


def _student(name: str) -> TestClient:
    c = TestClient(app)
    c.post("/welcome", data={"name": name}, follow_redirects=True)
    return c


def _create(c: TestClient, service: str = "fse") -> dict:
    response = c.post("/api/spid-game/challenge", json={"service": service})
    assert response.status_code == 200
    return response.json()


def test_lesson_4_links_to_the_game_in_a_new_tab() -> None:
    c = _student("Amina")
    response = c.get("/course/lezione-4")
    assert response.status_code == 200
    assert 'href="/games/spid"' in response.text
    assert 'target="_blank"' in response.text
    # The embedded-game route must not try to iframe it.
    redirect = c.get("/course/lezione-4/spid", follow_redirects=False)
    assert redirect.status_code == 303
    assert redirect.headers["location"] == "/games/spid"


def test_game_page_needs_a_name_and_has_no_site_menu() -> None:
    anonymous = TestClient(app).get("/games/spid", follow_redirects=False)
    assert anonymous.status_code == 303

    page = _student("Bushra").get("/games/spid")
    assert page.status_code == 200
    assert 'id="viewport"' in page.text
    assert 'id="task-list"' in page.text
    assert 'class="sidebar"' not in page.text
    assert "Se hai capito, fai clic su Inizia il gioco" in page.text


def test_challenge_round_trip_approve() -> None:
    c = _student("Chiara")
    made = _create(c)
    assert re.fullmatch(r"[A-Z2-9]{8}", made["code"])
    assert made["url"].endswith("/spid/" + made["code"])
    assert made["qr_svg"].startswith("<svg")
    assert c.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "pending"}

    phone = TestClient(app)  # a phone: no session at all
    page = phone.get(f"/spid/{made['code']}")
    assert page.status_code == 200
    assert "Approva" in page.text and "Rifiuta" in page.text
    assert "Fascicolo sanitario" in page.text

    done = phone.post(f"/spid/{made['code']}", data={"decision": "approve"})
    assert done.status_code == 200
    assert "Accesso approvato" in done.text

    assert c.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "approved"}
    # The computer has seen it: the code is spent.
    assert c.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "expired"}
    assert phone.get(f"/spid/{made['code']}").status_code == 410


def test_reject_and_one_time_use() -> None:
    c = _student("Dalia")
    made = _create(c, "comune")
    phone = TestClient(app)
    assert (
        "Accesso rifiutato" in phone.post(f"/spid/{made['code']}", data={"decision": "reject"}).text
    )
    # Already decided: a second tap cannot flip it to approved.
    again = phone.post(f"/spid/{made['code']}", data={"decision": "approve"})
    assert again.status_code == 410
    assert c.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "rejected"}


def test_only_the_owner_can_read_a_challenge_and_codes_are_not_guessable() -> None:
    owner = _student("Elham")
    other = _student("Farah")
    made = _create(owner)
    assert other.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "expired"}
    # The stranger's poll did not spend the owner's challenge.
    assert owner.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "pending"}
    assert TestClient(app).get("/spid/AAAAAAAA").status_code == 410
    assert TestClient(app).post("/spid/AAAAAAAA", data={"decision": "approve"}).status_code == 410


def test_challenge_input_is_validated_and_one_open_challenge_per_student() -> None:
    c = _student("Gina")
    assert c.post("/api/spid-game/challenge", json={"service": "bank"}).status_code == 400
    assert (
        TestClient(app).post("/api/spid-game/challenge", json={"service": "fse"}).status_code == 401
    )
    first = _create(c)
    second = _create(c, "inps")
    assert c.get(f"/api/spid-game/challenge/{first['code']}").json() == {"state": "expired"}
    assert c.get(f"/api/spid-game/challenge/{second['code']}").json() == {"state": "pending"}
    assert (
        TestClient(app).post(f"/spid/{second['code']}", data={"decision": "maybe"}).status_code
        == 400
    )


def test_challenges_expire(monkeypatch) -> None:
    c = _student("Hawa")
    made = _create(c)
    real = time.time()
    monkeypatch.setattr(spid_game.time, "time", lambda: real + spid_game.TTL_SECONDS + 5)
    assert c.get(f"/api/spid-game/challenge/{made['code']}").json() == {"state": "expired"}
    assert TestClient(app).get(f"/spid/{made['code']}").status_code == 410


def test_qr_points_at_the_student_host_when_started_from_the_teacher_host(monkeypatch) -> None:
    monkeypatch.setenv("ECO_PUBLIC_HOST", "rev-babel.example.org")
    c = _student("Ines")
    made = c.post(
        "/api/spid-game/challenge",
        json={"service": "fse"},
        headers={"host": "mic.test"},
    ).json()
    assert made["url"].startswith("https://rev-babel.example.org/spid/")
