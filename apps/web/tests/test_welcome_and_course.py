import os

os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("WEB_COOKIE_SECURE", "false")

from fastapi.testclient import TestClient
from rev_babel_web.main import app

client = TestClient(app)


def test_welcome_page_loads() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Come ti chiami?" in response.text


def test_course_requires_a_name() -> None:
    response = client.get("/course", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_submitting_a_name_reaches_the_course_page() -> None:
    response = client.post("/welcome", data={"name": "Fatima"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Benvenuta, Fatima!" in response.text
    assert "La Tastiera e il Mouse" in response.text


def test_blank_name_is_rejected() -> None:
    response = client.post("/welcome", data={"name": "   "})
    assert response.status_code == 400
    assert "Scrivi il tuo nome" in response.text


def test_course_page_embeds_both_games() -> None:
    response = client.get("/course")
    assert "/static/lessons/lezione-1/mouse/index.html" in response.text
    assert "/static/lessons/lezione-1/keyboard/index.html" in response.text
    assert "Il tuo miglior tempo" in response.text


def test_score_submission_requires_a_session() -> None:
    anonymous = TestClient(app)
    response = anonymous.post("/api/scores", json={"game": "mouse", "value": 800})
    assert response.status_code == 401


def test_unknown_game_is_rejected() -> None:
    response = client.post("/api/scores", json={"game": "chess", "value": 10})
    assert response.status_code == 400


def test_implausible_score_is_rejected() -> None:
    response = client.post("/api/scores", json={"game": "keyboard", "value": 999_999})
    assert response.status_code == 400


def test_submitting_scores_tracks_personal_best() -> None:
    first = client.post("/api/scores", json={"game": "keyboard", "value": 30.0})
    assert first.status_code == 200
    assert first.json() == {"best": 30.0, "last": 30.0}

    better = client.post("/api/scores", json={"game": "keyboard", "value": 20.0})
    assert better.json() == {"best": 20.0, "last": 20.0}

    worse = client.post("/api/scores", json={"game": "keyboard", "value": 25.0})
    assert worse.json() == {"best": 20.0, "last": 25.0}
