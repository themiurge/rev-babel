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
