from fastapi.testclient import TestClient
from rev_babel_web import db
from rev_babel_web.main import app

client = TestClient(app)


def test_language_cookie_seeds_a_new_account() -> None:
    fresh = TestClient(app)
    fresh.post("/api/language", json={"language": "fr"})
    fresh.post("/welcome", data={"name": "Cookie Seeded"})
    student_id = db.find_student_by_name("Cookie Seeded")
    assert student_id is not None
    assert db.get_student(student_id)["language"] == "fr"


def test_unknown_language_is_rejected() -> None:
    response = client.post("/api/language", json={"language": "xx"})
    assert response.status_code == 400


def test_logging_in_twice_with_same_name_reuses_the_account() -> None:
    first = TestClient(app)
    first.post("/welcome", data={"name": "Same Name"})
    first_id = db.find_student_by_name("Same Name")

    second = TestClient(app)
    second.post("/welcome", data={"name": "same name"})  # different case
    second_id = db.find_student_by_name("Same Name")

    assert first_id == second_id


def test_roster_login_by_id() -> None:
    setup = TestClient(app)
    setup.post("/welcome", data={"name": "Roster Login"})
    student_id = db.find_student_by_name("Roster Login")

    logging_in = TestClient(app)
    response = logging_in.post(f"/login/{student_id}", follow_redirects=True)
    assert response.status_code == 200
    assert "Roster Login" in response.text


def test_roster_login_rejects_an_unknown_id() -> None:
    response = client.post("/login/does-not-exist")
    assert response.status_code == 404


def test_welcome_page_lists_existing_students_in_the_roster() -> None:
    setup = TestClient(app)
    setup.post("/welcome", data={"name": "In The Roster"})

    fresh = TestClient(app)
    response = fresh.get("/")
    assert "In The Roster" in response.text
    assert f'action="/login/{db.find_student_by_name("In The Roster")}"' in response.text


def test_language_preference_persists_across_a_fresh_login() -> None:
    setup = TestClient(app)
    setup.post("/api/language", json={"language": "ckb"})
    setup.post("/welcome", data={"name": "Language Persist"})
    student_id = db.find_student_by_name("Language Persist")
    setup.get("/logout")

    logging_in = TestClient(app)
    response = logging_in.post(f"/login/{student_id}", follow_redirects=True)
    # Sidebar "Lezioni" hover title should be in Kurdish now.
    assert 'title="وانەکان"' in response.text


def test_game_page_shows_hover_translation_for_current_language() -> None:
    setup = TestClient(app)
    setup.post("/api/language", json={"language": "en"})
    setup.post("/welcome", data={"name": "English Speaker"})
    response = setup.get("/course/lezione-1/mouse")
    assert 'title="Back"' in response.text
    assert 'title="Best time"' in response.text


def test_italian_default_has_no_hover_titles() -> None:
    setup = TestClient(app)
    setup.post("/welcome", data={"name": "Italian Default"})
    response = setup.get("/course")
    assert "title=" not in response.text
